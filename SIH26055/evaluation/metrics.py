"""Scheduler-agnostic metrics: computed from a list of receiver observations."""


def compute_metrics(observations):
    """Compute metrics from receiver observations and optional evaluation truth.

    The optional ``actual_active`` field is evaluation-only ground truth. It is
    never part of the observation passed to learning or scheduling components.
    """
    total_scans = len(observations)
    hits = sum(1 for obs in observations if obs["detected"])
    misses = total_scans - hits

    detection_rate = hits / total_scans if total_scans > 0 else 0.0
    has_truth = all("actual_active" in obs for obs in observations)
    active_opportunities = sum(
        1 for obs in observations if obs.get("actual_active", False)
    )
    true_detections = sum(
        1 for obs in observations
        if obs.get("actual_active", False) and obs["detected"]
    )
    inactive_scans = total_scans - active_opportunities
    false_alarms = sum(
        1 for obs in observations
        if not obs.get("actual_active", False) and obs["detected"]
    )

    first_detection_time = None
    for obs in observations:
        if obs["detected"]:
            first_detection_time = obs["time"]
            break

    prediction_pairs = [
        (obs["predicted_activity"], obs["actual_active"])
        for obs in observations
        if "predicted_activity" in obs and "actual_active" in obs
    ]
    prediction_accuracy = None
    if prediction_pairs:
        prediction_accuracy = sum(
            (prediction >= 0.5) == actual
            for prediction, actual in prediction_pairs
        ) / len(prediction_pairs)

    first_true_detection_time = None
    if has_truth:
        first_true_detection_time = next(
            (obs["time"] for obs in observations
             if obs.get("actual_active") and obs["detected"]),
            None,
        )
    reward = true_detections - false_alarms - (0.01 * total_scans)

    return {
        "total_scans": total_scans,
        "hits": hits,
        "misses": misses,
        "detection_rate": detection_rate,
        "first_detection_time": first_detection_time,
        "probability_of_detection": (
            true_detections / active_opportunities
            if active_opportunities else None
        ),
        "false_alarm_probability": (
            false_alarms / inactive_scans if inactive_scans else None
        ),
        "sensitivity": (
            true_detections / active_opportunities
            if active_opportunities else None
        ),
        "average_intercept_rate": (
            true_detections / active_opportunities
            if active_opportunities else 0.0
        ),
        "average_reward_cost": reward,
        "first_true_detection_time": first_true_detection_time,
        "average_intercept_time": first_true_detection_time,
        "average_intercept_time_error": None,
        "prediction_accuracy": prediction_accuracy,
    }
