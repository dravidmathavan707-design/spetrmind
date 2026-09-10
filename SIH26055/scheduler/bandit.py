"""UCB-style scheduler using supplied activity and uncertainty values."""


class BanditScheduler:
	def __init__(self, num_bands, exploration_weight=0.5):
		if num_bands <= 0:
			raise ValueError("num_bands must be > 0")
		if exploration_weight < 0:
			raise ValueError("exploration_weight must be >= 0")

		self.num_bands = num_bands
		self.exploration_weight = exploration_weight
		self.last_selected_band = None
		self.selection_count = 0

	def _validate_band(self, band_id):
		if not isinstance(band_id, int) or not 0 <= band_id < self.num_bands:
			raise ValueError(f"band_id {band_id} out of range [0, {self.num_bands - 1}]")

	def _get_values(self, band_id, states):
		if not isinstance(states, dict) or band_id not in states:
			raise ValueError(f"states is missing band {band_id}")

		state = states[band_id]
		if not isinstance(state, dict):
			raise ValueError(f"state for band {band_id} must be a dictionary")

		activity = state.get("activity_score")
		if activity is None:
			activity = state.get("hit_rate", state.get("activity_probability"))
		uncertainty = state.get("uncertainty")
		if not isinstance(activity, (int, float)) or not 0 <= activity <= 1:
			raise ValueError(f"invalid activity score for band {band_id}: {activity}")
		if not isinstance(uncertainty, (int, float)) or not 0 <= uncertainty <= 1:
			raise ValueError(f"invalid uncertainty for band {band_id}: {uncertainty}")
		return activity, uncertainty

	def score_band(self, band_id, states):
		"""Return UCB = activity score + weight * uncertainty."""
		self._validate_band(band_id)
		activity, uncertainty = self._get_values(band_id, states)
		return activity + self.exploration_weight * uncertainty

	def select_band(self, states):
		"""Select the lowest-ID band among those with the highest UCB score."""
		if not isinstance(states, dict):
			raise ValueError("states must be a dictionary keyed by band ID")
		for band_id in range(self.num_bands):
			self._get_values(band_id, states)

		selected_band = max(
			range(self.num_bands),
			key=lambda band_id: (self.score_band(band_id, states), -band_id),
		)
		self.last_selected_band = selected_band
		self.selection_count += 1
		return selected_band

	def reset(self):
		self.last_selected_band = None
		self.selection_count = 0
