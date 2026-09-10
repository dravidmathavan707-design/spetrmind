"""Window-based detection of changing observation behavior."""


REQUIRED_KEYS = {"time", "band", "detected", "signal_strength"}


class DriftDetector:
	def __init__(self, num_bands, reference_window=5, recent_window=5,
				 threshold=0.5):
		if num_bands <= 0:
			raise ValueError("num_bands must be > 0")
		if reference_window <= 0 or recent_window <= 0:
			raise ValueError("window sizes must be > 0")
		if not 0 <= threshold <= 1:
			raise ValueError("threshold must be between 0 and 1")

		self.num_bands = num_bands
		self.reference_window = reference_window
		self.recent_window = recent_window
		self.threshold = threshold
		self._observations = {band_id: [] for band_id in range(num_bands)}

	def _validate_band(self, band_id):
		if not isinstance(band_id, int) or not 0 <= band_id < self.num_bands:
			raise ValueError(f"band_id {band_id} out of range [0, {self.num_bands - 1}]")

	def update(self, observation):
		"""Append one HIT/MISS and return the current drift state for its band."""
		if not isinstance(observation, dict) or not REQUIRED_KEYS.issubset(observation):
			raise ValueError(f"observation must contain keys {REQUIRED_KEYS}")
		band_id = observation["band"]
		self._validate_band(band_id)
		if not isinstance(observation["detected"], bool):
			raise ValueError("observation detected must be a bool")

		self._observations[band_id].append(observation["detected"])
		return self.detect(band_id)

	def detect(self, band_id):
		self._validate_band(band_id)
		values = self._observations[band_id]
		required = self.reference_window + self.recent_window
		if len(values) < required:
			return {
				"band_id": band_id,
				"observations": len(values),
				"reference_rate": None,
				"recent_rate": None,
				"drift_score": 0.0,
				"confidence": 0.0,
				"drift": False,
			}

		reference = values[-required:-self.recent_window]
		recent = values[-self.recent_window:]
		reference_rate = sum(reference) / len(reference)
		recent_rate = sum(recent) / len(recent)
		drift_score = abs(recent_rate - reference_rate)
		confidence = len(values) / (len(values) + required)
		return {
			"band_id": band_id,
			"observations": len(values),
			"reference_rate": reference_rate,
			"recent_rate": recent_rate,
			"drift_score": drift_score,
			"confidence": confidence,
			"drift": drift_score >= self.threshold,
		}

	def all(self):
		return {band_id: self.detect(band_id) for band_id in range(self.num_bands)}

	def reset(self):
		self._observations = {band_id: [] for band_id in range(self.num_bands)}
