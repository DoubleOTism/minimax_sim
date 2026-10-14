# minimax_sim

[Česky](#česky) | [English](#english)

## Česky

Simulátor minimaxu a alfa-beta prořezávání. Semestrální práce 4IZ504.

Python 3.12+ a PySide6. Testováno na Arch Linuxu + KDE Plasma + Wayland.

### Spuštění

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

Nastavení se mění v `scripts/run.sh`.

### Ovládání

Šipky krokují, Home a End skočí na začátek a konec, mezerník spustí přehrávání. Ctrl + kolečko přibližuje, Ctrl + 0 přizpůsobí strom oknu, F9 schová panel.

Vlastní strom se zadává v panelu vpravo v Rosenově zápisu a načte se přes Ctrl + Enter:

```
( (((3 17) (2 12)) ((15) (25 0))) (((2 5) (3)) ((2 14))) )
```

### Testy

```sh
.venv/bin/python -m pytest
```

## English

Minimax and alpha-beta pruning simulator. Semester project for 4IZ504.

Python 3.12+ and PySide6. Tested on Arch Linux + KDE Plasma + Wayland.

### Running

With the system Python:

```sh
sudo pacman -S pyside6
./scripts/run.sh --system
```

With Python from pip (creates `.venv`, run once):

```sh
./scripts/setup.sh
./scripts/run.sh
```

Settings are changed in `scripts/run.sh`.

### Controls

Arrows step, Home and End jump to the start and the end, Space starts the playback. Ctrl + wheel zooms, Ctrl + 0 fits the tree to the window, F9 hides the panel.

A custom tree goes into the panel on the right in Rosen's notation and loads with Ctrl + Enter:

```
( (((3 17) (2 12)) ((15) (25 0))) (((2 5) (3)) ((2 14))) )
```

### Tests

```sh
.venv/bin/python -m pytest
```
