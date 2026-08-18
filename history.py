import json
from pathlib import Path

HISTORY_FILE = Path("history.json")

class GameHistory:
    def __init__(self, history_file=HISTORY_FILE):
        self._file = history_file
        self._records = self._load()

    def _load(self):
        if not self._file.exists():
            self._file.write_text("[]", encoding="utf-8")
            return []
        try:
            data = json.loads(self._file.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise ValueError(f"Invalid JSON in {self._file}: {exc}") from exc
        if not isinstance(data, list):
            raise ValueError(f"History file {self._file} must contain a JSON array.")
        for entry in data:
            if not isinstance(entry, dict) or not {"won", "attempts", "word"}.issubset(entry):
                raise ValueError(f"Invalid history entry: {entry!r}")
        return data

    def _save(self):
        self._file.write_text(json.dumps(self._records, indent=2), encoding="utf-8")

    def record_game(self, won, attempts, word):
        self._records.append({"won": bool(won), "attempts": int(attempts), "word": str(word)})
        self._save()

    @property
    def total_games(self):
        return len(self._records)

    @property
    def total_wins(self):
        return sum(1 for r in self._records if r.get("won"))

    @property
    def win_percentage(self):
        if not self.total_games:
            return 0.0
        return (self.total_wins / self.total_games) * 100.0

    @property
    def current_streak(self):
        streak = 0
        for r in reversed(self._records):
            if r.get("won"):
                streak += 1
            else:
                break
        return streak

    @property
    def best_streak(self):
        best = 0
        cur = 0
        for r in self._records:
            if r.get("won"):
                cur += 1
                if cur > best:
                    best = cur
            else:
                cur = 0
        return best
