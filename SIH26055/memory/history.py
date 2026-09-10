"""Observation history: chronological record of receiver observations."""

REQUIRED_KEYS = {"time", "band", "detected", "signal_strength"}


class History:
    def __init__(self):
        self._records = []

    def add(self, observation):
        """Append a validated observation, preserving chronological (insertion) order."""
        if not isinstance(observation, dict) or not REQUIRED_KEYS.issubset(observation.keys()):
            raise ValueError(f"observation must contain keys {REQUIRED_KEYS}, got {observation}")

        self._records.append(dict(observation))

    def all(self):
        """Return every recorded observation, oldest first (copies; safe to mutate)."""
        return [dict(obs) for obs in self._records]

    def for_band(self, band_id):
        """Return only the observations that scanned a specific band."""
        return [dict(obs) for obs in self._records if obs["band"] == band_id]

    def recent(self, n):
        """Return the last n observations (fewer if history is shorter)."""
        if n <= 0:
            return []
        return [dict(obs) for obs in self._records[-n:]]

    def reset(self):
        """Clear all recorded observations."""
        self._records = []

    def __len__(self):
        return len(self._records)
