"""Interpretable time-aware activity predictions from observations."""

import math

try:
	from xgboost import XGBClassifier
except Exception:  # pragma: no cover - optional dependency
	XGBClassifier = None

try:
	from sklearn.ensemble import HistGradientBoostingClassifier
except Exception:  # pragma: no cover - optional dependency
	HistGradientBoostingClassifier = None


REQUIRED_KEYS = {"time", "band", "detected", "signal_strength"}


class TemporalModel:
	def __init__(self, num_bands, prior_probability=0.5, prior_strength=2, decay_rate=0.1,
				 lookahead_steps=3, min_training_samples=10):
		if num_bands <= 0:
			raise ValueError("num_bands must be > 0")
		if not 0 <= prior_probability <= 1:
			raise ValueError("prior_probability must be between 0 and 1")
		if prior_strength <= 0:
			raise ValueError("prior_strength must be > 0")
		if decay_rate < 0:
			raise ValueError("decay_rate must be >= 0")
		if lookahead_steps <= 0:
			raise ValueError("lookahead_steps must be > 0")
		if min_training_samples <= 0:
			raise ValueError("min_training_samples must be > 0")

		self.num_bands = num_bands
		self.prior_probability = prior_probability
		self.prior_strength = prior_strength
		self.decay_rate = decay_rate
		self.lookahead_steps = lookahead_steps
		self.min_training_samples = min_training_samples
		self._states = self._initial_states()
		self._history = {band_id: [] for band_id in range(self.num_bands)}
		self._max_seen_time = 0.0
		self._model = None
		self._trained = False

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

	def _append_history(self, band_id, observation):
		self._history.setdefault(band_id, []).append({
			"time": float(observation["time"]),
			"band": band_id,
			"detected": bool(observation["detected"]),
			"signal_strength": float(observation.get("signal_strength", 0.0) or 0.0),
		})
		self._max_seen_time = max(self._max_seen_time, float(observation["time"]))

	def _signal_strength_stats(self, band_history):
		strengths = [item["signal_strength"] for item in band_history if item["signal_strength"] is not None]
		if not strengths:
			return 0.0, 0.0
		return sum(strengths) / len(strengths), max(strengths)

	def _periodicity_features(self, band_history):
		hit_times = [item["time"] for item in band_history if item["detected"]]
		if len(hit_times) < 2:
			return 0.0, 0.0
		intervals = [later - earlier for earlier, later in zip(hit_times, hit_times[1:])]
		period = sum(intervals) / len(intervals)
		if not period:
			return 0.0, 0.0
		mean_offset = sum(abs(interval - period) for interval in intervals) / len(intervals)
		confidence = max(0.0, min(1.0, 1.0 - (mean_offset / max(period, 1.0))))
		return period, confidence

	def _feature_row(self, band_id, reference_time, band_history):
		if not band_history:
			return [0.5, 0.5, 0, 0, 0.0, 0.0, 0.5, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]

		recent_window = band_history[-min(len(band_history), 12):]
		recent_hits = sum(1 for item in recent_window if item["detected"])
		recent_total = len(recent_window)
		recent_hit_rate = recent_hits / recent_total if recent_total else 0.0
		recent_miss_rate = 1.0 - recent_hit_rate
		total_hits = sum(1 for item in band_history if item["detected"])
		total_misses = len(band_history) - total_hits
		activity_probability = total_hits / max(1, total_hits + total_misses)
		hit_times = [item["time"] for item in band_history if item["detected"]]
		time_since_last_hit = 0.0 if not hit_times else max(0.0, reference_time - hit_times[-1])
		time_since_last_scan = 0.0 if not band_history else max(0.0, reference_time - band_history[-1]["time"])
		signal_strength_recent = 0.0
		if recent_window:
			signal_strength_recent = sum(item["signal_strength"] for item in recent_window) / len(recent_window)
		signal_strength_mean, signal_strength_max = self._signal_strength_stats(band_history)
		period_estimate, periodicity_confidence = self._periodicity_features(band_history)
		recent_activity_trend = 0.0
		if len(recent_window) >= 2:
			recent_activity_trend = recent_hit_rate - (sum(1 for item in band_history[-2 * len(recent_window):-len(recent_window)] if item["detected"]) / max(1, len(recent_window)))
		time_position = 0.0 if self._max_seen_time <= 0 else reference_time / max(self._max_seen_time, 1.0)
		return [
			recent_hit_rate,
			recent_miss_rate,
			total_hits,
			total_misses,
			time_since_last_hit,
			time_since_last_scan,
			activity_probability,
			signal_strength_recent,
			signal_strength_mean,
			period_estimate,
			periodicity_confidence,
			recent_activity_trend,
			time_position,
		]

	def _build_training_data(self):
		features = []
		labels = []
		for band_id in range(self.num_bands):
			band_history = self._history.get(band_id, [])
			for index, current in enumerate(band_history[:-1]):
				future_window = band_history[index + 1: index + 1 + self.lookahead_steps]
				if not future_window:
					continue
				future_active = 1 if any(item["detected"] for item in future_window) else 0
				features.append(self._feature_row(band_id, current["time"], band_history[:index + 1]))
				labels.append(future_active)
		return features, labels

	def _train_model(self, features, labels):
		if len(features) < self.min_training_samples:
			self._model = None
			self._trained = False
			return False

		model = None
		if XGBClassifier is not None:
			model = XGBClassifier(
				n_estimators=200,
				max_depth=4,
				learning_rate=0.08,
				subsample=0.9,
				colsample_bytree=0.9,
				objective="binary:logistic",
				n_jobs=-1,
				random_state=0,
			)
		elif HistGradientBoostingClassifier is not None:
			model = HistGradientBoostingClassifier(
				max_depth=4,
				learning_rate=0.08,
				max_iter=200,
				random_state=0,
			)
		else:
			self._model = None
			self._trained = False
			return False

		model.fit(features, labels)
		self._model = model
		self._trained = True
		return True

	def train(self):
		"""Train a feature-based RF predictor from the accumulated observation history."""
		features, labels = self._build_training_data()
		return self._train_model(features, labels)

	def is_trained(self):
		return self._trained and self._model is not None

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

		self._append_history(band_id, observation)
		self.train()
		return dict(state)

	def predict(self, band_id, future_time):
		"""Estimate future activity using a trained RF feature model when possible."""
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
		heuristic_prediction = self.prior_probability + (
			smoothed_rate - self.prior_probability
		) * recency_weight
		heuristic_prediction = max(0.0, min(1.0, heuristic_prediction))

		if not self.is_trained():
			return heuristic_prediction

		band_history = self._history.get(band_id, [])
		if not band_history:
			return heuristic_prediction

		feature_row = self._feature_row(band_id, future_time, band_history)
		probability = self._model.predict_proba([feature_row])[0][1]
		blended = 0.7 * float(probability) + 0.3 * heuristic_prediction
		return max(0.0, min(1.0, blended))

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
		self._history = {band_id: [] for band_id in range(self.num_bands)}
		self._max_seen_time = 0.0
		self._model = None
		self._trained = False
