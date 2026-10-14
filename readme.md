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
