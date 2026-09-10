"""Interpretable time-aware activity predictions from observations."""

import math


REQUIRED_KEYS = {"time", "band", "detected", "signal_strength"}


class TemporalModel:
	def __init__(self, num_bands, prior_probability=0.5, prior_strength=2, decay_rate=0.1):
		if num_bands <= 0:
			raise ValueError("num_bands must be > 0")
		if not 0 <= prior_probability <= 1:
			raise ValueError("prior_probability must be between 0 and 1")
		if prior_strength <= 0:
			raise ValueError("prior_strength must be > 0")
		if decay_rate < 0:
			raise ValueError("decay_rate must be >= 0")

		self.num_bands = num_bands
		self.prior_probability = prior_probability
		self.prior_strength = prior_strength
		self.decay_rate = decay_rate
		self._states = self._initial_states()

	def _initial_states(self):
		return {
			band_id: {
				"band_id": band_id,
				"observations": 0,
				"hits": 0,
				"misses": 0,
				"last_observation_time": None,
				"last_hit_time": None,
			}
			for band_id in range(self.num_bands)
		}

	def _validate_band(self, band_id):
		if not isinstance(band_id, int) or not 0 <= band_id < self.num_bands:
			raise ValueError(f"band_id {band_id} out of range [0, {self.num_bands - 1}]")

	def update(self, observation):
		"""Learn from one observation and return the updated temporal state."""
		if not isinstance(observation, dict) or not REQUIRED_KEYS.issubset(observation):
			raise ValueError(f"observation must contain keys {REQUIRED_KEYS}")

		band_id = observation["band"]
		self._validate_band(band_id)
		if not isinstance(observation["detected"], bool):
			raise ValueError("observation detected must be a bool")
		if not isinstance(observation["time"], (int, float)):
			raise ValueError("observation time must be numeric")

		state = self._states[band_id]
		state["observations"] += 1
		state["last_observation_time"] = observation["time"]
		if observation["detected"]:
			state["hits"] += 1
			state["last_hit_time"] = observation["time"]
		else:
			state["misses"] += 1

		return dict(state)

	def predict(self, band_id, future_time):
		"""Estimate activity at future_time using smoothed tendency and recency decay."""
		self._validate_band(band_id)
		if not isinstance(future_time, (int, float)):
			raise ValueError("future_time must be numeric")

		state = self._states[band_id]
		observations = state["observations"]
		if observations == 0:
			return self.prior_probability

		smoothed_rate = (
			state["hits"] + self.prior_strength * self.prior_probability
		) / (observations + self.prior_strength)
		elapsed = max(0.0, future_time - state["last_observation_time"])
		recency_weight = math.exp(-self.decay_rate * elapsed)
		prediction = self.prior_probability + (
			smoothed_rate - self.prior_probability
		) * recency_weight
		return max(0.0, min(1.0, prediction))

	def all_predictions(self, future_time):
		return {
			band_id: self.predict(band_id, future_time)
			for band_id in range(self.num_bands)
		}

	def get_band(self, band_id):
		self._validate_band(band_id)
		return dict(self._states[band_id])

	def reset(self):
		self._states = self._initial_states()
