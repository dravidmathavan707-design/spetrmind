"""Smart Scheduler v1: select the highest supplied learned activity score."""


class SmartScheduler:
	def __init__(self, num_bands):
		if num_bands <= 0:
			raise ValueError("num_bands must be > 0")

		self.num_bands = num_bands
		self.last_selected_band = None
		self.selection_count = 0

	def select_band(self, learning_state):
		"""Select the lowest-ID band among those with the highest learned score."""
		if not isinstance(learning_state, dict):
			raise ValueError("learning_state must be a dictionary keyed by band ID")

		scores = {}
		for band_id in range(self.num_bands):
			if band_id not in learning_state:
				raise ValueError(f"learning_state is missing band {band_id}")

			state = learning_state[band_id]
			if isinstance(state, dict):
				score = state.get("hit_rate")
				if score is None:
					score = state.get("activity_probability")
			else:
				score = state

			if not isinstance(score, (int, float)) or not 0 <= score <= 1:
				raise ValueError(f"invalid learned score for band {band_id}: {score}")
			scores[band_id] = score

		selected_band = min(scores, key=lambda band_id: (-scores[band_id], band_id))
		self.last_selected_band = selected_band
		self.selection_count += 1
		return selected_band

	def reset(self):
		"""Clear decision bookkeeping; the next selection uses supplied state afresh."""
		self.last_selected_band = None
		self.selection_count = 0
