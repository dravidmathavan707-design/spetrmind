"""Estimate the value of obtaining one more observation per band."""

import math


REQUIRED_KEYS = {"time", "band", "detected", "signal_strength"}


class InformationGainEstimator:
	"""Use gain = count uncertainty * normalized Bernoulli entropy.

	Count uncertainty is 1 / sqrt(observations + 1), and entropy is based on
	the smoothed HIT rate. The resulting potential gain is bounded by [0, 1].
	"""

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
		self._evidence = self._initial_evidence()

	def _initial_evidence(self):
		return {band_id: {"observations": 0, "hits": 0, "misses": 0}
				for band_id in range(self.num_bands)}

	def _validate_band(self, band_id):
		if not isinstance(band_id, int) or not 0 <= band_id < self.num_bands:
			raise ValueError(f"band_id {band_id} out of range [0, {self.num_bands - 1}]")

	def update(self, observation):
		"""Add one HIT or MISS as evidence about its scanned band."""
		if not isinstance(observation, dict) or not REQUIRED_KEYS.issubset(observation):
			raise ValueError(f"observation must contain keys {REQUIRED_KEYS}")
		band_id = observation["band"]
		self._validate_band(band_id)
		if not isinstance(observation["detected"], bool):
			raise ValueError("observation detected must be a bool")

		evidence = self._evidence[band_id]
		evidence["observations"] += 1
		evidence["hits"] += int(observation["detected"])
		evidence["misses"] += int(not observation["detected"])
		return self.get_band(band_id)

	def _probability(self, evidence):
		return (
			evidence["hits"] + self.prior_strength * self.prior_probability
		) / (evidence["observations"] + self.prior_strength)

	def information_gain(self, band_id):
		self._validate_band(band_id)
		evidence = self._evidence[band_id]
		probability = self._probability(evidence)
		entropy = 0.0
		for value in (probability, 1 - probability):
			if value > 0:
				entropy -= value * math.log2(value)
		count_uncertainty = 1 / math.sqrt(evidence["observations"] + 1)
		return count_uncertainty * entropy

	def get_band(self, band_id):
		self._validate_band(band_id)
		evidence = self._evidence[band_id]
		return {
			"band_id": band_id,
			"observations": evidence["observations"],
			"hits": evidence["hits"],
			"misses": evidence["misses"],
			"estimated_activity": self._probability(evidence),
			"information_gain": self.information_gain(band_id),
		}

	def all(self):
		return {band_id: self.get_band(band_id) for band_id in range(self.num_bands)}

	def reset(self):
		self._evidence = self._initial_evidence()
