"""
Draws the game tree from a Layout and a Snapshot.

The Layout gives each node a position in abstract units, leaves at x = 0, 1, 2, ...
and levels at y = 0, 1, 2, ... This module turns them into pixels and draws
the nodes and edges on a QGraphicsScene shown in a scrollable QGraphicsView.

Nodes follow Rosen's notation, MAX nodes are squares and MIN nodes are circles.
The Snapshot decides how each node looks (active, on the path, done, pruned)
and which value it shows.
Colours come from the system theme, so the tree works in light and dark mode.
"""

from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import QBrush, QColor, QFont, QPainter, QPen
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

# Opacity of the fill of nodes on the path, 0 to 255
PATH_FILL_ALPHA = 90

# Sign in front of a value that is only a bound
BOUND_SIGNS = {ValueKind.EXACT: "", ValueKind.UPPER: "≤", ValueKind.LOWER: "≥"}


# Scrollable view of the tree, MAX nodes are squares and MIN nodes are circles
class TreeView(QGraphicsView):
    def __init__(self) -> None:
        super().__init__()
        self.setScene(QGraphicsScene(self))
        self.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Whether nodes the search has not reached yet are left out
        self.hide_unvisited = False

    # Throw away what is drawn and draw the whole tree again
    def draw(self, layout: Layout, snapshot: Snapshot) -> None:
        scene = self.scene()
        scene.clear()
        statuses = _statuses(layout, snapshot)

        # The scene always spans the whole tree, so it does not move when nodes are hidden
        scene.setSceneRect(self._tree_rect(layout))

        # Edges first, so the nodes cover their ends, each edge looks like the child it leads to
        for layout_node in layout.nodes.values():
            start = self._position(layout, layout_node.node)
            for child in layout_node.children:
                if self._is_hidden(statuses[child]):
                    continue
                end = self._position(layout, child)
                scene.addLine(start.x(), start.y(), end.x(), end.y(), self._pen(statuses[child]))

        for layout_node in layout.nodes.values():
            node = layout_node.node
            status = statuses[node]
            if self._is_hidden(status):
                continue
            center = self._position(layout, node)
            rect = QRectF(center.x() - NODE_SIZE / 2, center.y() - NODE_SIZE / 2, NODE_SIZE, NODE_SIZE)
            if layout_node.is_max:
                scene.addRect(rect, self._pen(status), self._brush(status))
            else:
                scene.addEllipse(rect, self._pen(status), self._brush(status))

            node_state = snapshot.nodes.get(node)
            if node_state is not None and node_state.value is not None:
                self._add_value(center, BOUND_SIGNS[node_state.kind] + _number(node_state.value), status)

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
    def _pen(self, status: Status) -> QPen:
        palette = self.palette()
        if status in (Status.ACTIVE, Status.ON_PATH):
            return QPen(palette.highlight().color(), LINE_WIDTH * 2)
        if status is Status.DONE:
            return QPen(palette.text().color(), LINE_WIDTH)
        if status is Status.PRUNED:
            return QPen(palette.placeholderText().color(), LINE_WIDTH, Qt.PenStyle.DotLine)
        return QPen(palette.placeholderText().color(), LINE_WIDTH)

    # Fill of a node
    def _brush(self, status: Status) -> QBrush:
        palette = self.palette()
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


# Number without a useless ".0", 3.0 is shown as 3
def _number(value: float) -> str:
    if isinstance(value, float) and value.is_integer():
        return str(int(value))
    return str(value)