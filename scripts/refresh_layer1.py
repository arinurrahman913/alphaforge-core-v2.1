"""Refresh Layer 1 only — lightweight, meant to run every ~2h via Task
Scheduler (task "AlphaForge-Layer1-Refresh"). Does NOT run Screening (no
network fan-out), but REUSES the price history the daily full pipeline already
cached (.cache/price_history/, loaded via load_cached_price_cache — zero
network) so market_breadth/market_sentiment stay populated instead of dropping
to missing/degraded on every fast refresh. The freshness classifier still
marks that reused breadth fresh/acceptable/stale honestly based on the real
price dates. If the cache is empty (first run ever), breadth falls back to
missing, same as before. The authoritative 12/12 reading happens once/day in
refresh_full_pipeline.py.

Writes atomically (tmp file + os.replace) so backend/app.py's mtime-based
lazy reload never observes a half-written file.
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from alphaforge.layer1.pipeline import build_market_context_package  # noqa: E402
from alphaforge.layer2.screening import load_cached_price_cache  # noqa: E402

OUT_PATH = ROOT / "dashboard" / "data" / "layer1_context.json"
SCREENING_PATH = ROOT / "dashboard" / "data" / "screening.json"


def _atomic_write(path: Path, data: dict) -> None:
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    os.replace(tmp, path)


def _passed_tickers() -> list[str] | None:
    """Daftar ticker yang lolos Screening terakhir (dari screening.json yang
    ditulis full pipeline). Dipakai membatasi price_cache breadth ke universe
    yang sama persis dengan run harian. None kalau file belum ada → loader
    fallback pakai semua cache."""
    if not SCREENING_PATH.exists():
        return None
    try:
        data = json.loads(SCREENING_PATH.read_text(encoding="utf-8"))
    except Exception:
        return None
    passed = data.get("passed") or []
    tickers = [row["ticker"] for row in passed if isinstance(row, dict) and row.get("ticker")]
    return tickers or None


def main() -> int:
    price_cache = load_cached_price_cache(_passed_tickers())
    pkg = build_market_context_package(price_cache=price_cache or None)
    data = pkg.to_dict()
    _atomic_write(OUT_PATH, data)

    n_ok = sum(1 for c in data["components"].values() if c["status"] == "ok")
    score = data["layer_score"]["final_score"] if data["layer_score"] else None
    reused = f", breadth dari {len(price_cache)} ticker cache" if price_cache else ", tanpa cache breadth"
    print(f"Layer 1 refreshed: {n_ok}/{len(data['components'])} ok, layer_score={score}{reused}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
