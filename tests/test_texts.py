"""
Test that basically just verifies that all languages (for now just en and cs) define the same texts with the same placeholders.
"""

import string

from minimax_sim.texts import cs, en


def names(module) -> set[str]:
    return {n for n in vars(module) if n.isupper()}


def placeholders(text: str) -> set[str]:
    return {field for _, field, _, _ in string.Formatter().parse(text) if field}


# Every text exists in both languages
def test_same_names():
    assert names(cs) == names(en)


# A translation must not drop or rename a {placeholder}, or .format() breaks
def test_same_placeholders():
    for name in names(cs):
        assert placeholders(getattr(cs, name)) == placeholders(getattr(en, name)), name
