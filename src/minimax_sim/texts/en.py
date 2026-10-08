"""
English user-facing texts.
"""

# core: abstract tree parser
PARSE_UNEXPECTED_CHAR = "Unexpected character {char!r} at position {pos}."
PARSE_UNEXPECTED_CLOSE = "Unexpected ')' at position {pos}."
PARSE_MISSING_CLOSE = "Missing ')' (list opened at position {pos} is not closed)."
PARSE_EMPTY_LIST = "Empty list '()' at position {pos}: an inner node needs children."
PARSE_EMPTY_INPUT = "Empty input."
PARSE_TRAILING = "Extra text at position {pos} after the end of the tree."
PARSE_NOT_FINITE = "Value {token!r} at position {pos} is not a finite number."
TREE_NO_HEURISTIC = "The abstract tree has no heuristic, so a depth limit is not supported for it."


# session
TRACE_LIMIT = "Run stopped: the limit of {limit} events was exceeded. Lower the depth limit or pick a position further into the game."
TREE_TOO_BIG = "The tree is too big to draw (limit {limit} nodes). Lower the depth limit or pick a position further into the game."