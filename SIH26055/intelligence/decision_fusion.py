"""Configurable normalized fusion of cognitive scan-decision signals."""


SIGNALS = (
    "activity_score",
    "prediction_score",
    "periodicity_score",
    "uncertainty",
    "information_gain",
    "drift_score",
)


class DecisionFusion:
    def __init__(self, num_bands, weights=None):
        if num_bands <= 0:
            raise ValueError("num_bands must be > 0")

        default_weights = {
            "activity_score": 0.30,
            "prediction_score": 0.20,
            "periodicity_score": 0.15,
            "uncertainty": 0.15,
            "information_gain": 0.10,
            "drift_score": 0.10,
        }
        self.weights = dict(weights or default_weights)
        if set(self.weights) != set(SIGNALS):
            raise ValueError(f"weights must contain exactly {SIGNALS}")
        if any(not isinstance(value, (int, float)) or value < 0 for value in self.weights.values()):
            raise ValueError("weights must be non-negative numbers")
        if sum(self.weights.values()) == 0:
            raise ValueError("at least one weight must be positive")

        self.num_bands = num_bands
        self.last_selected_band = None
        self.selection_count = 0

    def _validate_state(self, band_id, state):
        if not isinstance(state, dict):
            raise ValueError(f"state for band {band_id} must be a dictionary")
        for signal in SIGNALS:
            value = state.get(signal)
            if not isinstance(value, (int, float)) or not 0 <= value <= 1:
                raise ValueError(f"{signal} for band {band_id} must be between 0 and 1")

    def score_band(self, band_id, state):
        if not isinstance(band_id, int) or not 0 <= band_id < self.num_bands:
            raise ValueError(f"band_id {band_id} out of range [0, {self.num_bands - 1}]")
        self._validate_state(band_id, state)
        weight_total = sum(self.weights.values())
        return sum(self.weights[signal] * state[signal] for signal in SIGNALS) / weight_total

    def select_band(self, states):
        """Select the lowest-ID band with the highest normalized fusion score."""
        if not isinstance(states, dict):
            raise ValueError("states must be a dictionary keyed by band ID")
        for band_id in range(self.num_bands):
            if band_id not in states:
                raise ValueError(f"states is missing band {band_id}")
            self._validate_state(band_id, states[band_id])

        selected_band = max(
            range(self.num_bands),
            key=lambda band_id: (self.score_band(band_id, states[band_id]), -band_id),
        )
        self.last_selected_band = selected_band
        self.selection_count += 1
        return selected_band

    def scores(self, states):
        return {band_id: self.score_band(band_id, state) for band_id, state in states.items()}

    def reset(self):
        self.last_selected_band = None
        self.selection_count = 0
