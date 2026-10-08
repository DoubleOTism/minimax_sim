"""
Shared test setup.
Loaded by pytest automatically before the tests.
"""

import pytest

from minimax_sim.core.games.abstract_tree import AbstractTree


# Rosen's example tree, used as reference for the search tests
ROSEN = "( (((3 17) (2 12)) ((15) (25 0))) (((2 5) (3)) ((2 14))) )"


# A fresh Rosen tree game for every test that asks for "rosen"
@pytest.fixture
def rosen() -> AbstractTree:
    return AbstractTree(ROSEN)
