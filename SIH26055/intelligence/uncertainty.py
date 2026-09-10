"""Count-based uncertainty estimates derived from observations."""

import math


REQUIRED_KEYS = {"time", "band", "detected", "signal_strength"}


class UncertaintyEstimator:
	def __init__(self, num_bands):
		if num_bands <= 0:
			raise ValueError("num_bands must be > 0")

		self.num_bands = num_bands
		self._observations = {band_id: 0 for band_id in range(num_bands)}

	def _validate_band(self, band_id):
		if not isinstance(band_id, int) or not 0 <= band_id < self.num_bands:
			raise ValueError(f"band_id {band_id} out of range [0, {self.num_bands - 1}]")

	def update(self, observation):
		"""Count one valid observation as evidence, whether HIT or MISS."""
		if not isinstance(observation, dict) or not REQUIRED_KEYS.issubset(observation):
			raise ValueError(f"observation must contain keys {REQUIRED_KEYS}")
		band_id = observation["band"]
		self._validate_band(band_id)
		if not isinstance(observation["detected"], bool):
			raise ValueError("observation detected must be a bool")

		self._observations[band_id] += 1
		return self.get_band(band_id)

	def uncertainty(self, band_id):
		self._validate_band(band_id)
		return 1 / math.sqrt(self._observations[band_id] + 1)

	def confidence(self, band_id):
		return 1 - self.uncertainty(band_id)

	def get_band(self, band_id):
		self._validate_band(band_id)
		uncertainty = self.uncertainty(band_id)
		return {
			"band_id": band_id,
			"observations": self._observations[band_id],
			"uncertainty": uncertainty,
			"confidence": 1 - uncertainty,
		}

	def all(self):
		return {band_id: self.get_band(band_id) for band_id in range(self.num_bands)}

	def reset(self):
		self._observations = {band_id: 0 for band_id in range(self.num_bands)}
