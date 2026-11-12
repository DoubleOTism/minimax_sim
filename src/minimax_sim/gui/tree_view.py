"""
Draws the game tree from a Layout and a Snapshot.

The Layout gives each node a position in abstract units, leaves at x = 0, 1, 2, ...
and levels at y = 0, 1, 2, ... This module turns them into pixels and draws
the nodes and edges on a QGraphicsScene shown in a scrollable QGraphicsView.

A new tree is drawn whole once, every step after that only changes the nodes
that look different than before. A step therefore costs about the same
on a small and on a large tree.

Nodes follow Rosen's notation, MAX nodes are squares and MIN nodes are circles.
The Snapshot decides how each node looks (active, on the path, done, pruned)
and which value it shows. After the last step the optimal line from the root
is drawn in green.
Edges carry the label of their move when the game has one, and a game can show
a bubble with more about a node when the mouse stays over it.
Colours come from the system theme, so the tree works in light and dark mode.
"""

from collections.abc import Callable

from PySide6.QtCore import QEvent, QPoint, QPointF, QRectF, Qt
from PySide6.QtGui import (
    QBrush,
    QColor,
    QFont,
    QFontMetricsF,
    QPainter,
    QPen,
    QResizeEvent,
    QWheelEvent,
)
from PySide6.QtWidgets import (
    QAbstractGraphicsShapeItem,
    QGraphicsItem,
    QGraphicsLineItem,
    QGraphicsRectItem,
    QGraphicsScene,
    QGraphicsSimpleTextItem,
    QGraphicsView,
    QToolTip,
)

from minimax_sim.core.events import NodeId
from minimax_sim.numbers import number_text, value_text
from minimax_sim.session.layout import Layout
from minimax_sim.session.snapshot import NodeState, Snapshot, Status

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

# Size of the α and β text next to a node, in node sizes
BOUNDS_TEXT_SIZE = 0.3

# Size of the move label on an edge, in node sizes
LABEL_TEXT_SIZE = 0.35

# Where the label sits on its edge, 0 is the parent and 1 the child
# Closer to the child the edges of one parent are further apart, so the labels do not overlap
LABEL_POSITION = 0.6

# Free space left and right of the label text, in pixels
LABEL_PADDING = 2

# Key under which a drawn node keeps its id, so the bubble knows which node is under the mouse
NODE_KEY = 0

