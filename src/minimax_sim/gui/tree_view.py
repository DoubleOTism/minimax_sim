"""
Draws the game tree from a Layout.

The Layout gives each node a position in abstract units, leaves at x = 0, 1, 2, ...
and levels at y = 0, 1, 2, ... This module turns them into pixels and draws
the nodes and edges on a QGraphicsScene shown in a scrollable QGraphicsView.

Nodes follow Rosen's notation, MAX nodes are squares and MIN nodes are circles.
Colours come from the system theme, so the tree works in light and dark mode.
"""

from PySide6.QtCore import QPointF, QRectF
from PySide6.QtGui import QPainter, QPen
from PySide6.QtWidgets import QGraphicsScene, QGraphicsView

from minimax_sim.core.events import NodeId
from minimax_sim.session.layout import Layout

# Size of one node in pixels
NODE_SIZE = 40

# Distance between neighbouring leaves, in node sizes
X_SPACING = 1.6

# Distance between levels, in node sizes
Y_SPACING = 2.6


# Scrollable view of the tree, MAX nodes are squares and MIN nodes are circles
class TreeView(QGraphicsView):
    def __init__(self) -> None:
        super().__init__()
        self.setScene(QGraphicsScene(self))
        self.setRenderHint(QPainter.RenderHint.Antialiasing)

    # Throw away what is drawn and draw the whole tree again
    def show_layout(self, layout: Layout) -> None:
        scene = self.scene()
        scene.clear()

        # Colours of the current system theme, so it works in both light and dark mode
        pen = QPen(self.palette().text().color(), 2)
        brush = self.palette().base()

        # Edges first, so the nodes cover their ends
        for layout_node in layout.nodes.values():
            start = self._position(layout, layout_node.node)
            for child in layout_node.children:
                end = self._position(layout, child)
                scene.addLine(start.x(), start.y(), end.x(), end.y(), pen)

        for layout_node in layout.nodes.values():
            center = self._position(layout, layout_node.node)
            rect = QRectF(center.x() - NODE_SIZE / 2, center.y() - NODE_SIZE / 2, NODE_SIZE, NODE_SIZE)
            if layout_node.is_max:
                scene.addRect(rect, pen, brush)
            else:
                scene.addEllipse(rect, pen, brush)

    # Centre of a node in scene pixels
    def _position(self, layout: Layout, node: NodeId) -> QPointF:
        layout_node = layout.nodes[node]
        return QPointF(layout_node.x * X_SPACING * NODE_SIZE, layout_node.y * Y_SPACING * NODE_SIZE)