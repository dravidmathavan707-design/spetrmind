"""Noise model for realistic synthetic receiver observations."""

import random


class NoiseModel:
	def __init__(self, noise_floor=-100.0, standard_deviation=0.0,
				 false_alarm_probability=0.0, seed=None):
		if standard_deviation < 0:
			raise ValueError("standard_deviation must be >= 0")
		if not 0 <= false_alarm_probability <= 1:
			raise ValueError("false_alarm_probability must be between 0 and 1")

		self.noise_floor = noise_floor
		self.standard_deviation = standard_deviation
		self.false_alarm_probability = false_alarm_probability
		self._rng = random.Random(seed)

	def sample(self, signal_strength=None):
		"""Return measured power for a signal or the noise floor when absent."""
		if signal_strength is None:
			measured_power = self._rng.gauss(
				self.noise_floor, self.standard_deviation
			)
			false_alarm = self._rng.random() < self.false_alarm_probability
			return measured_power, false_alarm

		measured_power = self._rng.gauss(
			signal_strength, self.standard_deviation
		)
		return measured_power, False
