"""Random scheduler: independent uniform random band selection (baseline)."""

import random as random_module


class RandomScheduler:
    def __init__(self, num_bands, seed=None):
        if num_bands <= 0:
            raise ValueError("num_bands must be > 0")

        self.num_bands = num_bands
        self.seed = seed
        self._rng = random_module.Random(seed)

    def next_band(self):
        """Independently pick a valid band uniformly at random; repeats allowed."""
        return self._rng.randrange(self.num_bands)

    def reset(self):
        """Reinitialize the RNG so a seeded scheduler reproduces its sequence."""
        self._rng = random_module.Random(self.seed)
