"""Flask API + static server for the AlphaForge dashboard.

Read-only: serves whatever the pipeline (alphaforge/cli.py) has already
written to dashboard/data/*.json, plus the built React app in
frontend/dist. Does not trigger Screening/Evidence/etc itself.
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

from flask import Flask, jsonify, send_from_directory

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from alphaforge.layer2.sources.live_quote import fetch_live_quote  # noqa: E402
DATA_DIR = ROOT / "dashboard" / "data"
FRONTEND_DIST = ROOT / "frontend" / "dist"

STAGE_FILES = {
    "layer1": "layer1_context.json",
    "screening": "screening.json",
    "evidence": "evidence.json",
    "knowledge": "knowledge.json",
    "peer": "peer_results.json",
    "confidence": "confidence_scores.json",
    "risk": "risk_assessments.json",
    "reasoning": "reasoning_outputs.json",
    "aggregator": "final_recommendations.json",
    "historical": "historical_timeline.json",
}


def _load_stage(name: str) -> dict:
    path = DATA_DIR / STAGE_FILES[name]
    if not path.exists():
        return {}
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def load_all_stages() -> dict[str, dict]:
    return {name: _load_stage(name) for name in STAGE_FILES}


def build_ticker_indexes(stages: dict[str, dict]) -> dict[str, dict]:
    """Index each stage's per-ticker list by ticker for O(1) lookup in /api/ticker/<ticker>."""
    def index_by_ticker(items: list[dict]) -> dict[str, dict]:
        return {item["ticker"]: item for item in items if "ticker" in item}

    return {
        "evidence": index_by_ticker(stages["evidence"].get("packages", [])),
        "knowledge": index_by_ticker(stages["knowledge"].get("profiles", [])),
        "confidence": index_by_ticker(stages["confidence"].get("scores", [])),
        "risk": index_by_ticker(stages["risk"].get("assessments", [])),
        "reasoning": index_by_ticker(stages["reasoning"].get("reasoning_outputs", [])),
        "aggregator": index_by_ticker(stages["aggregator"].get("recommendations", [])),
        # historical_timeline.json is already a dict keyed by ticker.
        "historical": stages["historical"],
    }


STAGES = load_all_stages()
TICKER_INDEX = build_ticker_indexes(STAGES)

app = Flask(__name__, static_folder=str(FRONTEND_DIST), static_url_path="")


@app.get("/api/<stage>")
def get_stage(stage: str):
    if stage not in STAGE_FILES:
        return jsonify({"error": f"unknown stage '{stage}'"}), 404
    return jsonify(STAGES[stage])


@app.get("/api/ticker/<ticker>")
def get_ticker_detail(ticker: str):
    ticker = ticker.upper()
    return jsonify({
        "ticker": ticker,
        "evidence": TICKER_INDEX["evidence"].get(ticker),
        "knowledge": TICKER_INDEX["knowledge"].get(ticker),
        "confidence": TICKER_INDEX["confidence"].get(ticker),
        "risk": TICKER_INDEX["risk"].get(ticker),
        "reasoning": TICKER_INDEX["reasoning"].get(ticker),
        "aggregator": TICKER_INDEX["aggregator"].get(ticker),
        "historical": TICKER_INDEX["historical"].get(ticker),
    })


@app.get("/api/ticker/<ticker>/live")
def get_ticker_live_quote(ticker: str):
    """Level 3 freshness: fetches the current quote from Yahoo Finance right
    now (fast_info only, no history download), not the pipeline snapshot.
    Best-effort — times out and returns {"stale": true} rather than blocking
    the request if Yahoo is slow/unreachable."""
    return jsonify(fetch_live_quote(ticker))


@app.get("/")
@app.get("/<path:path>")
def serve_frontend(path: str = ""):
    full_path = FRONTEND_DIST / path
    if path and full_path.exists() and full_path.is_file():
        return send_from_directory(FRONTEND_DIST, path)
    return send_from_directory(FRONTEND_DIST, "index.html")


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
