from fastapi.testclient import TestClient

from api.main import app, health
from environment.scenarios import SCENARIOS
from prediction.temporal_model import TemporalModel
from realtime import RealtimeScanner


def test_health_endpoint_function():
    assert health() == {"status": "ok", "service": "SpectraMind"}


def test_requested_band_is_scanned_next():
    scanner = RealtimeScanner()
    scanner.request_band(7)

    event = scanner.step()

    assert event["band"] == 7
    assert event["cycle"] == 1


def test_reset_restarts_selected_scenario():
    scanner = RealtimeScanner()
    scanner.step()

    scanner.reset(SCENARIOS["periodic"])
    event = scanner.step()

    assert event["time"] == 0
    assert scanner.step_number == 1


def test_websocket_stream_accepts_controls():
    with TestClient(app) as client:
        with client.websocket_connect("/api/realtime") as websocket:
            first = websocket.receive_json()
            assert first["runtime_status"] == "running"
            assert first["scenario"] == "stable"

            websocket.send_json({"type": "pause"})
            paused = websocket.receive_json()
            assert paused["runtime_status"] == "paused"

            websocket.send_json({"type": "scenario", "scenario": "periodic"})
            changed = websocket.receive_json()
            assert changed["runtime_status"] == "running"
            assert changed["scenario"] == "periodic"

            websocket.send_json({"type": "tune", "band": 7})
            tuned = websocket.receive_json()
            assert tuned["band"] == 7

            websocket.send_json({"type": "stop"})
            stopped = websocket.receive_json()
            assert stopped["runtime_status"] == "stopped"


def test_temporal_model_builds_feature_based_forecast():
    model = TemporalModel(num_bands=4)

    for step in range(12):
        model.update({"time": step, "band": 1, "detected": step % 3 != 0, "signal_strength": 0.8 if step % 3 != 0 else 0.1})
        model.update({"time": step, "band": 0, "detected": False, "signal_strength": 0.05})
        model.update({"time": step, "band": 2, "detected": False, "signal_strength": 0.0})

    model.train()

    assert model.is_trained()
    assert model.predict(1, future_time=15) > model.predict(0, future_time=15)
