# Wordle CLI

A command-line implementation of the Wordle word-guessing game built in Python.
The project is structured for clarity, testability, and easy extension.

---

## Project Structure

```
wordle/
├── game.py              # Core logic: LetterResult, GuessResult, evaluate_guess, Game
├── history.py           # Persistence: GameHistory reads and writes history.json
├── wordle.py            # CLI entry point: game loop, input handling, stats display
├── words.txt            # Word list — 685 unique valid five-letter words
├── history.json         # Auto-created on first run, stores completed games
├── pyproject.toml       # Pytest and Ruff configuration
├── README.md
├── .gitignore
└── tests/
    └── test_game.py     # 23 pytest tests covering logic, edge cases, and history
```

---

## How It Works

### Module Responsibilities

| Module | Responsibility |
|---|---|
| `game.py` | Pure logic — no file I/O, no printing |
| `history.py` | Pure persistence — no game logic, no printing |
| `wordle.py` | Orchestration — reads input, prints output, calls the other two |

Each module is independent. You can swap the CLI for a web API or a TUI
without touching `game.py` or `history.py`.

---

### The Core Algorithm — `evaluate_guess`

The tricky part of Wordle is **duplicate-letter handling**.
A naïve single-pass check marks letters as PRESENT without accounting
for how many times they appear in the secret, producing wrong results.

`evaluate_guess` uses a **two-pass Counter algorithm**:

```
secret = "spine"
guess  = "speed"

Counter(secret) → {s:1, p:1, i:1, n:1, e:1}

Pass 1 — exact matches first (CORRECT takes priority):
  pos 0: s == s → CORRECT,  pool = {s:0, p:1, i:1, n:1, e:1}
  pos 1: p == p → CORRECT,  pool = {s:0, p:0, i:1, n:1, e:1}

Pass 2 — present / absent for remaining positions:
  pos 2: 'e', pool[e]=1 → PRESENT, pool[e]=0
  pos 3: 'e', pool[e]=0 → ABSENT
  pos 4: 'd', pool[d]=0 → ABSENT

Result:  ✓  ✓  ~  ✗  ✗
```

**Time complexity: O(n)**  
**Space complexity: O(k)** where k is the alphabet size (bounded at 26)

The Counter ensures that a letter is never marked PRESENT more times
than it actually appears in the secret word.

---

### Game State

`Game` stores state as an append-only list of `GuessResult` objects.
`is_won` and `is_over` are computed properties derived from that list —
there are no mutable flags to accidentally forget to update.

```python
@property
def is_won(self) -> bool:
    return bool(self.guesses) and self.guesses[-1].word == self.secret

@property
def is_over(self) -> bool:
    return self.is_won or len(self.guesses) >= MAX_GUESSES
```

---

### History and Streaks

`GameHistory` reads and writes `history.json` as a JSON array:

```json
[
  { "won": true,  "attempts": 3, "word": "crane" },
  { "won": false, "attempts": 6, "word": "spine" }
]
```

**current_streak** — iterate records in reverse, count wins until a loss:

```
[Win, Win, Loss, Win, Win, Win]  →  current_streak = 3
```

**best_streak** — single linear scan tracking the longest run:

```
[Win, Win, Loss, Win, Win, Win]  →  best_streak = 3
```

---

## Requirements

- Python 3.12 or later
- `pytest` (testing)
- `ruff` (linting)

---

## Installation

```bash
# Clone or download the project
cd wordle

# Create and activate a virtual environment
python -m venv .venv

# Windows
.venv\Scripts\activate

# macOS / Linux
source .venv/bin/activate

# Install dependencies
pip install pytest ruff
```

---

## Running the Game

```bash
python wordle.py
```

You have 6 attempts to guess the secret five-letter word.
Type a valid word from the word list and press Enter.

> **Windows note:** If Unicode symbols appear garbled, run
> `$env:PYTHONUTF8 = "1"` in PowerShell before starting the game.
> The game also attempts to reconfigure stdout to UTF-8 automatically.

---

## Example Game

```
WORDLE
=========

_  _  _  _  _
_  _  _  _  _
_  _  _  _  _
_  _  _  _  _
_  _  _  _  _
_  _  _  _  _

Attempts remaining: 6/6

Enter your guess: crane

WORDLE
=========

C  R  A  N  E
✗  ~  ~  ✗  ✓

_  _  _  _  _
_  _  _  _  _
_  _  _  _  _
_  _  _  _  _
_  _  _  _  _

Attempts remaining: 5/6
```

**Win message:**
```
You got it in 4/6!
```

**Loss message:**
```
The word was SPINE.
```

**Statistics shown after every game:**
```
Statistics
----------
Games:          12
Wins:           9
Win percentage: 75.0%
Current streak: 3
Best streak:    5
```

---

## Running Tests

```bash
pytest -v
```

The test suite covers:

| Area | Tests |
|---|---|
| All-correct guess | `test_all_correct` |
| Mixed correct / present / absent | `test_mixed_result` |
| Duplicate letters (spine/speed) | `test_duplicate_spine_speed` |
| Duplicate letters in secret | `test_duplicate_letter_in_secret` |
| Extra duplicates marked absent | `test_duplicate_guess_exceeds_secret_count` |
| Invalid word rejected | `test_invalid_word_raises` |
| Win detection | `test_win` |
| Six failed guesses ends game | `test_six_failed_guesses` |
| Wrong length rejected | `test_wrong_length_raises` |
| Guess after game over | `test_guess_after_game_over_raises` |
| Invalid guess does not consume attempt | `test_invalid_guess_does_not_consume_attempt` |
| Wrong length does not consume attempt | `test_wrong_length_does_not_consume_attempt` |
| Board string contains header | `test_game_str_contains_header` |
| GuessResult string format | `test_guess_result_str` |
| Empty history stats | `test_empty_history` |
| Win percentage | `test_win_percentage` |
| Current streak | `test_current_streak` |
| Best streak | `test_best_streak` |
| Best streak at start of history | `test_best_streak_at_start` |
| History persists to disk | `test_history_persistence` |
| Corrupted JSON raises error | `test_corrupted_history_raises` |
| Non-array JSON raises error | `test_history_not_list_raises` |
| Invalid entry raises error | `test_history_invalid_entry_raises` |

---

## Running the Linter

```bash
ruff check .
```

Ruff is configured in `pyproject.toml` with the following rule sets:
`E`, `W`, `F`, `I`, `B`, `C4`, `UP`, `N`.

---

## Constants

All magic numbers live in one place:

```python
# game.py
WORD_LENGTH = 5
MAX_GUESSES = 6
```

Every other module imports from `game.py`. Nothing is hardcoded elsewhere.

---

## Extending the Project

| Extension | What to change |
|---|---|
| Add a web API | Wrap `game.py` and `history.py` in Flask or FastAPI — no changes needed to core logic |
| Add hard mode | Subclass `Game`, override `make_guess` to enforce revealed-letter constraints |
| Add a solver | Add `solver.py` — filter word list after each guess, pick the word with highest entropy |
| Richer terminal UI | Replace `print` calls in `wordle.py` with `rich` or `textual` — core modules unchanged |
| Store history in SQLite | Replace `history.py` internals — public API stays identical |
