"""Refresh Layer 1 only — lightweight, meant to run every ~2h via Task
Scheduler (task "AlphaForge-Layer1-Refresh"). Does NOT run Screening, so
market_breadth/market_sentiment keep whatever status they last had — that's
an accepted tradeoff to keep this cheap enough to run this often. The full
12/12 reading happens once/day in refresh_full_pipeline.py instead.

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

OUT_PATH = ROOT / "dashboard" / "data" / "layer1_context.json"


def _atomic_write(path: Path, data: dict) -> None:
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    os.replace(tmp, path)


def main() -> int:
    pkg = build_market_context_package()
    data = pkg.to_dict()
    _atomic_write(OUT_PATH, data)

    n_ok = sum(1 for c in data["components"].values() if c["status"] == "ok")
    score = data["layer_score"]["final_score"] if data["layer_score"] else None
    print(f"Layer 1 refreshed: {n_ok}/{len(data['components'])} ok, layer_score={score}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
