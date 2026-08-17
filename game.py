"""Core Wordle game logic: constants, enums, result types, and game class."""

from collections import Counter
from enum import Enum

WORD_LENGTH = 5
MAX_GUESSES = 6


class LetterResult(Enum):
    """Represents the evaluation outcome of a single letter in a guess."""

    CORRECT = "correct"
    PRESENT = "present"
    ABSENT = "absent"


class GuessResult:
    """Stores the outcome of one guess: the word and its per-letter results.

    Attributes:
        word: The five-letter word that was guessed.
        results: A list of LetterResult values, one per letter position.
    """

    def __init__(self, word: str, results: list[LetterResult]) -> None:
        self.word = word
        self.results = results

    def __str__(self) -> str:
        """Return a two-line string showing letters and their result symbols.

        Example::

            S  P  E  E  D
            ✓  ✓  ~  ✗  ✗
        """
        symbol_map = {
            LetterResult.CORRECT: "✓",
            LetterResult.PRESENT: "~",
            LetterResult.ABSENT: "✗",
        }
        letters_row = "  ".join(ch.upper() for ch in self.word)
        symbols_row = "  ".join(symbol_map[r] for r in self.results)
        return f"{letters_row}\n{symbols_row}"


def evaluate_guess(secret: str, guess: str) -> GuessResult:
    """Evaluate a guess against the secret word using a Counter-based algorithm.

    Uses a two-pass approach with a frequency Counter to handle duplicate
    letters correctly:

    Pass 1 — exact matches:
        For each position where guess[i] == secret[i], mark CORRECT and
        decrement that letter's count in the Counter so it cannot be
        matched again in Pass 2.

    Pass 2 — present / absent:
        For each unresolved position, check the Counter:
        - pool[letter] > 0  →  mark PRESENT, decrement the Counter.
        - pool[letter] == 0 →  mark ABSENT.

    This guarantees exact matches always take priority and a letter is
    never counted PRESENT more times than it appears in the secret.

    Time complexity:  O(n)
    Space complexity: O(k) where k is the alphabet size (bounded at 26)

    Args:
        secret: The five-letter target word (lower-case).
        guess:  The five-letter guessed word (lower-case).

    Returns:
        A GuessResult with per-letter LetterResult values.

    Example:
        >>> result = evaluate_guess("spine", "speed")
        >>> [r.value for r in result.results]
        ['correct', 'correct', 'present', 'absent', 'absent']
    """
    results = [LetterResult.ABSENT] * WORD_LENGTH
    pool = Counter(secret)

    for i in range(WORD_LENGTH):
        if guess[i] == secret[i]:
            results[i] = LetterResult.CORRECT
            pool[guess[i]] -= 1

    for i in range(WORD_LENGTH):
        if results[i] == LetterResult.CORRECT:
            continue
        if pool[guess[i]] > 0:
            results[i] = LetterResult.PRESENT
            pool[guess[i]] -= 1

    return GuessResult(guess, results)


class Game:
    """Manages a single Wordle game session.

    Attributes:
        secret:    The target word the player must guess.
        word_list: The list of valid guess words.
        guesses:   Ordered list of GuessResult objects for each valid guess made.
    """

    def __init__(self, secret: str, word_list: list[str]) -> None:
        self.secret = secret
        self.word_list = word_list
        self.guesses: list[GuessResult] = []

    @property
    def is_won(self) -> bool:
        """Return True if the last guess matched the secret word."""
        return bool(self.guesses) and self.guesses[-1].word == self.secret

    @property
    def is_over(self) -> bool:
        """Return True when the game has ended (won or all attempts used)."""
        return self.is_won or len(self.guesses) >= MAX_GUESSES

    def make_guess(self, word: str) -> GuessResult:
        """Submit a guess and return its GuessResult.

        Invalid guesses raise an exception and do not consume an attempt.

        Args:
            word: The word to guess (normalised to lower-case internally).

        Returns:
            A GuessResult for the submitted guess.

        Raises:
            RuntimeError: If the game is already over.
            ValueError:   If the word is the wrong length or not in the word list.
        """
        if self.is_over:
            raise RuntimeError("The game is already over.")

        normalised = word.strip().lower()

        if len(normalised) != WORD_LENGTH:
            raise ValueError(
                f"Guess must be exactly {WORD_LENGTH} characters, "
                f"got {len(normalised)}."
            )

        if normalised not in self.word_list:
            raise ValueError(f"'{normalised}' is not in the word list.")

        result = evaluate_guess(self.secret, normalised)
        self.guesses.append(result)
        return result

    def __str__(self) -> str:
        """Return the full board: played rows, empty rows, and attempt count.

        Example::

            WORDLE
            =========

            S  P  E  E  D
            ✓  ✓  ~  ✗  ✗

            _  _  _  _  _
            _  _  _  _  _

            Attempts remaining: 5/6
        """
        lines: list[str] = ["WORDLE", "=========", ""]

        for guess_result in self.guesses:
            lines.append(str(guess_result))
            lines.append("")

        for _ in range(MAX_GUESSES - len(self.guesses)):
            lines.append("_  _  _  _  _")
            lines.append("")

        lines.append(
            f"Attempts remaining: {MAX_GUESSES - len(self.guesses)}/{MAX_GUESSES}"
        )
        return "\n".join(lines)
