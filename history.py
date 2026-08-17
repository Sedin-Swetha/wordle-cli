"""Persistence layer for Wordle game history."""
import json
from pathlib import Path
HISTORY_FILE = Path("history.json")
class GameHistory:
    """Persists completed Wordle games and computes player statistics.
    Each game is stored as a JSON object with the keys ``won``, ``attempts``,
    and ``word``. Statistics are computed on demand from the full record list.
    Attributes:
        total_games: Total number of completed games.
        total_wins: Total number of won games.
        win_percentage: Percentage of games won (0.0 to 100.0).
        current_streak: Consecutive wins ending at the most recent game.
        best_streak: Longest consecutive win streak across all games.
    """
    def __init__(self, history_file: Path = HISTORY_FILE) -> None:
        self._file = history_file
        self._records: list[dict[str, object]] = self._load()
    def _load(self) -> list[dict[str, object]]:
        if not self._file.exists():
            self._file.write_text("[]", encoding="utf-8")
            return []
        raw = self._file.read_text(encoding="utf-8")
        try:
            data = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise ValueError(
                f"History file '{self._file}' contains invalid JSON: {exc}"
            ) from exc
        if not isinstance(data, list):
            raise ValueError(
                f"History file '{self._file}' must contain a JSON array."
            )
        for entry in data:
            if not isinstance(entry, dict) or not {
                "won", "attempts", "word"
            }.issubset(entry):
                raise ValueError(
                    f"History file '{self._file}' contains an invalid entry: "
                    f"{entry!r}"
                )
        return data  # type: ignore[return-value]
    def _save(self) -> None:
        self._file.write_text(
            json.dumps(self._records, indent=2), encoding="utf-8"
        )
    def record_game(self, won: bool, attempts: int, word: str) -> None:
        """Append a completed game to the history and persist to disk.
        Args:
            won: Whether the player won the game.
            attempts: Number of valid guesses made.
            word: The secret word for this game.
        """
        self._records.append({"won": won, "attempts": attempts, "word": word})
        self._save()
    @property
    def total_games(self) -> int:
        """Total number of completed games."""
        return len(self._records)
    @property
    def total_wins(self) -> int:
        """Total number of won games."""
        return sum(1 for r in self._records if r["won"])
    @property
    def win_percentage(self) -> float:
        """Win percentage in the range [0.0, 100.0]. Returns 0.0 if no games."""
        if self.total_games == 0:
            return 0.0
        return (self.total_wins / self.total_games) * 100.0
    @property
    def current_streak(self) -> int:
        """Consecutive wins ending at the most recent game.
        Iterates records in reverse and counts wins until a loss is found.
        """
        streak = 0
        for record in reversed(self._records):
            if record["won"]:
                streak += 1
            else:
                break
        return streak
    @property
    def best_streak(self) -> int:
        """Longest consecutive win streak across all recorded games."""
        best = 0
        current = 0
        for record in self._records:
            if record["won"]:
                current += 1
                best = max(best, current)
            else:
                current = 0
        return best
