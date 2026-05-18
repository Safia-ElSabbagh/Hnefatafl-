# ᚺᚾᛖᚠᚨᛏᚨᚠᛚ — Hnefatafl: The Viking Chess Game

> *An ancient Norse strategy game brought to life with Python, Pygame, and AI.*

![Python](https://img.shields.io/badge/Python-3.8%2B-blue?style=flat-square&logo=python)
![Tkinter](https://img.shields.io/badge/tkinter-green?style=flat-square)
![AI](https://img.shields.io/badge/AI-Alpha--Beta%20Pruning-red?style=flat-square)

---

## 📖 About

**Hnefatafl** (pronounced *"nef-ah-tah-fel"*) is a two-player asymmetric Viking board game dating back to 400 AD. This project is a fully playable **Human vs. Computer** implementation built in Python, featuring a rich graphical interface and an AI opponent powered by the **Alpha-Beta Pruning** algorithm.

---

## 🎮 Gameplay

The game is played on an **11×11 board** between two asymmetric sides:

| Side | Pieces | Goal |
|------|--------|------|
| **Attackers** (Black) | 24 soldiers | Capture the King |
| **Defenders** (White) | 12 soldiers + 1 King | Escort the King to any corner |

### Rules at a Glance

- **Movement:** All pieces move any number of squares horizontally or vertically — exactly like a Rook in Chess. They cannot jump over other pieces.
- **Capture (Custodial):** A piece is captured when it is sandwiched between two enemy pieces, or between an enemy piece and a special square (throne or corner).
- **Special squares:** The central **Throne** and the four **corner squares** act as hostile squares that assist in captures.
- **King capture:** Attackers win by surrounding the King on all four sides (three sides if against a wall; two sides if in a corner).
- **King escape:** Defenders win if the King reaches any of the four corner squares.
- **Turn order:** Attackers always move first.

---

## ✨ Features

- 🤖 **AI opponent** using Alpha-Beta Pruning with a multi-factor heuristic evaluation function
- 🎚️ **Three difficulty levels** — Easy (depth 1), Medium (depth 2), Hard (depth 3)
- ⚔️ **Choose your side** — play as Attacker or Defender
- 🎨 **Full Pygame GUI** with animated move hints, piece selection glow, last-move highlights, and a Viking rune aesthetic
- 🏆 **Victory & defeat overlays** with game-over detection for all win conditions
- 🔄 **New Game / Return to Menu** without restarting the application
- 🧵 **Threaded AI computation** — the UI stays responsive while the computer thinks

---

## 🗂️ Project Structure

```
hnefatafl/
├── game_logic.py   # Pure game engine: board, rules, move generation, AI
├── gui.py          # Pygame interface: rendering, menus, input handling
└── README.md
```

### Module Responsibilities

**`game_logic.py`** — no GUI dependency, fully self-contained:
- Board representation and initialization
- Move generation (rook-style, with throne/corner restrictions)
- Custodial capture detection
- Win condition checking (king escape, king capture, no moves)
- Heuristic evaluation function (8 weighted factors)
- Alpha-Beta Pruning algorithm
- `get_computer_move()` entry point

**`gui.py`** — imports from `game_logic`:
- Pygame window, fonts, and colour palette
- Board, panel, and piece rendering
- Animated move dots and selection highlights
- Main menu with side/difficulty selection
- Game loop with threaded AI turns

---

## 🧠 AI Design

The AI uses **Alpha-Beta Pruning**, a minimax variant that prunes branches provably worse than already-found options, dramatically reducing the search space.

### Heuristic Evaluation (8 factors)

| # | Factor | Effect |
|---|--------|--------|
| 1 | Piece count ratio | More attackers alive → attacker advantage |
| 2 | King–corner distance | King far from corner → attacker advantage |
| 3 | King encirclement | More sides threatened → attacker advantage |
| 4 | King mobility | Fewer king moves → attacker advantage |
| 5 | Defender mobility | Fewer defender moves → attacker advantage |
| 6 | Attacker proximity to king | Attackers close to king → attacker advantage |
| 7 | King escape path control | Clear path to corner → defender advantage |
| 8 | Attacker route blocking | Attacker blocking escape path → attacker advantage |

The AI plays as **maximizer** (attacker) or **minimizer** (defender) depending on whose turn it is.

---


### Controls

| Input | Action |
|-------|--------|
| **Click** a piece | Select it (valid moves shown as animated dots) |
| **Click** a gold dot | Move the selected piece there |
| **N** | Start a new game |
| **ESC** | Return to the main menu |

---

## 🔗 Learn More About Hnefatafl

- [Video introduction (YouTube)](https://www.youtube.com/watch?v=fZ9cMj2Qn5Y)
- [Gameplay walkthrough (YouTube)](https://www.youtube.com/watch?v=pByySTArLe8)
