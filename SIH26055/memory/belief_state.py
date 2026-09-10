"""Observation-driven estimated activity beliefs for each frequency band."""


REQUIRED_KEYS = {"time", "band", "detected", "signal_strength"}


class BeliefState:
	def __init__(self, num_bands, prior_probability=0.5, prior_strength=2):
		if num_bands <= 0:
			raise ValueError("num_bands must be > 0")
		if not 0 <= prior_probability <= 1:
			raise ValueError("prior_probability must be between 0 and 1")
		if prior_strength <= 0:
			raise ValueError("prior_strength must be > 0")

		self.num_bands = num_bands
		self.prior_probability = prior_probability
		self.prior_strength = prior_strength
		self._states = self._initial_states()

	def _initial_states(self):
		return {
			band_id: {
				"band_id": band_id,
				"activity_probability": self.prior_probability,
				"scan_count": 0,
				"hit_count": 0,
				"miss_count": 0,
				"last_scan_time": None,
				"last_hit_time": None,
			}
			for band_id in range(self.num_bands)
		}

	def _validate_band(self, band_id):
		if not isinstance(band_id, int) or not 0 <= band_id < self.num_bands:
			raise ValueError(f"band_id {band_id} out of range [0, {self.num_bands - 1}]")

	def update(self, observation):
		"""Update one band from a receiver observation, without ground-truth access."""
		if not isinstance(observation, dict) or not REQUIRED_KEYS.issubset(observation):
			raise ValueError(f"observation must contain keys {REQUIRED_KEYS}")

		band_id = observation["band"]
		self._validate_band(band_id)
		if not isinstance(observation["detected"], bool):
			raise ValueError("observation detected must be a bool")

		state = self._states[band_id]
		state["scan_count"] += 1
		state["last_scan_time"] = observation["time"]

		if observation["detected"]:
			state["hit_count"] += 1
			state["last_hit_time"] = observation["time"]
		else:
			state["miss_count"] += 1

		state["activity_probability"] = (
			state["hit_count"] + self.prior_strength * self.prior_probability
		) / (state["scan_count"] + self.prior_strength)

	def get_band(self, band_id):
		self._validate_band(band_id)
		return dict(self._states[band_id])

	def probability(self, band_id):
		return self.get_band(band_id)["activity_probability"]

	def all(self):
		return {band_id: dict(state) for band_id, state in self._states.items()}

	def reset(self):
		self._states = self._initial_states()
