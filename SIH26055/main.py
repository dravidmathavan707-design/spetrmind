"""Run the complete SpectraMind cognitive scanning loop."""

from environment.scenarios import stable
from environment.noise import NoiseModel
from receiver.receiver import Receiver
from memory.history import History
from memory.belief_state import BeliefState
from learning.online_learning import OnlineLearning
from prediction.temporal_model import TemporalModel
from intelligence.periodicity import PeriodicityDetector
from intelligence.uncertainty import UncertaintyEstimator
from intelligence.information_gain import InformationGainEstimator
from intelligence.drift_detection import DriftDetector
from intelligence.decision_fusion import DecisionFusion
from scheduler.dwell_optimizer import DwellOptimizer
from evaluation.metrics import compute_metrics


def run_cognitive_loop(num_bands=20, steps=100, scenario_factory=stable,
					   receiver=None, exploration_weight=0.5,
					   min_dwell=10, max_dwell=100):
	"""Run one end-to-end experiment and return decisions, observations, metrics."""
	if num_bands <= 0:
		raise ValueError("num_bands must be > 0")
	if steps < 0:
		raise ValueError("steps must be >= 0")

	world = scenario_factory(num_bands=num_bands)
	receiver = receiver or Receiver()
	history = History()
	belief = BeliefState(num_bands)
	learning = OnlineLearning(num_bands)
	temporal = TemporalModel(num_bands)
	periodicity = PeriodicityDetector(num_bands)
	uncertainty = UncertaintyEstimator(num_bands)
	information_gain = InformationGainEstimator(num_bands)
	drift = DriftDetector(num_bands)
	fusion = DecisionFusion(num_bands, weights={
		"activity_score": 0.30,
		"prediction_score": 0.20,
		"periodicity_score": 0.15,
		"uncertainty": 0.15 * exploration_weight / 0.5 if exploration_weight else 0.0,
		"information_gain": 0.10,
		"drift_score": 0.10,
	})
	dwell = DwellOptimizer(min_dwell, max_dwell)

	observations = []
	decisions = []
	for time in range(steps):
		world.current_time = time - 1
		world.step(dt=1)

		learning_state = learning.all()
		temporal_predictions = temporal.all_predictions(time + 1)
		band_states = {}
		for band_id in range(num_bands):
			periodicity_state = periodicity.detect(band_id)
			drift_state = drift.detect(band_id)
			band_states[band_id] = {
				"activity_score": temporal_predictions[band_id],
				"prediction_score": temporal_predictions[band_id],
				"periodicity_score": periodicity_state["confidence"],
				"uncertainty": uncertainty.uncertainty(band_id),
				"drift_score": drift_state["drift_score"],
			}
			band_states[band_id]["information_gain"] = information_gain.information_gain(band_id)

		selected_band = fusion.select_band(band_states)
		selected_state = band_states[selected_band]
		dwell_time = dwell.dwell_for({
			"activity_score": selected_state["activity_score"],
			"uncertainty": selected_state["uncertainty"],
			"information_gain": selected_state["information_gain"],
		})

		actual_active, actual_strength = world.query_band(selected_band)
		observation = receiver.scan(selected_band, world)
		observation["actual_active"] = actual_active
		observation["actual_signal_strength"] = actual_strength
		observations.append(observation)

		learning_observation = {
			key: observation[key]
			for key in ("time", "band", "detected", "signal_strength")
		}
		history.add(learning_observation)
		belief.update(learning_observation)
		learning.update(learning_observation)
		temporal.update(learning_observation)
		periodicity.update(learning_observation)
		uncertainty.update(learning_observation)
		information_gain.update(learning_observation)
		drift.update(learning_observation)

		decisions.append({
			"time": observation["time"],
			"band": selected_band,
			"dwell": dwell_time,
			"activity_score": selected_state["activity_score"],
			"prediction_score": selected_state["prediction_score"],
			"periodicity_score": selected_state["periodicity_score"],
			"uncertainty": selected_state["uncertainty"],
			"information_gain": selected_state["information_gain"],
			"drift_score": selected_state["drift_score"],
			"drift": drift.detect(selected_band)["drift"],
		})

	return {
		"observations": observations,
		"decisions": decisions,
		"metrics": compute_metrics(observations),
		"history": history.all(),
		"belief": belief.all(),
		"learning": learning.all(),
		"predictions": temporal.all_predictions(steps),
		"periodicity": periodicity.all(),
		"uncertainty": uncertainty.all(),
		"information_gain": information_gain.all(),
		"drift": drift.all(),
	}


if __name__ == "__main__":
	result = run_cognitive_loop(steps=20)
	print("Cognitive loop complete")
	print(result["metrics"])
