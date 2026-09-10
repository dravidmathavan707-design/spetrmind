"""Deterministic RF scenarios used to challenge schedulers."""

from environment.emitter import Emitter
from environment.rf_world import RFWorld


class PatternEmitter(Emitter):
	def __init__(self, band_id, signal_strength, start_time, duration,
				 period=None, active_duration=None, band_schedule=None):
		super().__init__(band_id, signal_strength, start_time, duration)
		self.period = period
		self.active_duration = active_duration or duration
		self.band_schedule = band_schedule

	def update(self, current_time):
		if self.band_schedule:
			scheduled_band = next(
				(band for time, band in reversed(self.band_schedule)
				 if current_time >= time),
				self.band_id,
			)
			self.band_id = scheduled_band

		if self.period is None:
			return super().update(current_time)

		elapsed = current_time - self.start_time
		self.active = (
			0 <= elapsed < self.duration
			and elapsed % self.period < self.active_duration
		)
		return self.active


def _world(num_bands=20, noise_level=0.0):
	world = RFWorld(num_bands=num_bands)
	world.noise_level = noise_level
	return world


def stable(num_bands=20):
	world = _world(num_bands)
	world.add_emitter(Emitter(3, -60, 0, 100))
	return world


def bursty(num_bands=20):
	world = _world(num_bands)
	world.add_emitter(PatternEmitter(3, -60, 0, 100, period=10, active_duration=2))
	return world


def periodic(num_bands=20):
	world = _world(num_bands)
	world.add_emitter(PatternEmitter(7, -58, 0, 100, period=5, active_duration=1))
	return world


def frequency_agile(num_bands=20):
	world = _world(num_bands)
	world.add_emitter(PatternEmitter(
		3, -60, 0, 100, band_schedule=[(0, 3), (10, 8), (20, 15), (30, 4)]
	))
	return world


def multiple_emitters(num_bands=20):
	world = _world(num_bands)
	world.add_emitter(Emitter(3, -60, 0, 100))
	world.add_emitter(Emitter(12, -65, 0, 100))
	world.add_emitter(Emitter(17, -55, 0, 100))
	return world


def weak_emitter(num_bands=20):
	world = _world(num_bands)
	world.add_emitter(Emitter(5, -95, 0, 100))
	return world


def noisy(num_bands=20, noise_level=0.35):
	world = _world(num_bands, noise_level=noise_level)
	world.add_emitter(Emitter(9, -70, 0, 100))
	return world


def changing(num_bands=20):
	world = _world(num_bands)
	world.add_emitter(Emitter(3, -60, 0, 20))
	world.add_emitter(Emitter(12, -62, 20, 80))
	return world


SCENARIOS = {
	"stable": stable,
	"bursty": bursty,
	"periodic": periodic,
	"frequency_agile": frequency_agile,
	"multiple_emitters": multiple_emitters,
	"weak": weak_emitter,
	"noisy": noisy,
	"changing": changing,
}
