"""Flask API + static server for the AlphaForge dashboard.

Read-only: serves whatever the pipeline has already written to
dashboard/data/*.json, plus the built React app in frontend/dist. Does not
trigger Screening/Evidence/etc itself — that's scripts/refresh_layer1.py
(every ~2h) and scripts/refresh_full_pipeline.py (daily), run by Windows
Task Scheduler independently of whether this Flask process is even running.

Each stage file is reloaded lazily based on mtime (_get_stage below)
instead of being read once at import time — so once a scheduled refresh
script finishes writing new data, the next request picks it up automatically,
no restart needed. The stage files themselves are written atomically
(tmp file + os.replace) by the refresh scripts, so this never observes a
half-written file mid-reload.
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

# name -> (mtime at last load, parsed JSON). Populated lazily on first request.
_stage_cache: dict[str, tuple[float, dict]] = {}


def _get_stage(name: str) -> dict:
    path = DATA_DIR / STAGE_FILES[name]
    if not path.exists():
        return {}

    mtime = path.stat().st_mtime
    cached = _stage_cache.get(name)
    if cached is not None and cached[0] == mtime:
        return cached[1]

    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    _stage_cache[name] = (mtime, data)
    return data


def _index_by_ticker(items: list[dict]) -> dict[str, dict]:
    return {item["ticker"]: item for item in items if "ticker" in item}


app = Flask(__name__, static_folder=str(FRONTEND_DIST), static_url_path="")


@app.get("/api/<stage>")
def get_stage(stage: str):
    if stage not in STAGE_FILES:
        return jsonify({"error": f"unknown stage '{stage}'"}), 404
    return jsonify(_get_stage(stage))


@app.get("/api/ticker/<ticker>")
def get_ticker_detail(ticker: str):
    ticker = ticker.upper()
    evidence = _index_by_ticker(_get_stage("evidence").get("packages", []))
    knowledge = _index_by_ticker(_get_stage("knowledge").get("profiles", []))
    confidence = _index_by_ticker(_get_stage("confidence").get("scores", []))
    risk = _index_by_ticker(_get_stage("risk").get("assessments", []))
    reasoning = _index_by_ticker(_get_stage("reasoning").get("reasoning_outputs", []))
    aggregator = _index_by_ticker(_get_stage("aggregator").get("recommendations", []))
    historical = _get_stage("historical")

    return jsonify({
        "ticker": ticker,
        "evidence": evidence.get(ticker),
        "knowledge": knowledge.get(ticker),
        "confidence": confidence.get(ticker),
        "risk": risk.get(ticker),
        "reasoning": reasoning.get(ticker),
        "aggregator": aggregator.get(ticker),
        "historical": historical.get(ticker),
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
