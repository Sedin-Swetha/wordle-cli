"""CLI entry point for the Wordle game."""
import random
import sys
from pathlib import Path
from game import MAX_GUESSES, WORD_LENGTH, Game
from history import GameHistory
WORDS_FILE = Path("words.txt")
def load_words(path: Path = WORDS_FILE) -> list[str]:
    """Load and validate the word list from *path*.
    Each word must be exactly WORD_LENGTH lowercase alphabetic characters.
    Duplicates are removed while preserving the first occurrence.
    Args:
        path: Path to the plain-text word file, one word per line.
    Returns:
        A deduplicated list of valid five-letter words.
    Raises:
        FileNotFoundError: If the file does not exist.
        ValueError: If any word is invalid or fewer than 50 words are found.
    """
    if not path.exists():
        raise FileNotFoundError(f"Word list not found: '{path}'")
    seen: set[str] = set()
    words: list[str] = []
    for lineno, raw in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        word = raw.strip().lower()
        if not word:
            continue
        if len(word) != WORD_LENGTH or not word.isalpha():
            raise ValueError(
                f"Invalid word on line {lineno}: '{raw.strip()}'. "
                f"Words must be exactly {WORD_LENGTH} alphabetic characters."
            )
        if word not in seen:
            seen.add(word)
            words.append(word)
    if len(words) < 50:
        raise ValueError(
            f"Word list must contain at least 50 valid words; found {len(words)}."
        )
    return words
def display_stats(history: GameHistory) -> None:
    """Print end-of-game statistics to stdout.
    Args:
        history: The GameHistory instance to read from.
    """
    print("\nStatistics")
    print("----------")
    print(f"Games:          {history.total_games}")
    print(f"Wins:           {history.total_wins}")
    print(f"Win percentage: {history.win_percentage:.1f}%")
    print(f"Current streak: {history.current_streak}")
    print(f"Best streak:    {history.best_streak}")
def run_game() -> None:
    """Load words, run an interactive Wordle game, and persist the result."""
    if sys.stdout.encoding and sys.stdout.encoding.lower() not in ("utf-8", "utf-16"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")  # type: ignore[union-attr]
    try:
        word_list = load_words()
    except (FileNotFoundError, ValueError) as exc:
        print(f"Error loading word list: {exc}", file=sys.stderr)
        sys.exit(1)
    secret = random.choice(word_list)
    game = Game(secret, word_list)
    try:
        game_history = GameHistory()
    except ValueError as exc:
        print(f"Warning: could not load history: {exc}", file=sys.stderr)
        game_history = GameHistory.__new__(GameHistory)
        game_history._file = Path("history.json")  # noqa: SLF001
        game_history._records = []  # noqa: SLF001
    print("\n" + str(game))
    while not game.is_over:
        try:
            raw_guess = input("\nEnter your guess: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nGame aborted.")
            sys.exit(0)
        try:
            game.make_guess(raw_guess)
        except ValueError as exc:
            print(f"  [!] {exc}")
            continue
        except RuntimeError as exc:
            print(f"  [!] {exc}")
            break
        print()
        print(str(game))
    if game.is_won:
        print(f"\nYou got it in {len(game.guesses)}/{MAX_GUESSES}!")
    else:
        print(f"\nThe word was {secret.upper()}.")
    game_history.record_game(
        won=game.is_won,
        attempts=len(game.guesses),
        word=secret,
    )
    display_stats(game_history)
if __name__ == "__main__":
    run_game()
