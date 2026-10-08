"""
Tests for the node positions.
"""

from minimax_sim.session.layout import layout


# Rosen's tree: 26 nodes, leaves side by side, every parent centred above its children
def test_rosen_layout(rosen):
    tree = layout(rosen, rosen.initial_state(), None)
    assert tree is not None
    assert len(tree.nodes) == 26
    root = tree.nodes[()]
    assert root.y == 0 and root.is_max
    assert root.children == ((0,), (1,))
    assert not tree.nodes[(0,)].is_max

    # Leaves get consecutive x from left to right
    leaves = [node for node in tree.nodes.values() if not node.children]
    assert [leaf.x for leaf in leaves] == list(range(12))

    # Parent centred above its children, one level higher
    for node in tree.nodes.values():
        if node.children:
            child_xs = [tree.nodes[child].x for child in node.children]
            assert node.x == (min(child_xs) + max(child_xs)) / 2
            assert all(tree.nodes[child].y == node.y + 1 for child in node.children)
    assert tree.nodes[(0, 1, 1)].label == "1"
    assert tree.width == 12 and tree.depth == 4


# The same tree always gives the same positions
def test_layout_deterministic(rosen):
    assert layout(rosen, rosen.initial_state(), None) == layout(rosen, rosen.initial_state(), None)


# Depth limit cuts the tree, too many nodes gives None
def test_layout_respects_depth_limit_and_node_limit(rosen):
    tree = layout(rosen, rosen.initial_state(), 2)
    assert tree is not None and len(tree.nodes) == 7 and tree.depth == 2
    assert layout(rosen, rosen.initial_state(), None, max_nodes=26) is not None
    assert layout(rosen, rosen.initial_state(), None, max_nodes=25) is None