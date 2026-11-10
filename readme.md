# minimax_sim

Simulátor minimaxu a alfa-beta prořezávání. Semestrální práce 4IZ504.

Python 3.12+ a PySide6. Testováno na Arch Linuxu + KDE Plasma + Wayland.

## Spuštění

Se systémovým Pythonem:

```sh
sudo pacman -S pyside6
./scripts/run.sh --system
```

S Pythonem z pipu (vytvoří `.venv`, stačí jednou):

```sh
./scripts/setup.sh
./scripts/run.sh
```

Na X11 je dle všeho ještě potřeba `sudo pacman -S xcb-util-cursor xcb-util-wm xcb-util-image xcb-util-keysyms xcb-util-renderutil`.
Na X11 zatím nevyzkoušeno.

Nastavení se mění v `scripts/run.sh`.

## Ovládání

Šipky krokují, Home a End skočí na začátek a konec, mezerník spustí přehrávání. Ctrl + kolečko přibližuje, Ctrl + 0 přizpůsobí strom oknu, F9 schová panel.

Vlastní strom se zadává v panelu vpravo v Rosenově zápisu a načte se přes Ctrl + Enter:

```
( (((3 17) (2 12)) ((15) (25 0))) (((2 5) (3)) ((2 14))) )
```

## Vlastní předvolby

Vlastní stromy i pozice piškvorek se dají přidat do JSON souboru, vzor je v `presets.example.json`:

```json
{
  "trees": {
    "Název stromu v nabídce": "((3 12 8) (2 4 6) (14 5 2))"
  },
  "tictactoe": {
    "Název pozice v nabídce": {
      "board": "O.. .X. ...",
      "depth_limit": 3,
      "prefer_fast": true
    }
  }
}
```

Obě části jsou nepovinné. V `trees` je strom zapsaný stejně jako v panelu. V `tictactoe` je pozice piškvorek:

- `board` je deska po řádcích, `.` je prázdné pole, mezery se ignorují
- `depth_limit` je limit hloubky, `null` znamená bez limitu
- `prefer_fast` je „rychlejší výhra má vyšší hodnotu“, když chybí, je zapnuté

Soubor se zapne v `scripts/run.sh` přes `MINIMAX_PRESETS`.

## Testy

Se systémovým Pythonem:

```sh
sudo pacman -S python-pytest
PYTHONPATH=src python -m pytest
```

S Pythonem z pipu:

```sh
.venv/bin/python -m pytest
```
