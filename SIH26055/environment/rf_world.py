"""Synthetic RF world: holds ground-truth emitter state for every band over time."""

from environment.emitter import Emitter


class RFWorld:
    def __init__(self, num_bands=20):
        self.num_bands = num_bands
        self.emitters = []
        self.current_time = 0.0
        self.band_state = [False] * num_bands
        self.band_signal_strength = [None] * num_bands

    def add_emitter(self, emitter: Emitter):
        self.emitters.append(emitter)

    def step(self, dt=1.0):
        """Advance simulation time and recompute ground-truth band activity."""
        self.current_time += dt
        self.band_state = [False] * self.num_bands
        self.band_signal_strength = [None] * self.num_bands

        for emitter in self.emitters:
            is_active = emitter.update(self.current_time)
            if is_active:
                self.band_state[emitter.band_id] = True
                self.band_signal_strength[emitter.band_id] = emitter.signal_strength

        return self.band_state

    def query_band(self, band_id):
        """Restricted interface: report truth for ONE band only (used by the receiver)."""
        active = self.band_state[band_id]
        strength = self.band_signal_strength[band_id]
        return active, strength

    def get_ground_truth(self):
        """Return the current true ON/OFF state for every band (test/debug use only)."""
        return list(self.band_state)
