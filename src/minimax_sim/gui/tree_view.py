"""
Draws the game tree from a Layout and a Snapshot.

The Layout gives each node a position in abstract units, leaves at x = 0, 1, 2, ...
and levels at y = 0, 1, 2, ... This module turns them into pixels and draws
the nodes and edges on a QGraphicsScene shown in a scrollable QGraphicsView.

Nodes follow Rosen's notation, MAX nodes are squares and MIN nodes are circles.
The Snapshot decides how each node looks (active, on the path, done, pruned)
and which value it shows. After the last step the optimal line from the root
is drawn in green.
Colours come from the system theme, so the tree works in light and dark mode.
"""

from math import isinf
from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import QBrush, QColor, QFont, QPainter, QPen, QResizeEvent, QWheelEvent
from PySide6.QtWidgets import QGraphicsScene, QGraphicsView

from minimax_sim.core.events import NodeId, ValueKind
from minimax_sim.session.layout import Layout
from minimax_sim.session.snapshot import Snapshot, Status

# Size of one node in pixels
NODE_SIZE = 40

# Distance between neighbouring leaves, in node sizes
X_SPACING = 1.6

# Distance between levels, in node sizes
Y_SPACING = 2.6

# Line width of nodes and edges in pixels, the active node and its path get double
LINE_WIDTH = 2

# Opacity of the fill of nodes on the path and on the optimal line, 0 to 255
PATH_FILL_ALPHA = 90

# Colour of the optimal line, readable on both light and dark background
OPTIMAL_LINE_COLOR = "#3aa655"

# Sign in front of a value that is only a bound
BOUND_SIGNS = {ValueKind.EXACT: "", ValueKind.UPPER: "≤", ValueKind.LOWER: "≥"}

# Size of the α and β text next to a node, in node sizes
BOUNDS_TEXT_SIZE = 0.3

# Limits of the zoom when the tree is fitted to the window, 1 means one scene pixel is one screen pixel
MIN_ZOOM = 0.5
MAX_ZOOM = 5.0

# Limits of the zoom by hand, wider than for fitting
MIN_HAND_ZOOM = 0.2
MAX_HAND_ZOOM = 6.0

# How much one step of zooming in or out changes the zoom
ZOOM_STEP = 1.25

# Free space kept around the active node when the view follows it, in node sizes
FOLLOW_MARGIN = 2


