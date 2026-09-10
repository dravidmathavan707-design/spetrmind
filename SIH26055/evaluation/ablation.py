"""Evaluation-only ablation study for the integrated cognitive scheduler."""

from environment.scenarios import stable
from environment.rf_world import RFWorld
from evaluation.metrics import compute_metrics
from intelligence.drift_detection import DriftDetector
from intelligence.information_gain import InformationGainEstimator
from intelligence.periodicity import PeriodicityDetector
from intelligence.uncertainty import UncertaintyEstimator
from learning.online_learning import OnlineLearning
from prediction.temporal_model import TemporalModel
from receiver.receiver import Receiver
from scheduler.bandit import BanditScheduler
from scheduler.dwell_optimizer import DwellOptimizer


VARIANTS = (
    "full",
    "without_ucb_exploration",
    "without_temporal_prediction",
    "without_periodicity",
    "without_uncertainty",
    "without_information_gain",
    "without_drift_detection",
    "without_adaptive_dwell",
)


def _validate_variant(variant):
    if variant not in VARIANTS:
        raise ValueError(f"unknown ablation variant: {variant}")


def run_ablation_variant(variant="full", num_bands=20, steps=100,
                         scenario_factory=stable, exploration_weight=0.5,
                         min_dwell=10, max_dwell=100):
    """Run one variant with identical loop timing and a fresh scenario world."""
    _validate_variant(variant)
    if num_bands <= 0 or steps < 0:
        raise ValueError("num_bands must be > 0 and steps must be >= 0")

    world = scenario_factory(num_bands=num_bands)
    receiver = Receiver()
    learning = OnlineLearning(num_bands)
    temporal = TemporalModel(num_bands)
    periodicity = PeriodicityDetector(num_bands)
    uncertainty = UncertaintyEstimator(num_bands)
    information_gain = InformationGainEstimator(num_bands)
    drift = DriftDetector(num_bands)
    bandit = BanditScheduler(
        num_bands,
        exploration_weight=0 if variant == "without_ucb_exploration" else exploration_weight,
    )
    dwell_optimizer = DwellOptimizer(min_dwell, max_dwell)
    observations = []
    decisions = []

    for time in range(steps):
        world.current_time = time - 1
        world.step(dt=1)
        learning_state = learning.all()
        predictions = temporal.all_predictions(time + 1)
        states = {}
        for band_id in range(num_bands):
            activity = (
                learning_state[band_id]["hit_rate"]
                if variant == "without_temporal_prediction"
                else predictions[band_id]
            )
            states[band_id] = {
                "activity_score": activity,
                "uncertainty": (
                    0.0
                    if variant == "without_uncertainty"
                    else uncertainty.uncertainty(band_id)
                ),
                "information_gain": (
                    0.0
                    if variant == "without_information_gain"
                    else information_gain.information_gain(band_id)
                ),
            }

        selected_band = bandit.select_band(states)
        selected_state = states[selected_band]
        selected_dwell = (
            min_dwell
            if variant == "without_adaptive_dwell"
            else dwell_optimizer.dwell_for(selected_state)
        )
        actual_active, actual_strength = world.query_band(selected_band)
        observation = receiver.scan(selected_band, world)
        observation["actual_active"] = actual_active
        observation["actual_signal_strength"] = actual_strength
        observations.append(observation)
        learning_observation = {
            key: observation[key]
            for key in ("time", "band", "detected", "signal_strength")
        }

        learning.update(learning_observation)
        temporal.update(learning_observation)
        uncertainty.update(learning_observation)
        information_gain.update(learning_observation)
        if variant != "without_periodicity":
            periodicity.update(learning_observation)
        if variant != "without_drift_detection":
            drift.update(learning_observation)
        decisions.append({
            "time": observation["time"],
            "band": selected_band,
            "dwell": selected_dwell,
            "activity_score": selected_state["activity_score"],
            "uncertainty": selected_state["uncertainty"],
            "information_gain": selected_state["information_gain"],
        })

    return {
        "variant": variant,
        "observations": observations,
        "decisions": decisions,
        "metrics": compute_metrics(observations),
    }


def run_ablation_study(num_bands=20, steps=100, scenario_factory=stable,
                       variants=VARIANTS):
    """Run every requested variant under identical scenario and timing settings."""
    unknown = set(variants) - set(VARIANTS)
    if unknown:
        raise ValueError(f"unknown ablation variants: {sorted(unknown)}")
    return {
        variant: run_ablation_variant(
            variant=variant,
            num_bands=num_bands,
            steps=steps,
            scenario_factory=scenario_factory,
        )
        for variant in variants
    }


def summarize_ablation(results):
    """Return comparable core metrics for an ablation result mapping."""
    return {
        variant: {
            "detection_rate": result["metrics"]["detection_rate"],
            "hits": result["metrics"]["hits"],
            "misses": result["metrics"]["misses"],
            "total_scans": result["metrics"]["total_scans"],
        }
        for variant, result in results.items()
    }