# Limits of the zoom when the tree is fitted to the window, 1 means one scene pixel is one screen pixel
MIN_ZOOM = 0.75
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

        # Text of the bubble over a node, an empty text shows no bubble
        self.node_tooltip: Callable[[NodeId], str] | None = None

        # Layout that is drawn and the last snapshot with show_bounds, None while nothing is drawn
        self._layout: Layout | None = None
        self._last_draw: tuple[Snapshot, bool] | None = None

        # Drawn items by node id, an edge and a label belong to the child they lead to
        self._edges: dict[NodeId, QGraphicsLineItem] = {}
        self._labels: dict[NodeId, QGraphicsRectItem] = {}
        self._shapes: dict[NodeId, QAbstractGraphicsShapeItem] = {}
        self._values: dict[NodeId, QGraphicsSimpleTextItem] = {}

        # How each node looked at the last step, see _update
        self._looks: dict[NodeId, tuple[Status, bool, str, bool]] = {}

        # α and β texts drawn at the last step
        self._bounds: list[QGraphicsItem] = []

    # Bring the drawing in line with the snapshot
    # A different layout is drawn whole first, then only the nodes that changed are touched
    # With show_bounds the active node and its ancestors get their α and β next to them
    def draw(self, layout: Layout, snapshot: Snapshot, show_bounds: bool) -> None:
        if layout is not self._layout:
            self._build(layout)
        self._last_draw = (snapshot, show_bounds)
        self._update(snapshot, show_bounds)

        # Scroll only as much as needed to keep the active node in sight
        # After the last step there is no active node, the view goes to the end of the optimal line
        target = snapshot.active
        if target is None and snapshot.principal_variation:
            target = snapshot.principal_variation[-1]
        if self.follow_active and target is not None:
            center = self._position(layout, target)
            margin = NODE_SIZE * FOLLOW_MARGIN
            self.ensureVisible(QRectF(center.x() - margin, center.y() - margin, 2 * margin, 2 * margin))

    # Create every edge, label and node of a new tree, how they look is set by _update
    def _build(self, layout: Layout) -> None:
        self.clear_tree()
        self._layout = layout
        scene = self.scene()

        # The scene always spans the whole tree, so it does not move when nodes are hidden
        # A tree of a different size gets fitted to the window again
        tree_rect = self._tree_rect(layout)
        if scene.sceneRect() != tree_rect:
            scene.setSceneRect(tree_rect)
            self.fit_to_window()

        # Edges first, so the nodes cover their ends, each edge belongs to the child it leads to
        for layout_node in layout.nodes.values():
            start = self._position(layout, layout_node.node)
            for child in layout_node.children:
                end = self._position(layout, child)
                self._edges[child] = scene.addLine(start.x(), start.y(), end.x(), end.y())

        # Move labels after all edges, so no edge crosses a label
        for layout_node in layout.nodes.values():
            start = self._position(layout, layout_node.node)
            for child in layout_node.children:
                label = layout.nodes[child].label
                if label:
                    end = self._position(layout, child)
                    self._labels[child] = self._add_label(start + (end - start) * LABEL_POSITION, label)

        # Nodes last, the value text is a child of the shape, so it hides and shows with it
        for layout_node in layout.nodes.values():
            node = layout_node.node
            center = self._position(layout, node)
            rect = QRectF(center.x() - NODE_SIZE / 2, center.y() - NODE_SIZE / 2, NODE_SIZE, NODE_SIZE)
            shape = scene.addRect(rect) if layout_node.is_max else scene.addEllipse(rect)
            shape.setData(NODE_KEY, node)
            self._shapes[node] = shape
            self._values[node] = self._add_value(shape)

    # Change only what looks different than at the last step
    # The look of a node is its status, whether it is on the optimal line, its value text and whether it is hidden
    def _update(self, snapshot: Snapshot, show_bounds: bool) -> None:
        statuses = _statuses(self._layout, snapshot)

        # Optimal line from the root, empty until the run is over
        line = set(snapshot.principal_variation)

        for node, status in statuses.items():
            node_state = snapshot.nodes.get(node)
            on_line = node in line
            look = (status, on_line, _value_text(node_state), self._is_hidden(status))
            if self._looks.get(node) == look:
                continue
            self._looks[node] = look
            self._restyle(node, *look)

        # α and β are only next to the active node and its ancestors, a few items drawn again every step
        # Leaves only get a value, their bounds tell nothing
        for item in self._bounds:
            self.scene().removeItem(item)
        self._bounds = []
        if show_bounds:
            for node in snapshot.path:
                if self._layout.nodes[node].children:
                    node_state = snapshot.nodes[node]
                    self._bounds.append(self._add_bounds(self._shapes[node], node_state.alpha, node_state.beta))

    # Give one node, the edge leading to it and its label the look of its status
    def _restyle(self, node: NodeId, status: Status, on_line: bool, value_text: str, hidden: bool) -> None:
        palette = self.palette()
        shape = self._shapes[node]
        shape.setVisible(not hidden)
        shape.setPen(self._pen(status, on_line))
        shape.setBrush(self._brush(status, on_line))

        # Value in the middle of the node, centred again because the width of the text changes
        value = self._values[node]
        value.setText(value_text)
        value.setBrush(palette.highlightedText() if status is Status.ACTIVE else palette.text())
        size = value.boundingRect()
        center = shape.boundingRect().center()
        value.setPos(center.x() - size.width() / 2, center.y() - size.height() / 2)

        # The root has no edge and no label, each edge looks like the child it leads to
        edge = self._edges.get(node)
        if edge is not None:
            edge.setVisible(not hidden)
            edge.setPen(self._pen(status, on_line))
        label = self._labels.get(node)
        if label is not None:
            label.setVisible(not hidden)
            text = label.childItems()[0]
            faded = status in (Status.UNVISITED, Status.PRUNED)
            text.setBrush(palette.placeholderText() if faded else palette.text())

    # Remove everything drawn, used when there is no tree to show
    def clear_tree(self) -> None:
        self.scene().clear()
        self._layout = None
        self._last_draw = None
        self._edges.clear()
        self._labels.clear()
        self._shapes.clear()
        self._values.clear()
        self._looks.clear()
        self._bounds = []

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

    # Called by Qt when the system colours change, the whole tree is built again in the new colours
    def changeEvent(self, event: QEvent) -> None:
        super().changeEvent(event)
        if event.type() is QEvent.Type.PaletteChange and self._layout is not None and self._last_draw is not None:
            layout = self._layout
            self._layout = None
            self.draw(layout, *self._last_draw)

    # Called by Qt for events in the visible area, a tooltip event over a node shows its bubble
    def viewportEvent(self, event: QEvent) -> bool:
        if event.type() is not QEvent.Type.ToolTip or self.node_tooltip is None:
            return super().viewportEvent(event)
        node = self._node_at(event.pos())
        text = self.node_tooltip(node) if node is not None else ""
        if text:
            QToolTip.showText(event.globalPos(), text, self.viewport())
        else:
            QToolTip.hideText()
        return True

    # Id of the node under a point of the visible area, None if there is none
    # The value text lies on top of the node, so the items under the point are searched for the shape
    def _node_at(self, point: QPoint) -> NodeId | None:
        for item in self.items(point):
            node = item.data(NODE_KEY)
            if node is not None:
                return node
        return None

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

    # Empty value text inside a node, _restyle fills and centres it
    def _add_value(self, shape: QGraphicsItem) -> QGraphicsSimpleTextItem:
        font = QFont()
        font.setPixelSize(int(NODE_SIZE * 0.4))
        font.setBold(True)
        item = QGraphicsSimpleTextItem(shape)
        item.setFont(font)
        return item

    # Move label centred on point, on a patch of the background that hides the edge under it
    # The text is a child of the patch, _restyle colours it
    def _add_label(self, point: QPointF, text: str) -> QGraphicsRectItem:
        font = QFont()
        font.setPixelSize(int(NODE_SIZE * LABEL_TEXT_SIZE))
        metrics = QFontMetricsF(font)
        width = metrics.horizontalAdvance(text) + 2 * LABEL_PADDING
        height = metrics.height()
        patch = self.scene().addRect(
            QRectF(point.x() - width / 2, point.y() - height / 2, width, height),
            QPen(Qt.PenStyle.NoPen),
            self.palette().base(),
        )
        item = QGraphicsSimpleTextItem(text, patch)
        item.setFont(font)
        item.setPos(patch.rect().x() + LABEL_PADDING, patch.rect().y())
        return patch

    # α above β, to the upper right of a node
    def _add_bounds(self, shape: QGraphicsItem, alpha: float, beta: float) -> QGraphicsSimpleTextItem:
        font = QFont()
        font.setPixelSize(int(NODE_SIZE * BOUNDS_TEXT_SIZE))
        item = self.scene().addSimpleText(f"α = {number_text(alpha)}\nβ = {number_text(beta)}", font)
        item.setBrush(self.palette().text())
        center = shape.boundingRect().center()
        item.setPos(center.x() + NODE_SIZE * 0.55, center.y() - NODE_SIZE * 0.65)
        return item


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


# Text in the middle of a node, a bound gets ≤ or ≥, a node without a value stays empty
def _value_text(node_state: NodeState | None) -> str:
    if node_state is None or node_state.value is None:
        return ""
    return value_text(node_state.value, node_state.kind)
