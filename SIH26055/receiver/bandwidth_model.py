"""Bandwidth model: defines receiver capability limits, separate from receiver logic."""


class BandwidthModel:
    def __init__(self, num_bands, instantaneous_bands=1):
        if num_bands <= 0:
            raise ValueError("num_bands must be > 0")
        if not (1 <= instantaneous_bands <= num_bands):
            raise ValueError("instantaneous_bands must satisfy 1 <= instantaneous_bands <= num_bands")

        self.num_bands = num_bands
        self.instantaneous_bands = instantaneous_bands

    def validate_band(self, band_id):
        """Raise if band_id is outside the valid range [0, num_bands - 1]."""
        if not (0 <= band_id < self.num_bands):
            raise ValueError(f"band_id {band_id} out of range [0, {self.num_bands - 1}]")
        return True

    def can_scan(self, band_ids):
        """Raise if a proposed scan request exceeds instantaneous bandwidth or band range."""
        if isinstance(band_ids, int):
            band_ids = [band_ids]

        if len(band_ids) > self.instantaneous_bands:
            raise ValueError(
                f"requested {len(band_ids)} band(s) exceeds instantaneous_bands={self.instantaneous_bands}"
            )

        for band_id in band_ids:
            self.validate_band(band_id)

        return True
