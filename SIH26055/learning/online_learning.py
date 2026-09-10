"""Interpretable online learning from receiver observations only."""


REQUIRED_KEYS = {"time", "band", "detected", "signal_strength"}


class OnlineLearning:
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
		self._model = self._initial_model()

	def _initial_model(self):
		return {
			band_id: {
				"band_id": band_id,
				"observations": 0,
				"hits": 0,
				"misses": 0,
				"hit_rate": self.prior_probability,
			}
			for band_id in range(self.num_bands)
		}

	def _validate_band(self, band_id):
		if not isinstance(band_id, int) or not 0 <= band_id < self.num_bands:
			raise ValueError(f"band_id {band_id} out of range [0, {self.num_bands - 1}]")

	def update(self, observation):
		"""Update one band using a single receiver observation."""
		if not isinstance(observation, dict) or not REQUIRED_KEYS.issubset(observation):
			raise ValueError(f"observation must contain keys {REQUIRED_KEYS}")

		band_id = observation["band"]
		self._validate_band(band_id)
		if not isinstance(observation["detected"], bool):
			raise ValueError("observation detected must be a bool")

		state = self._model[band_id]
		state["observations"] += 1
		if observation["detected"]:
			state["hits"] += 1
		else:
			state["misses"] += 1

		state["hit_rate"] = (
			state["hits"] + self.prior_strength * self.prior_probability
		) / (state["observations"] + self.prior_strength)

		return dict(state)

	def get_band(self, band_id):
		self._validate_band(band_id)
		return dict(self._model[band_id])

	def score(self, band_id):
		return self.get_band(band_id)["hit_rate"]

	def all(self):
		return {band_id: dict(state) for band_id, state in self._model.items()}

	def reset(self):
		self._model = self._initial_model()
