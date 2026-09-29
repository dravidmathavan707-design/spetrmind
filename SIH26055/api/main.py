"""FastAPI interface for the SpectraMind cognitive scanning demo."""

import asyncio
from pathlib import Path

from fastapi import FastAPI, Query, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from evaluation.generalization import evaluate_unseen, summarize_unseen
from environment.scenarios import SCENARIOS
from main import run_cognitive_loop
from explainability.decision_explainer import DecisionExplainer
from realtime import RealtimeScanner

app = FastAPI(title="SpectraMind Cognitive Spectrum Scanner", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
def health():
    return {"status": "ok", "service": "SpectraMind"}


@app.get("/api/mission")
def mission(steps: int = Query(40, ge=0, le=10000)):
    result = run_cognitive_loop(steps=steps)
    explainer = DecisionExplainer()
    return {
        "metrics": result["metrics"],
        "decisions": result["decisions"],
        "observations": result["observations"],
        "explanations": [
            explainer.explain(decision) for decision in result["decisions"]
        ],
        "spectrum": result["belief"],
    }


@app.get("/api/benchmark")
def benchmark(steps: int = Query(40, ge=0, le=10000)):
    evaluation = evaluate_unseen(steps=steps)
    return {
        "scenarios": evaluation["unseen_scenarios"],
        "summary": summarize_unseen(evaluation),
    }


@app.websocket("/api/realtime")
async def realtime(websocket: WebSocket):
    """Stream one simulated scan event at a time to connected dashboards."""
    await websocket.accept()
    scenario_name = "stable"
    scanner = RealtimeScanner(scenario_factory=SCENARIOS[scenario_name])
    runtime_status = "running"
    last_event = None

    async def receive_commands():
        nonlocal scanner, runtime_status, scenario_name
        while True:
            message = await websocket.receive_json()
            command = message.get("type")
            if command == "tune":
                scanner.request_band(message.get("band"))
            elif command == "start":
                runtime_status = "running"
            elif command == "pause":
                runtime_status = "paused"
            elif command == "stop":
                runtime_status = "stopped"
            elif command == "reset":
                scenario_name = message.get("scenario", scenario_name)
                if scenario_name not in SCENARIOS:
                    scenario_name = "stable"
                scanner.reset(SCENARIOS[scenario_name])
                runtime_status = "running"
            elif command == "scenario":
                scenario_name = message.get("scenario", "stable")
                if scenario_name not in SCENARIOS:
                    scenario_name = "stable"
                scanner.reset(SCENARIOS[scenario_name])
                runtime_status = "running"

    command_task = asyncio.create_task(receive_commands())
    try:
        while True:
            if runtime_status == "running":
                last_event = scanner.step()
            event = dict(last_event or {
                "time": 0,
                "cycle": 0,
                "band": 0,
                "detected": False,
                "spectrum": scanner.belief.all(),
                "metrics": {"detection_rate": 0.0, "hits": 0, "misses": 0},
            })
            event["runtime_status"] = runtime_status
            event["scenario"] = scenario_name
            await websocket.send_json(event)
            await asyncio.sleep(0.5)
    except WebSocketDisconnect:
        return
    finally:
        command_task.cancel()


dashboard_dist = Path(__file__).resolve().parent.parent / "dashboard" / "react-app" / "dist"
if dashboard_dist.exists():
    app.mount("/", StaticFiles(directory=dashboard_dist, html=True), name="dashboard")
