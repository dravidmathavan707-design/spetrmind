"""Feature engineering for RF temporal prediction using only history available up to time t."""

from __future__ import annotations


def _safe_divide(numerator, denominator):
    if denominator == 0:
        return 0.0
    return float(numerator) / float(denominator)


def _window_history(history, window_size):
    if not history:
        return []
    return history[-window_size:]


def build_feature_row(history, current_time, band_id, prediction_horizon=3):
    """Build feature vector for a single band at a given time.

    The feature set must use only values observed at or before current_time.
    Any future-valued data is rejected to prevent leakage.
    """
    if current_time < 0:
        raise ValueError("current_time must be >= 0")

    if any(item["time"] > current_time for item in history):
        raise ValueError("history contains future information; use only data available at or before current_time")

    band_history = [item for item in history if item.get("band") == band_id]
    if not band_history:
        return {
            "band_id": band_id,
            "time": current_time,
            "recent_hit_rate_3": 0.0,
            "recent_hit_rate_5": 0.0,
            "recent_hit_rate_10": 0.0,
            "recent_hit_rate_20": 0.0,
            "recent_miss_rate_5": 0.0,
            "total_hits": 0,
            "total_misses": 0,
            "time_since_last_hit": 0.0,
            "time_since_last_scan": 0.0,
            "mean_signal_strength": 0.0,
            "recent_signal_strength": 0.0,
            "signal_strength_trend": 0.0,
            "activity_probability": 0.0,
            "estimated_period": 0.0,
            "periodicity_confidence": 0.0,
            "recent_activity_trend": 0.0,
            "drift_score": 0.0,
            "future_activity": 0,
        }

    recent_3 = _window_history(band_history, 3)
    recent_5 = _window_history(band_history, 5)
    recent_10 = _window_history(band_history, 10)
    recent_20 = _window_history(band_history, 20)

    total_hits = sum(1 for item in band_history if item.get("detected"))
    total_misses = len(band_history) - total_hits

    hit_times = [item["time"] for item in band_history if item.get("detected")]
    last_hit_time = hit_times[-1] if hit_times else None
    last_scan_time = band_history[-1]["time"] if band_history else current_time

    time_since_last_hit = 0.0 if last_hit_time is None else max(0.0, current_time - last_hit_time)
    time_since_last_scan = 0.0 if not band_history else max(0.0, current_time - last_scan_time)

    strengths = [float(item.get("signal_strength", 0.0) or 0.0) for item in band_history]
    recent_strengths = [float(item.get("signal_strength", 0.0) or 0.0) for item in recent_10]
    mean_signal_strength = sum(strengths) / len(strengths)
    recent_signal_strength = sum(recent_strengths) / len(recent_strengths) if recent_strengths else 0.0

    if len(strengths) >= 2:
        signal_strength_trend = strengths[-1] - strengths[0]
    else:
        signal_strength_trend = 0.0

    activity_probability = _safe_divide(total_hits, len(band_history))

    if len(hit_times) >= 2:
        intervals = [later - earlier for earlier, later in zip(hit_times, hit_times[1:])]
        estimated_period = sum(intervals) / len(intervals) if intervals else 0.0
        period_deviation = sum(abs(interval - estimated_period) for interval in intervals) / len(intervals) if intervals else 0.0
        periodicity_confidence = max(0.0, min(1.0, 1.0 - (period_deviation / max(estimated_period, 1.0))))
    else:
        estimated_period = 0.0
        periodicity_confidence = 0.0

    if len(recent_5) >= 2:
        recent_step_hits = sum(1 for item in recent_5 if item.get("detected"))
        older_window = band_history[-(len(recent_5) + 2):-2] if len(band_history) > len(recent_5) else []
        older_hit_rate = _safe_divide(sum(1 for item in older_window if item.get("detected")), max(1, len(older_window)))
        recent_activity_trend = recent_step_hits / len(recent_5) - older_hit_rate
    else:
        recent_activity_trend = 0.0

    drift_score = 0.0
    if len(band_history) >= 2:
        reference_window = band_history[: max(1, len(band_history) // 2)]
        recent_window = band_history[-max(1, len(band_history) // 2):]
        reference_rate = _safe_divide(sum(1 for item in reference_window if item.get("detected")), max(1, len(reference_window)))
        recent_rate = _safe_divide(sum(1 for item in recent_window if item.get("detected")), max(1, len(recent_window)))
        drift_score = abs(recent_rate - reference_rate)

    row = {
        "band_id": band_id,
        "time": current_time,
        "recent_hit_rate_3": _safe_divide(sum(1 for item in recent_3 if item.get("detected")), max(1, len(recent_3))),
        "recent_hit_rate_5": _safe_divide(sum(1 for item in recent_5 if item.get("detected")), max(1, len(recent_5))),
        "recent_hit_rate_10": _safe_divide(sum(1 for item in recent_10 if item.get("detected")), max(1, len(recent_10))),
        "recent_hit_rate_20": _safe_divide(sum(1 for item in recent_20 if item.get("detected")), max(1, len(recent_20))),
        "recent_miss_rate_5": 1.0 - _safe_divide(sum(1 for item in recent_5 if item.get("detected")), max(1, len(recent_5))),
        "total_hits": total_hits,
        "total_misses": total_misses,
        "time_since_last_hit": time_since_last_hit,
        "time_since_last_scan": time_since_last_scan,
        "mean_signal_strength": mean_signal_strength,
        "recent_signal_strength": recent_signal_strength,
        "signal_strength_trend": signal_strength_trend,
        "activity_probability": activity_probability,
        "estimated_period": estimated_period,
        "periodicity_confidence": periodicity_confidence,
        "recent_activity_trend": recent_activity_trend,
        "drift_score": drift_score,
        "future_activity": 0,
    }
    return row
