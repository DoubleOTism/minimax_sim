"""
Czech user-facing texts.
"""

# core: abstract tree parser
PARSE_UNEXPECTED_CHAR = "Neočekávaný znak {char!r} na pozici {pos}."
PARSE_UNEXPECTED_CLOSE = "Neočekávaná ')' na pozici {pos}."
PARSE_MISSING_CLOSE = "Chybí ')' (seznam otevřený na pozici {pos} není uzavřen)."
PARSE_EMPTY_LIST = "Prázdný seznam '()' na pozici {pos}: vnitřní uzel musí mít potomky."
PARSE_EMPTY_INPUT = "Prázdný vstup."
PARSE_TRAILING = "Nadbytečný text na pozici {pos} za koncem stromu."
PARSE_NOT_FINITE = "Hodnota {token!r} na pozici {pos} není konečné číslo."
TREE_NO_HEURISTIC = "Abstraktní strom nemá heuristiku, limit hloubky pro něj není podporovaný."


# session
TRACE_LIMIT = "Běh zastaven: překročen limit {limit} událostí. Snižte limit hloubky nebo zvolte rozehranou pozici."
TREE_TOO_BIG = "Strom je příliš velký na vykreslení (limit {limit} uzlů). Snižte limit hloubky nebo zvolte rozehranou pozici."

# gui
APP_TITLE = "Simulátor minimaxu a alfa-beta prořezávání"
STEP_TO_START = "Na začátek"
STEP_BACK = "Krok zpět"
STEP_FORWARD = "Krok vpřed"
STEP_TO_END = "Na konec"
STEP_COUNTER = "Krok {current} z {total}"
STEP_COUNTER_UNKNOWN_TOTAL = "Krok {current}"
ALGORITHM_MINIMAX = "Minimax"
ALGORITHM_ALPHABETA = "Alfa-beta"
PRUNE_GE = "Prořezávat při α ≥ β"
PRUNE_GT = "Prořezávat při α > β"
HIDE_UNVISITED = "Skrýt nenavštívené"