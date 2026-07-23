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
import subprocess
import sys
import threading
import time
from pathlib import Path

from flask import Flask, jsonify, request, send_from_directory

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from alphaforge.layer2.sources.live_quote import fetch_live_quote  # noqa: E402
from alphaforge.layer2.sources.sector_map import (  # noqa: E402
    KNOWN_SECTORS, load_sector_map_meta as sector_map_meta
)

DATA_DIR = ROOT / "dashboard" / "data"
FRONTEND_DIST = ROOT / "frontend" / "dist"

STAGE_FILES = {
    "layer1": "layer1_context.json",
    "layer1_history": "layer1_history.json",
    "screening": "screening.json",
    "evidence": "evidence.json",
    "knowledge": "knowledge.json",
    "catalyst": "catalysts.json",
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
    catalyst = _index_by_ticker(_get_stage("catalyst").get("catalyst_sets", []))
    confidence = _index_by_ticker(_get_stage("confidence").get("scores", []))
    risk = _index_by_ticker(_get_stage("risk").get("assessments", []))
    reasoning = _index_by_ticker(_get_stage("reasoning").get("reasoning_outputs", []))
    aggregator = _index_by_ticker(_get_stage("aggregator").get("recommendations", []))
    historical = _get_stage("historical")

    return jsonify({
        "ticker": ticker,
        "evidence": evidence.get(ticker),
        "knowledge": knowledge.get(ticker),
        "catalyst": catalyst.get(ticker),
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


# --- Refresh pipeline dari dashboard (tombol Generate) -----------------------
# Menjalankan script refresh yang sudah ada sebagai subprocess di thread
# background, supaya request HTTP tidak nge-block. Status di-poll oleh frontend.
REFRESH_SCRIPTS = {
    "layer1": ROOT / "scripts" / "refresh_layer1.py",
    "full": ROOT / "scripts" / "refresh_full_pipeline.py",
}

_refresh_lock = threading.Lock()
_refresh_state: dict = {
    "running": False,
    "mode": None,
    "sector": None,
    "started_at": None,
    "finished_at": None,
    "ok": None,
    "message": None,
}


def _run_refresh(mode: str, sector: str | None = None) -> None:
    script = REFRESH_SCRIPTS[mode]
    ok = False
    msg = ""
    try:
        # mode="full" sekarang scan full-market (~5000+ ticker) secara default
        # (lihat SCREENING_LIMIT di scripts/refresh_full_pipeline.py) — bisa
        # makan waktu berjam-jam, jauh di atas 30 menit lama yang cukup untuk
        # sample 60-ticker. Kalau `sector` diisi, scope-nya jauh lebih kecil
        # (satu sektor GICS) jadi tetap cepat walau mode="full".
        timeout = 4 * 3600 if mode == "full" and not sector else 1800
        env = dict(os.environ)
        if sector:
            env["SCREENING_SECTOR"] = sector
        proc = subprocess.run(
            [sys.executable, str(script)],
            cwd=str(ROOT),
            capture_output=True,
            text=True,
            timeout=timeout,
            env=env,
        )
        ok = proc.returncode == 0
        out = (proc.stdout or "").strip()
        err = (proc.stderr or "").strip()
        if ok:
            msg = out.splitlines()[-1] if out else "Selesai."
        else:
            tail = err.splitlines()[-1] if err else f"exit code {proc.returncode}"
            msg = f"Gagal: {tail}"
    except subprocess.TimeoutExpired:
        msg = "Timeout (>30 menit)."
    except Exception as exc:  # noqa: BLE001
        msg = f"Error: {exc}"
    finally:
        with _refresh_lock:
            _refresh_state.update(running=False, finished_at=time.time(), ok=ok, message=msg)


@app.post("/api/refresh/<mode>")
def start_refresh(mode: str):
    if mode not in REFRESH_SCRIPTS:
        return jsonify({"error": f"unknown mode '{mode}'"}), 404
    sector = request.args.get("sector") or None
    with _refresh_lock:
        if _refresh_state["running"]:
            return jsonify({"running": True, "mode": _refresh_state["mode"], "already": True}), 409
        _refresh_state.update(
            running=True, mode=mode, sector=sector, started_at=time.time(), finished_at=None, ok=None, message=None
        )
    threading.Thread(target=_run_refresh, args=(mode, sector), daemon=True).start()
    return jsonify({"started": True, "mode": mode, "sector": sector})


@app.get("/api/refresh/status")
def refresh_status():
    with _refresh_lock:
        return jsonify(dict(_refresh_state))


@app.get("/api/sectors")
def get_sectors():
    """Daftar sektor GICS yang bisa dipilih di dashboard + status sector_map
    (kapan terakhir dibangun, berapa ticker sudah termapping) — dipakai
    tombol screening per-sektor supaya user tahu mapnya sudah siap atau belum
    sebelum klik (kalau belum dibangun, scripts/build_sector_map.py perlu
    dijalankan dulu, kalau tidak filter sektor apapun hasilkan 0 kandidat)."""
    meta = sector_map_meta()
    return jsonify({
        "known_sectors": KNOWN_SECTORS,
        "map_built": meta is not None,
        "generated_at": meta.get("generated_at") if meta else None,
        "total_mapped": meta.get("total_mapped") if meta else 0,
        "coverage": meta.get("coverage") if meta else {},
    })


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
