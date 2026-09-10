"""Receiver model: scans exactly one band at a time and returns HIT/MISS only."""


class Receiver:
    def __init__(self, bandwidth_model=None, noise_model=None,
                 detection_threshold=None):
        self.bandwidth_model = bandwidth_model
        self.noise_model = noise_model
        self.detection_threshold = detection_threshold
        if detection_threshold is not None and not isinstance(detection_threshold, (int, float)):
            raise ValueError("detection_threshold must be numeric")

    def scan(self, band_id, rf_world):
        """Query the RF world for a single band; never see any other band's state."""
        if self.bandwidth_model is not None:
            self.bandwidth_model.can_scan(band_id)

        detected, signal_strength = rf_world.query_band(band_id)

        if self.noise_model is not None:
            measured_power, false_alarm = self.noise_model.sample(
                signal_strength if detected else None
            )
            threshold = self.detection_threshold
            if threshold is None:
                threshold = self.noise_model.noise_floor
            detected = (detected and measured_power >= threshold) or false_alarm
            signal_strength = measured_power if detected else None

        return {
            "time": rf_world.current_time,
            "band": band_id,
            "detected": detected,
            "signal_strength": signal_strength if detected else None,
        }

