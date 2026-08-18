import random
import sys
from pathlib import Path
from game import MAX_GUESSES, WORD_LENGTH, Game
from history import GameHistory

WORDS_FILE = Path("words.txt")

def load_words(path=WORDS_FILE):
    if not path.exists():
        raise FileNotFoundError(f"Word list not found: '{path}'")
    seen = set()
    words = []
    for raw in path.read_text(encoding="utf-8").splitlines():
        word = raw.strip().lower()
        if not word:
            continue
        if len(word) != WORD_LENGTH or not word.isalpha():
            raise ValueError(f"Invalid word: '{raw.strip()}'")
        if word not in seen:
            seen.add(word)
            words.append(word)
    if len(words) < 50:
        raise ValueError(f"Word list must contain at least 50 valid words; found {len(words)}.")
    return words

def display_stats(history):
    print("\nStatistics")
    print("----------")
    print(f"Games:          {history.total_games}")
    print(f"Wins:           {history.total_wins}")
    print(f"Win percentage: {history.win_percentage:.1f}%")
    print(f"Current streak: {history.current_streak}")
    print(f"Best streak:    {history.best_streak}")

def run_game():
    try:
        word_list = load_words()
    except (FileNotFoundError, ValueError) as exc:
        print(f"Error loading word list: {exc}", file=sys.stderr)
        sys.exit(1)
    secret = random.choice(word_list)
    game = Game(secret, word_list)
    try:
        game_history = GameHistory()
    except Exception:
        game_history = GameHistory.__new__(GameHistory)
        game_history._file = Path("history.json")
        game_history._records = []
    print("\n" + str(game))
    while not game.is_over:
        try:
            raw_guess = input("\nEnter your guess: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nGame aborted.")
            sys.exit(0)
        try:
            game.make_guess(raw_guess)
        except Exception as exc:
            print(f"  [!] {exc}")
            continue
        print()
        print(str(game))
    if game.is_won:
        print(f"\nYou got it in {len(game.guesses)}/{MAX_GUESSES}!")
    else:
        print(f"\nThe word was {secret.upper()}.")
    game_history.record_game(won=game.is_won, attempts=len(game.guesses), word=secret)
    display_stats(game_history)

if __name__ == "__main__":
    run_game()
