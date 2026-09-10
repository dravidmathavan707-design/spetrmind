"""FastAPI interface for the SpectraMind cognitive scanning demo."""

from pathlib import Path

from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from evaluation.generalization import evaluate_unseen, summarize_unseen
from main import run_cognitive_loop
from explainability.decision_explainer import DecisionExplainer

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


dashboard_dist = Path(__file__).resolve().parent.parent / "dashboard" / "react-app" / "dist"
if dashboard_dist.exists():
    app.mount("/", StaticFiles(directory=dashboard_dist, html=True), name="dashboard")
