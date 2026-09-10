"""Detect repeating activity intervals from observation timestamps."""


REQUIRED_KEYS = {"time", "band", "detected", "signal_strength"}


class PeriodicityDetector:
	def __init__(self, num_bands, minimum_hits=3, confidence_threshold=0.8):
		if num_bands <= 0:
			raise ValueError("num_bands must be > 0")
		if minimum_hits < 3:
			raise ValueError("minimum_hits must be >= 3")
		if not 0 <= confidence_threshold <= 1:
			raise ValueError("confidence_threshold must be between 0 and 1")

		self.num_bands = num_bands
		self.minimum_hits = minimum_hits
		self.confidence_threshold = confidence_threshold
		self._states = self._initial_states()

	def _initial_states(self):
		return {
			band_id: {
				"band_id": band_id,
				"hit_times": [],
				"intervals": [],
				"period": None,
				"confidence": 0.0,
				"periodic": False,
			}
			for band_id in range(self.num_bands)
		}

	def _validate_band(self, band_id):
		if not isinstance(band_id, int) or not 0 <= band_id < self.num_bands:
			raise ValueError(f"band_id {band_id} out of range [0, {self.num_bands - 1}]")

	def update(self, observation):
		"""Record a detected event and recompute that band's periodicity."""
		if not isinstance(observation, dict) or not REQUIRED_KEYS.issubset(observation):
			raise ValueError(f"observation must contain keys {REQUIRED_KEYS}")
		band_id = observation["band"]
		self._validate_band(band_id)
		if not isinstance(observation["detected"], bool):
			raise ValueError("observation detected must be a bool")
		if not isinstance(observation["time"], (int, float)):
			raise ValueError("observation time must be numeric")

		if observation["detected"]:
			state = self._states[band_id]
			hit_times = state["hit_times"]
			if hit_times and observation["time"] <= hit_times[-1]:
				raise ValueError("HIT timestamps must be strictly increasing per band")
			hit_times.append(observation["time"])
			self._recompute(state)

		return self.detect(band_id)

	def _recompute(self, state):
		hit_times = state["hit_times"]
		if len(hit_times) < self.minimum_hits:
			state["intervals"] = []
			state["period"] = None
			state["confidence"] = 0.0
			state["periodic"] = False
			return

		intervals = [later - earlier for earlier, later in zip(hit_times, hit_times[1:])]
		period = sum(intervals) / len(intervals)
		mean_deviation = sum(abs(interval - period) for interval in intervals) / len(intervals)
		confidence = max(0.0, min(1.0, 1.0 - mean_deviation / period))

		state["intervals"] = intervals
		state["period"] = period
		state["confidence"] = confidence
		state["periodic"] = confidence >= self.confidence_threshold

	def detect(self, band_id):
		self._validate_band(band_id)
		state = self._states[band_id]
		result = dict(state)
		result["hit_times"] = list(state["hit_times"])
		result["intervals"] = list(state["intervals"])
		return result

	def all(self):
		return {band_id: self.detect(band_id) for band_id in range(self.num_bands)}

	def reset(self):
		self._states = self._initial_states()
