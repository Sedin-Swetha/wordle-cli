from collections import Counter
from enum import Enum

WORD_LENGTH = 5
MAX_GUESSES = 6


class LetterResult(Enum):
    CORRECT = "correct"
    PRESENT = "present"
    ABSENT = "absent"


class GuessResult:
    def __init__(self, word, results):
        self.word = word
        self.results = results

    def __str__(self):
        symbol_map = {
            LetterResult.CORRECT: "✓",
            LetterResult.PRESENT: "~",
            LetterResult.ABSENT: "✗",
        }
        letters_row = "  ".join(ch.upper() for ch in self.word)
        symbols_row = "  ".join(symbol_map[r] for r in self.results)
        return f"{letters_row}\n{symbols_row}"


def evaluate_guess(secret, guess):
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
    def __init__(self, secret, word_list):
        self.secret = secret
        self.word_list = word_list
        self.guesses = []

    @property
    def is_won(self):
        return bool(self.guesses) and self.guesses[-1].word == self.secret

    @property
    def is_over(self):
        return self.is_won or len(self.guesses) >= MAX_GUESSES

    def make_guess(self, word):
        if self.is_over:
            raise RuntimeError("The game is already over.")
        normalised = word.strip().lower()
        if len(normalised) != WORD_LENGTH:
            raise ValueError(f"Guess must be exactly {WORD_LENGTH} characters, got {len(normalised)}.")
        if normalised not in self.word_list:
            raise ValueError(f"'{normalised}' is not in the word list.")
        result = evaluate_guess(self.secret, normalised)
        self.guesses.append(result)
        return result

    def __str__(self):
        lines = ["WORDLE", "=========", ""]
        for guess_result in self.guesses:
            lines.append(str(guess_result))
            lines.append("")
        for _ in range(MAX_GUESSES - len(self.guesses)):
            lines.append("_  _  _  _  _")
            lines.append("")
        lines.append(f"Attempts remaining: {MAX_GUESSES - len(self.guesses)}/{MAX_GUESSES}")
        return "\n".join(lines)