# Scrollable view of the tree, MAX nodes are squares and MIN nodes are circles
class TreeView(QGraphicsView):
    def __init__(self) -> None:
        super().__init__()
        self.setScene(QGraphicsScene(self))
        self.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Dragging with the mouse moves the tree, zooming keeps the point under the mouse in place
        self.setDragMode(QGraphicsView.DragMode.ScrollHandDrag)
        self.setTransformationAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)

        # Whether the zoom follows the window size, zooming by hand turns it off
        self._follows_window = True

        # Whether nodes the search has not reached yet are left out
        self.hide_unvisited = False

        # Whether the view scrolls so the active node stays visible, matters only when zoomed in
        self.follow_active = True

    # Throw away what is drawn and draw the whole tree again
    # With show_bounds the active node and its ancestors get their α and β next to them
    def draw(self, layout: Layout, snapshot: Snapshot, show_bounds: bool) -> None:
        scene = self.scene()
        scene.clear()
        statuses = _statuses(layout, snapshot)

        # Optimal line from the root, empty until the run is over
        line = set(snapshot.principal_variation)

        # The scene always spans the whole tree, so it does not move when nodes are hidden
        # A different tree gets fitted to the window again
        tree_rect = self._tree_rect(layout)
        if scene.sceneRect() != tree_rect:
            scene.setSceneRect(tree_rect)
            self.fit_to_window()

        # Edges first, so the nodes cover their ends, each edge looks like the child it leads to
        for layout_node in layout.nodes.values():
            start = self._position(layout, layout_node.node)
            for child in layout_node.children:
                if self._is_hidden(statuses[child]):
                    continue
                end = self._position(layout, child)
                scene.addLine(start.x(), start.y(), end.x(), end.y(), self._pen(statuses[child], child in line))

        for layout_node in layout.nodes.values():
            node = layout_node.node
            status = statuses[node]
            if self._is_hidden(status):
                continue
            center = self._position(layout, node)
            rect = QRectF(center.x() - NODE_SIZE / 2, center.y() - NODE_SIZE / 2, NODE_SIZE, NODE_SIZE)
            pen = self._pen(status, node in line)
            brush = self._brush(status, node in line)
            if layout_node.is_max:
                scene.addRect(rect, pen, brush)
            else:
                scene.addEllipse(rect, pen, brush)

            node_state = snapshot.nodes.get(node)
            if node_state is not None and node_state.value is not None:
                self._add_value(center, BOUND_SIGNS[node_state.kind] + number_text(node_state.value), status)

            # Leaves only get a value, their bounds tell nothing
            if show_bounds and status in (Status.ACTIVE, Status.ON_PATH) and layout_node.children:
                self._add_bounds(center, node_state.alpha, node_state.beta)

        # Scroll only as much as needed to keep the active node in sight
        # After the last step there is no active node, the view goes to the end of the optimal line
        target = snapshot.active
        if target is None and snapshot.principal_variation:
            target = snapshot.principal_variation[-1]
        if self.follow_active and target is not None:
            center = self._position(layout, target)
            margin = NODE_SIZE * FOLLOW_MARGIN
            self.ensureVisible(QRectF(center.x() - margin, center.y() - margin, 2 * margin, 2 * margin))

    # Remove everything drawn, used when there is no tree to show
    def clear_tree(self) -> None:
        self.scene().clear()

    # Zoom in on the tree
    def zoom_in(self) -> None:
        self._zoom_by(ZOOM_STEP)

    # Zoom out on the tree
    def zoom_out(self) -> None:
        self._zoom_by(1 / ZOOM_STEP)

    # Fit the tree to the window and keep it fitted when the window changes size
    def fit_to_window(self) -> None:
        self._follows_window = True
        self._fit()

    # Called by Qt whenever the view changes size, the tree is fitted again unless zoomed by hand
    def resizeEvent(self, event: QResizeEvent) -> None:
        super().resizeEvent(event)
        if self._follows_window:
            self._fit()

    # Called by Qt for the mouse wheel, Ctrl + wheel zooms, the wheel alone scrolls as usual
    def wheelEvent(self, event: QWheelEvent) -> None:
        if event.modifiers() & Qt.KeyboardModifier.ControlModifier:
            self._zoom_by(ZOOM_STEP if event.angleDelta().y() > 0 else 1 / ZOOM_STEP)
        else:
            super().wheelEvent(event)

    # Change the zoom by factor, within MIN_HAND_ZOOM and MAX_HAND_ZOOM
    def _zoom_by(self, factor: float) -> None:
        current = self.transform().m11()
        target = max(MIN_HAND_ZOOM, min(current * factor, MAX_HAND_ZOOM))
        self._follows_window = False
        self.scale(target / current, target / current)

    # Zoom so the whole tree fills the view, within MIN_ZOOM and MAX_ZOOM
    def _fit(self) -> None:
        tree = self.sceneRect()
        view = self.viewport().rect()
        if tree.isEmpty() or view.isEmpty():
            return
        zoom = min(view.width() / tree.width(), view.height() / tree.height())
        zoom = max(MIN_ZOOM, min(zoom, MAX_ZOOM))
        self.resetTransform()
        self.scale(zoom, zoom)
        self.centerOn(tree.center())

    # Whether a node with this status is left out of the drawing
    def _is_hidden(self, status: Status) -> bool:
        return self.hide_unvisited and status is Status.UNVISITED

    # Area of the whole tree in scene pixels, with half a node of margin around it
    def _tree_rect(self, layout: Layout) -> QRectF:
        width = (layout.width - 1) * X_SPACING * NODE_SIZE
        height = layout.depth * Y_SPACING * NODE_SIZE
        return QRectF(-NODE_SIZE, -NODE_SIZE, width + 2 * NODE_SIZE, height + 2 * NODE_SIZE)

    # Centre of a node in scene pixels
    def _position(self, layout: Layout, node: NodeId) -> QPointF:
        layout_node = layout.nodes[node]
        return QPointF(layout_node.x * X_SPACING * NODE_SIZE, layout_node.y * Y_SPACING * NODE_SIZE)

    # Outline of a node or an edge
    def _pen(self, status: Status, on_line: bool) -> QPen:
        palette = self.palette()
        if on_line:
            return QPen(QColor(OPTIMAL_LINE_COLOR), LINE_WIDTH * 2)
        if status in (Status.ACTIVE, Status.ON_PATH):
            return QPen(palette.highlight().color(), LINE_WIDTH * 2)
        if status is Status.DONE:
            return QPen(palette.text().color(), LINE_WIDTH)
        if status is Status.PRUNED:
            return QPen(palette.placeholderText().color(), LINE_WIDTH, Qt.PenStyle.DotLine)
        return QPen(palette.placeholderText().color(), LINE_WIDTH)

    # Fill of a node
    def _brush(self, status: Status, on_line: bool) -> QBrush:
        palette = self.palette()
        if on_line:
            color = QColor(OPTIMAL_LINE_COLOR)
            color.setAlpha(PATH_FILL_ALPHA)
            return QBrush(color)
        if status is Status.ACTIVE:
            return palette.highlight()
        if status is Status.ON_PATH:
            color = QColor(palette.highlight().color())
            color.setAlpha(PATH_FILL_ALPHA)
            return QBrush(color)
        return palette.base()

    # Value written in the middle of a node
    def _add_value(self, center: QPointF, text: str, status: Status) -> None:
        palette = self.palette()
        font = QFont()
        font.setPixelSize(int(NODE_SIZE * 0.4))
        font.setBold(True)
        item = self.scene().addSimpleText(text, font)
        item.setBrush(palette.highlightedText() if status is Status.ACTIVE else palette.text())
        size = item.boundingRect()
        item.setPos(center.x() - size.width() / 2, center.y() - size.height() / 2)

    # α above β, to the upper right of a node
    def _add_bounds(self, center: QPointF, alpha: float, beta: float) -> None:
        font = QFont()
        font.setPixelSize(int(NODE_SIZE * BOUNDS_TEXT_SIZE))
        item = self.scene().addSimpleText(f"α = {number_text(alpha)}\nβ = {number_text(beta)}", font)
        item.setBrush(self.palette().text())
        item.setPos(center.x() + NODE_SIZE * 0.55, center.y() - NODE_SIZE * 0.65)


# Status of every node in the layout, everything below a pruned node counts as pruned too
def _statuses(layout: Layout, snapshot: Snapshot) -> dict[NodeId, Status]:
    statuses: dict[NodeId, Status] = {}

    # Walk from the root down, pruned is passed on to the children
    def visit(node: NodeId, under_pruned: bool) -> None:
        node_state = snapshot.nodes.get(node)
        status = node_state.status if node_state is not None else Status.UNVISITED
        if under_pruned:
            status = Status.PRUNED
        statuses[node] = status
        for child in layout.nodes[node].children:
            visit(child, status is Status.PRUNED)

    visit((), False)
    return statuses


# Number without ".0", 3.0 is shown as 3, infinity as ∞
def number_text(value: float) -> str:
    if isinf(value):
        return "∞" if value > 0 else "−∞"
    if isinstance(value, float) and value.is_integer():
        return str(int(value))
    return str(value)
