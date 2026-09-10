"""Emitter model: a signal source that turns on/off inside the simulated RF world."""


class Emitter:
    def __init__(self, band_id, signal_strength, start_time, duration):
        self.band_id = band_id
        self.signal_strength = signal_strength
        self.start_time = start_time
        self.duration = duration
        self.active = False

    def update(self, current_time):
        """Recompute active state for the given simulation time."""
        end_time = self.start_time + self.duration
        self.active = self.start_time <= current_time < end_time
        return self.active

    def __repr__(self):
        return (
            f"Emitter(band={self.band_id}, active={self.active}, "
            f"strength={self.signal_strength}, "
            f"window=[{self.start_time}, {self.start_time + self.duration}))"
        )
