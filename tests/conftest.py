"""
Shared test setup.
Loaded by pytest automatically before the tests.
"""

import os

import pytest

from minimax_sim.core.games.abstract_tree import AbstractTree

# GUI tests draw without opening a window, also on a machine without a display
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

# Rosen's example tree, used as reference for the search tests
ROSEN = "( (((3 17) (2 12)) ((15) (25 0))) (((2 5) (3)) ((2 14))) )"


# A fresh Rosen tree game for every test that asks for "rosen"
@pytest.fixture
def rosen() -> AbstractTree:
    return AbstractTree(ROSEN)


# One Qt application for all GUI tests, Qt allows only one per process
@pytest.fixture(scope="session")
def qt_app():
    from PySide6.QtWidgets import QApplication

    return QApplication.instance() or QApplication([])
