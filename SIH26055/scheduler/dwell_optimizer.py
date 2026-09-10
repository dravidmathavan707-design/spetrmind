"""Adaptive dwell-time calculation independent of band-selection logic."""


class DwellOptimizer:
	def __init__(self, min_dwell, max_dwell):
		if min_dwell < 0:
			raise ValueError("min_dwell must be >= 0")
		if max_dwell <= 0:
			raise ValueError("max_dwell must be > 0")
		if min_dwell > max_dwell:
			raise ValueError("min_dwell must be <= max_dwell")

		self.min_dwell = min_dwell
		self.max_dwell = max_dwell
		self._last_dwell = None

	def _validate_value(self, name, value):
		if not isinstance(value, (int, float)) or not 0 <= value <= 1:
			raise ValueError(f"{name} must be between 0 and 1")

	def calculate_dwell(self, activity_score, uncertainty, information_gain):
		"""Map information gain linearly to [min_dwell, max_dwell]."""
		self._validate_value("activity_score", activity_score)
		self._validate_value("uncertainty", uncertainty)
		self._validate_value("information_gain", information_gain)

		dwell = self.min_dwell + (
			information_gain * (self.max_dwell - self.min_dwell)
		)
		self._last_dwell = dwell
		return dwell

	def dwell_for(self, state):
		"""Calculate dwell from a supplied state dictionary without choosing a band."""
		if not isinstance(state, dict):
			raise ValueError("state must be a dictionary")
		try:
			return self.calculate_dwell(
				state["activity_score"],
				state["uncertainty"],
				state["information_gain"],
			)
		except KeyError as error:
			raise ValueError(f"state is missing {error.args[0]}") from error

	def reset(self):
		self._last_dwell = None

	@property
	def last_dwell(self):
		return self._last_dwell
