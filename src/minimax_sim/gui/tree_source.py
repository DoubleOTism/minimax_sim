"""
Input of the abstract tree, shown at the top of the side panel.

Presets, the player in the root and the tree text in Rosen's format.
It parses the text itself and hands a ready game to the page.
The bubble over a node describes it: who moves there or the value of the leaf, and the leaves below it.
"""

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QKeySequence, QShortcut
from PySide6.QtWidgets import (
    QComboBox,
    QGroupBox,
    QLabel,
    QPlainTextEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from minimax_sim import texts
from minimax_sim.core.games.abstract_tree import AbstractTree, ParseError, Tree, TreeState
from minimax_sim.numbers import number_text

# Most leaf values listed for one node, a larger subtree gets only the first ones and the count
MAX_LISTED_LEAVES = 8


# Presets, root player and tree text, sends a game when a valid tree should be loaded
class TreeSource(QWidget):
    # Sent with the game and its depth limit, the abstract tree has none
    game_requested = Signal(object, object)

    # presets are pairs of name and tree text, the first one fills the text field
    def __init__(self, presets: list[tuple[str, str]]) -> None:
        super().__init__()
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)

        # Everything sits in one group, like the parts of the tic-tac-toe panel
        group = QGroupBox(texts.TREE_GROUP)
        outer.addWidget(group)
        column = QVBoxLayout(group)

        # Prepared trees, choosing one puts it into the text field and loads it
        # A loaded tree that matches no preset shows as the custom tree
        column.addWidget(QLabel(texts.PRESET_LABEL))
        self.preset_box = QComboBox()
        self.preset_box.setPlaceholderText(texts.PRESET_CUSTOM)
        for name, tree in presets:
            self.preset_box.addItem(name, tree)
        self.preset_box.activated.connect(self._preset_chosen)
        column.addWidget(self.preset_box)

        # Who moves first in the root, each item carries the value of root_is_max as data
        column.addWidget(QLabel(texts.ROOT_LABEL))
        self.root_box = QComboBox()
        self.root_box.addItem(texts.ROOT_MAX, True)
        self.root_box.addItem(texts.ROOT_MIN, False)
        self.root_box.currentIndexChanged.connect(self._root_player_selected)
        column.addWidget(self.root_box)

        # Tree text, long lines scroll sideways instead of wrapping
        # Enter makes a new line, so loading has its own shortcut
        column.addWidget(QLabel(texts.TREE_LABEL))
        self.tree_edit = QPlainTextEdit(presets[0][1])
        self.tree_edit.setLineWrapMode(QPlainTextEdit.LineWrapMode.NoWrap)
        column.addWidget(self.tree_edit, 1)
        for keys in ("Ctrl+Return", "Ctrl+Enter"):
            shortcut = QShortcut(QKeySequence(keys), self.tree_edit)
            shortcut.setContext(Qt.ShortcutContext.WidgetShortcut)
            shortcut.activated.connect(self.request_load)

        load_button = QPushButton(texts.TREE_LOAD)
        load_button.clicked.connect(self.request_load)
        column.addWidget(load_button)

        # Problems with the tree, empty when all is fine
        self.message_label = QLabel()
        self.message_label.setWordWrap(True)
        column.addWidget(self.message_label)

        # Last tree that was loaded, the root player switch loads it again
        self._tree_text = presets[0][1]

    # Load the tree from the text field
    def request_load(self) -> None:
        self._load(self.tree_edit.toPlainText())

    # Show a message under the tree text, empty clears it
    def show_message(self, message: str) -> None:
        self.message_label.setText(message)

    # A node of the abstract tree has no position to show, the step explanation says what happens
    def show_node(self, state: TreeState, move: int | None, depth: int) -> None:
        pass

    # Text of the bubble over a node: who moves there or the value of the leaf, and the leaves below it
    def node_tooltip(self, state: TreeState, move: int | None, depth: int) -> str:
        return _node_text(state, depth).replace("\n", "<br>")

    # Parse the text and send the game, or keep the old tree and show where the text is wrong
    def _load(self, text: str) -> None:
        try:
            game = AbstractTree(text, root_is_max=self.root_box.currentData())
        except ParseError as error:
            self.show_message(str(error))
            cursor = self.tree_edit.textCursor()
            cursor.setPosition(error.pos)
            self.tree_edit.setTextCursor(cursor)
            self.tree_edit.setFocus()
            return
        self._tree_text = text
        self.preset_box.setCurrentIndex(self.preset_box.findData(text))
        self.game_requested.emit(game, None)

    # Put the chosen preset into the text field and load it
    def _preset_chosen(self) -> None:
        self.tree_edit.setPlainText(self.preset_box.currentData())
        self.request_load()

    # Load the current tree again with the other player in the root
    # The text field may be edited and not loaded yet, so the last loaded tree is used
    def _root_player_selected(self) -> None:
        self._load(self._tree_text)


# Who moves in the node or the value of the leaf, its depth and the leaves below it
def _node_text(state: TreeState, depth: int) -> str:
    if not isinstance(state.node, tuple):
        return texts.TREE_NODE_LEAF.format(value=number_text(state.node), depth=depth)
    player = texts.TREE_NODE_MAX if state.is_max else texts.TREE_NODE_MIN
    leaves = _leaf_values(state.node)
    listed = ", ".join(number_text(value) for value in leaves[:MAX_LISTED_LEAVES])
    if len(leaves) > MAX_LISTED_LEAVES:
        listed = texts.TREE_NODE_MORE_LEAVES.format(values=listed, count=len(leaves))
    lines = (
        player.format(children=len(state.node)),
        texts.TREE_NODE_DEPTH.format(depth=depth),
        texts.TREE_NODE_LEAVES.format(values=listed),
    )
    return "\n".join(lines)


# Values of all leaves below a node, from left to right
def _leaf_values(tree: Tree) -> list[float]:
    if not isinstance(tree, tuple):
        return [tree]
    return [value for child in tree for value in _leaf_values(child)]
