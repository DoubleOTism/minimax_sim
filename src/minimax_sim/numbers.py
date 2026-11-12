"""
How values are written for the user, in the tree, the panel and the step explanation.
"""

from math import isinf

from minimax_sim.core.events import ValueKind

# Sign in front of a value that is only a bound
BOUND_SIGNS = {ValueKind.EXACT: "", ValueKind.UPPER: "≤", ValueKind.LOWER: "≥"}


# Number without ".0", 3.0 is shown as 3, infinity as ∞
def number_text(value: float) -> str:
    if isinf(value):
        return "∞" if value > 0 else "-∞"
    if isinstance(value, float) and value.is_integer():
        return str(int(value))
    return str(value)


# Value with ≤ or ≥ in front when it is only a bound
def value_text(value: float, kind: ValueKind) -> str:
    return BOUND_SIGNS[kind] + number_text(value)
