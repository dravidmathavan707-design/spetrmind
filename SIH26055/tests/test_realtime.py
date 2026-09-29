from fastapi.testclient import TestClient

from api.main import app, health
from environment.scenarios import SCENARIOS
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
