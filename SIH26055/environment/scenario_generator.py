"""Seeded generation of varied synthetic RF worlds."""

import random

from environment.scenarios import SCENARIOS


def generate_scenario(name=None, num_bands=20, seed=None):
	"""Return a fresh scenario world, optionally choosing its type by seed."""
	if num_bands <= 0:
		raise ValueError("num_bands must be > 0")

	generator = random.Random(seed)
	scenario_name = name or generator.choice(sorted(SCENARIOS))
	if scenario_name not in SCENARIOS:
		raise ValueError(f"unknown scenario: {scenario_name}")
	return SCENARIOS[scenario_name](num_bands=num_bands)


def available_scenarios():
	return tuple(sorted(SCENARIOS))
