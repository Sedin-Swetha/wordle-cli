"""Tests for the Wordle game logic and history."""

import json
from pathlib import Path

import pytest

from game import (
    MAX_GUESSES,
    WORD_LENGTH,
    Game,
    LetterResult,
    evaluate_guess,
)
from history import GameHistory

WORD_LIST = [
    "crane", "spine", "speed", "bland", "abide",
    "blast", "blaze", "blend", "brave", "break",
    "breed", "brief", "bring", "broke", "brook",
    "brown", "build", "burst", "catch", "chess",
    "child", "claim", "clean", "clear", "climb",
    "clock", "close", "cloud", "coach", "count",
    "cover", "crack", "cross", "crowd", "crush",
    "dance", "death", "delay", "depot", "depth",
    "ditch", "doing", "doubt", "dough", "draft",
    "drain", "drama", "drank", "dream", "dress",
    "dried", "drift", "drink", "drive", "drone",
    "drove", "drown", "dryer", "dunno", "dying",
]


def make_game(secret: str = "crane") -> Game:
    return Game(secret, WORD_LIST)


def test_all_correct() -> None:
    """evaluate_guess('crane', 'crane') must return all CORRECT."""
    result = evaluate_guess("crane", "crane")
    assert all(r == LetterResult.CORRECT for r in result.results)
    assert result.word == "crane"


def test_mixed_result() -> None:
    """A guess with correct, present, and absent letters is handled correctly.

    secret = 'crane', guess = 'abide'
      a → PRESENT  (a is in 'crane' but not at position 0)
      b → ABSENT
      i → ABSENT
      d → ABSENT
      e → CORRECT  (e at index 4 matches)
    """
    result = evaluate_guess("crane", "abide")
    assert result.results[0] == LetterResult.PRESENT
    assert result.results[1] == LetterResult.ABSENT
    assert result.results[2] == LetterResult.ABSENT
    assert result.results[3] == LetterResult.ABSENT
    assert result.results[4] == LetterResult.CORRECT


def test_duplicate_spine_speed() -> None:
    """evaluate_guess('spine', 'speed') → CORRECT CORRECT PRESENT ABSENT ABSENT."""
    result = evaluate_guess("spine", "speed")
    expected = [
        LetterResult.CORRECT,
        LetterResult.CORRECT,
        LetterResult.PRESENT,
        LetterResult.ABSENT,
        LetterResult.ABSENT,
    ]
    assert result.results == expected


def test_duplicate_letter_in_secret() -> None:
    """Exact matches consume letters before PRESENT matching occurs.

    secret = 'breed', guess = 'creek'
      c → ABSENT
      r → CORRECT  (r at index 1 matches in both)
      e → CORRECT  (e at index 2 matches)
      e → CORRECT  (e at index 3 matches)
      k → ABSENT
    """
    result = evaluate_guess("breed", "creek")
    assert result.results[0] == LetterResult.ABSENT
    assert result.results[1] == LetterResult.CORRECT
    assert result.results[2] == LetterResult.CORRECT
    assert result.results[3] == LetterResult.CORRECT
    assert result.results[4] == LetterResult.ABSENT


def test_duplicate_guess_exceeds_secret_count() -> None:
    """Extra duplicate letters beyond the count in the secret are ABSENT.

    secret = 'bland', guess = 'blaze'
    """
    result = evaluate_guess("bland", "blaze")
    assert result.results[0] == LetterResult.CORRECT
    assert result.results[1] == LetterResult.CORRECT
    assert result.results[2] == LetterResult.CORRECT
    assert result.results[3] == LetterResult.ABSENT
    assert result.results[4] == LetterResult.ABSENT


def test_invalid_word_raises() -> None:
    """make_guess with a word not in the word list raises ValueError."""
    game = make_game()
    with pytest.raises(ValueError, match="not in the word list"):
        game.make_guess("zzzzz")


def test_win() -> None:
    """Guessing the secret sets is_won to True."""
    game = make_game("crane")
    game.make_guess("crane")
    assert game.is_won is True
    assert game.is_over is True


def test_six_failed_guesses() -> None:
    """Six incorrect guesses exhaust all attempts and end the game."""
    wrong_words = ["bland", "blaze", "blend", "brave", "break", "breed"]
    game = make_game("crane")
    for word in wrong_words:
        game.make_guess(word)
    assert game.is_over is True
    assert game.is_won is False
    assert len(game.guesses) == MAX_GUESSES


