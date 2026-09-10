"""Fixed scheduler: non-intelligent open-loop sequential scan (baseline)."""


class FixedScheduler:
    def __init__(self, num_bands):
        if num_bands <= 0:
            raise ValueError("num_bands must be > 0")

        self.num_bands = num_bands
        self.current_index = 0

    def next_band(self):
        """Return the next band in sequence, wrapping around after num_bands - 1."""
        band = self.current_index
        self.current_index = (self.current_index + 1) % self.num_bands
        return band

    def reset(self):
        """Restart the sequence from band 0."""
        self.current_index = 0
