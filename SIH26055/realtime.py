"""Stateful real-time scanning runtime built on the cognitive scan pipeline."""

from environment.scenarios import stable
from evaluation.metrics import compute_metrics
from intelligence.decision_fusion import DecisionFusion
from intelligence.drift_detection import DriftDetector
from intelligence.information_gain import InformationGainEstimator
from intelligence.periodicity import PeriodicityDetector
from intelligence.uncertainty import UncertaintyEstimator
from learning.online_learning import OnlineLearning
from memory.belief_state import BeliefState
from memory.history import History
from prediction.temporal_model import TemporalModel
from receiver.receiver import Receiver
from scheduler.dwell_optimizer import DwellOptimizer


class RealtimeScanner:
    """Keep scanner state alive and produce one telemetry event per scan."""

    def __init__(self, num_bands=20, scenario_factory=stable, receiver=None,
                 exploration_weight=0.5, min_dwell=10, max_dwell=100):
        if num_bands <= 0:
            raise ValueError("num_bands must be > 0")

        self.num_bands = num_bands
        self.scenario_factory = scenario_factory
        self.world = scenario_factory(num_bands=num_bands)
        self.receiver = receiver or Receiver()
        self.history = History()
        self.belief = BeliefState(num_bands)
        self.learning = OnlineLearning(num_bands)
        self.temporal = TemporalModel(num_bands)
        self.periodicity = PeriodicityDetector(num_bands)
        self.uncertainty = UncertaintyEstimator(num_bands)
        self.information_gain = InformationGainEstimator(num_bands)
        self.drift = DriftDetector(num_bands)
        self.fusion = DecisionFusion(num_bands, weights={
            "activity_score": 0.30,
            "prediction_score": 0.20,
            "periodicity_score": 0.15,
            "uncertainty": 0.15 * exploration_weight / 0.5 if exploration_weight else 0.0,
            "information_gain": 0.10,
            "drift_score": 0.10,
        })
        self.dwell = DwellOptimizer(min_dwell, max_dwell)
        self.step_number = 0
        self.observations = []
        self.requested_band = None

    def reset(self, scenario_factory=None):
        """Clear learned state and restart the RF world from time zero."""
        if scenario_factory is not None:
            self.scenario_factory = scenario_factory
        replacement = type(self)(
            num_bands=self.num_bands,
            scenario_factory=self.scenario_factory,
            receiver=self.receiver,
        )
        self.__dict__.update(replacement.__dict__)

    def request_band(self, band_id):
        """Set one valid band as the next scan target."""
        if not isinstance(band_id, int) or not 0 <= band_id < self.num_bands:
            raise ValueError("band_id must be a valid band index")
        self.requested_band = band_id

    def step(self):
        """Advance the simulated world and return the newest telemetry event."""
        self.world.current_time = self.step_number - 1
        self.world.step(dt=1)

        predictions = self.temporal.all_predictions(self.step_number + 1)
        band_states = {}
        for band_id in range(self.num_bands):
            periodicity_state = self.periodicity.detect(band_id)
            drift_state = self.drift.detect(band_id)
            band_states[band_id] = {
                "activity_score": predictions[band_id],
                "prediction_score": predictions[band_id],
                "periodicity_score": periodicity_state["confidence"],
                "uncertainty": self.uncertainty.uncertainty(band_id),
                "information_gain": self.information_gain.information_gain(band_id),
                "drift_score": drift_state["drift_score"],
            }

        selected_band = self.requested_band
        if selected_band is None:
            selected_band = self.fusion.select_band(band_states)
        self.requested_band = None
        selected_state = band_states[selected_band]
        dwell_time = self.dwell.dwell_for({
            "activity_score": selected_state["activity_score"],
            "uncertainty": selected_state["uncertainty"],
            "information_gain": selected_state["information_gain"],
        })

        actual_active, actual_strength = self.world.query_band(selected_band)
        observation = self.receiver.scan(selected_band, self.world)
        observation["actual_active"] = actual_active
        observation["actual_signal_strength"] = actual_strength
        self.observations.append(observation)

        learning_observation = {
            key: observation[key]
            for key in ("time", "band", "detected", "signal_strength")
        }
        self.history.add(learning_observation)
        self.belief.update(learning_observation)
        self.learning.update(learning_observation)
        self.temporal.update(learning_observation)
        self.periodicity.update(learning_observation)
        self.uncertainty.update(learning_observation)
        self.information_gain.update(learning_observation)
        self.drift.update(learning_observation)

        self.step_number += 1
        return {
            "time": observation["time"],
            "cycle": self.step_number,
            "process": {
                "stage": "model_update",
                "stage_index": 5,
                "total_stages": 5,
                "steps": [
                    {"key": "world", "label": "Advance RF world", "status": "complete"},
                    {"key": "score", "label": "Score candidate bands", "status": "complete"},
                    {"key": "tune", "label": "Tune receiver", "status": "complete"},
                    {"key": "measure", "label": "Measure selected frequency", "status": "complete"},
                    {"key": "model", "label": "Update learning model", "status": "active"},
                ],
            },
            "band": selected_band,
            "dwell": dwell_time,
            "detected": observation["detected"],
            "signal_strength": observation["signal_strength"],
            "actual_active": actual_active,
            "activity_score": selected_state["activity_score"],
            "prediction_score": selected_state["prediction_score"],
            "periodicity_score": selected_state["periodicity_score"],
            "uncertainty": selected_state["uncertainty"],
            "information_gain": selected_state["information_gain"],
            "drift_score": selected_state["drift_score"],
            "drift": self.drift.detect(selected_band)["drift"],
            "spectrum": self.belief.all(),
            "metrics": compute_metrics(self.observations),
        }