def test_wrong_length_raises() -> None:
    """Guesses with the wrong length raise ValueError."""
    game = make_game()
    with pytest.raises(ValueError, match=f"exactly {WORD_LENGTH}"):
        game.make_guess("hi")


def test_guess_after_game_over_raises() -> None:
    """Guessing after the game is over raises RuntimeError."""
    game = make_game("crane")
    game.make_guess("crane")
    with pytest.raises(RuntimeError, match="already over"):
        game.make_guess("crane")


def test_invalid_guess_does_not_consume_attempt() -> None:
    """An invalid guess does not count as an attempt."""
    game = make_game("crane")
    try:
        game.make_guess("zzzzz")
    except ValueError:
        pass
    assert len(game.guesses) == 0


def test_wrong_length_does_not_consume_attempt() -> None:
    """A wrong-length guess does not count as an attempt."""
    game = make_game("crane")
    try:
        game.make_guess("hi")
    except ValueError:
        pass
    assert len(game.guesses) == 0


def test_game_str_contains_header() -> None:
    """Game.__str__ includes the WORDLE header."""
    game = make_game()
    assert "WORDLE" in str(game)


def test_guess_result_str() -> None:
    """GuessResult.__str__ includes the word letters and symbols."""
    result = evaluate_guess("crane", "crane")
    text = str(result)
    assert "C" in text and "✓" in text


def test_empty_history(tmp_path: Path) -> None:
    """A fresh history has zero games and all stats at zero."""
    h = GameHistory(tmp_path / "history.json")
    assert h.total_games == 0
    assert h.total_wins == 0
    assert h.win_percentage == 0.0
    assert h.current_streak == 0
    assert h.best_streak == 0


def test_win_percentage(tmp_path: Path) -> None:
    """Win percentage is calculated correctly."""
    h = GameHistory(tmp_path / "history.json")
    h.record_game(won=True, attempts=3, word="crane")
    h.record_game(won=False, attempts=6, word="spine")
    h.record_game(won=True, attempts=4, word="speed")
    assert h.total_games == 3
    assert h.total_wins == 2
    assert abs(h.win_percentage - 66.666) < 0.1


def test_current_streak(tmp_path: Path) -> None:
    """Current streak counts consecutive wins from the most recent game."""
    h = GameHistory(tmp_path / "history.json")
    for won in [True, True, False, True, True, True]:
        h.record_game(won=won, attempts=3, word="crane")
    assert h.current_streak == 3


def test_best_streak(tmp_path: Path) -> None:
    """Best streak finds the longest consecutive win run."""
    h = GameHistory(tmp_path / "history.json")
    for won in [True, True, False, True, True, True]:
        h.record_game(won=won, attempts=3, word="crane")
    assert h.best_streak == 3


def test_best_streak_at_start(tmp_path: Path) -> None:
    """Best streak correctly identifies a streak at the beginning of history."""
    h = GameHistory(tmp_path / "history.json")
    for won in [True, True, True, False, True]:
        h.record_game(won=won, attempts=2, word="crane")
    assert h.best_streak == 3


def test_history_persistence(tmp_path: Path) -> None:
    """Games are persisted to disk and reloaded correctly."""
    hist_file = tmp_path / "history.json"
    h1 = GameHistory(hist_file)
    h1.record_game(won=True, attempts=2, word="crane")
    h2 = GameHistory(hist_file)
    assert h2.total_games == 1
    assert h2.total_wins == 1


def test_corrupted_history_raises(tmp_path: Path) -> None:
    """A corrupted history file raises ValueError on load."""
    hist_file = tmp_path / "history.json"
    hist_file.write_text("not valid json{{", encoding="utf-8")
    with pytest.raises(ValueError, match="invalid JSON"):
        GameHistory(hist_file)


def test_history_not_list_raises(tmp_path: Path) -> None:
    """A history file that is not a JSON array raises ValueError."""
    hist_file = tmp_path / "history.json"
    hist_file.write_text('{"key": "value"}', encoding="utf-8")
    with pytest.raises(ValueError, match="JSON array"):
        GameHistory(hist_file)


def test_history_invalid_entry_raises(tmp_path: Path) -> None:
    """A history entry missing required keys raises ValueError."""
    hist_file = tmp_path / "history.json"
    hist_file.write_text(json.dumps([{"won": True}]), encoding="utf-8")
    with pytest.raises(ValueError, match="invalid entry"):
        GameHistory(hist_file)
