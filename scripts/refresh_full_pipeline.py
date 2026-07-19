"""Full pipeline refresh: Screening -> Evidence -> Knowledge -> Peer ->
Confidence -> Risk -> Reasoning -> Aggregator -> Historical, plus Layer 1
with a complete price_cache (so market_breadth/market_sentiment get a real
reading too). Meant to run once/day via Task Scheduler (task
"AlphaForge-FullPipeline-Refresh").

Runs every stage in-process — calls the same run_*() functions directly,
not 9 separate `python -m alphaforge.cli ...` subprocess invocations —
so there's no repeated interpreter startup and no JSON-serialize-then-
deserialize round trip between stages.

All-or-nothing: nothing is written to dashboard/data/ (or the tracked root
reference snapshots) until every stage above has succeeded. A pipeline
that fails partway through must never leave the dashboard in a state
where e.g. Aggregator references a ticker Knowledge doesn't have yet —
that's a worse failure mode than just leaving yesterday's (consistent)
data in place and trying again at the next scheduled run.
"""
from __future__ import annotations

import json
import logging
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from alphaforge.layer1.pipeline import build_market_context_package  # noqa: E402
from alphaforge.layer2.screening import run_screening  # noqa: E402
from alphaforge.layer2.evidence import run_evidence  # noqa: E402
from alphaforge.layer2.knowledge import run_knowledge  # noqa: E402
from alphaforge.layer2.peer import run_peer_comparison  # noqa: E402
from alphaforge.layer2.confidence import run_confidence  # noqa: E402
from alphaforge.layer2.risk import run_risk_assessment  # noqa: E402
from alphaforge.layer2.reasoning import run_reasoning_pipeline  # noqa: E402
from alphaforge.layer2.aggregator import run_aggregator  # noqa: E402
from alphaforge.layer2.historical import load_historical_timeline, update_timeline  # noqa: E402

DATA_DIR = ROOT / "dashboard" / "data"
LOG_DIR = ROOT / "logs"
LOG_DIR.mkdir(exist_ok=True)

# run_screening(limit=None) scans the ENTIRE cheap-filter survivor list
# (5000+ tickers as of this writing) — far beyond the ~47-ticker dataset
# this dashboard has been built and tested against all session. Matches
# the `--limit 60` convention used throughout (scans 60 candidates from
# the cheap-filtered list, ~47 typically pass the harder filters).
# Override via SCREENING_LIMIT env var if the target universe size changes.
SCREENING_LIMIT = int(os.environ.get("SCREENING_LIMIT", "60"))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    handlers=[
        logging.FileHandler(LOG_DIR / "refresh_full_pipeline.log"),
        logging.StreamHandler(sys.stdout),
    ],
)
log = logging.getLogger("refresh_full_pipeline")


def _atomic_write(path: Path, data: dict) -> None:
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    os.replace(tmp, path)


def main() -> int:
    started = datetime.now(timezone.utc)
    log.info("Full pipeline refresh started")

    try:
        screening_result, price_cache = run_screening(limit=SCREENING_LIMIT)
        log.info(f"Screening: {len(screening_result.passed)} passed / {screening_result.universe_scanned} scanned")

        evidence_packages = run_evidence(screening_result)
        log.info(f"Evidence: {len(evidence_packages)} packages")

        profiles = run_knowledge(evidence_packages, screening_result.passed)
        log.info(f"Knowledge: {len(profiles)} profiles")

        comparisons = run_peer_comparison(profiles)
        log.info(f"Peer: {len(comparisons)} comparisons")

        confidences = run_confidence(profiles, comparisons)
        log.info(f"Confidence: {len(confidences)} scores")

        risks = run_risk_assessment(profiles)
        log.info(f"Risk: {len(risks)} assessments")

        confidence_map = {c.ticker: c for c in confidences}
        risk_map = {r.ticker: r for r in risks}
        reasonings = [
            run_reasoning_pipeline(p, confidence_map.get(p.ticker), risk_map.get(p.ticker))
            for p in profiles
        ]
        log.info(f"Reasoning: {len(reasonings)} outputs")

        recommendations = run_aggregator(profiles, comparisons, confidences, risks, reasonings)
        log.info(f"Aggregator: {len(recommendations)} recommendations")

        timelines = load_historical_timeline(str(DATA_DIR / "historical_timeline.json"))
        timelines = update_timeline(timelines, recommendations)
        log.info(f"Historical: {len(timelines)} tickers tracked")

        layer1_pkg = build_market_context_package(price_cache=price_cache)
        n_ok = sum(1 for c in layer1_pkg.components.values() if c.status == "ok")
        log.info(f"Layer 1: {n_ok}/{len(layer1_pkg.components)} ok")
    except Exception:
        log.exception("Pipeline failed — dashboard/data left untouched")
        return 1

    # Every stage succeeded — build the JSON payloads (same shape cli.py's
    # per-stage commands already produce, so the dashboard doesn't need to
    # know or care whether a file came from the CLI or this orchestrator).
    screening_data = screening_result.to_dict()
    evidence_data = {
        "screening_universe": screening_result.universe_raw,
        "screening_passed": len(screening_result.passed),
        "evidence_generated": len(evidence_packages),
        "generated_at": evidence_packages[0].generated_at if evidence_packages else None,
        "packages": [p.to_dict() for p in evidence_packages],
    }
    knowledge_data = {
        "evidence_count": len(evidence_packages),
        "knowledge_generated": len(profiles),
        "generated_at": profiles[0].metadata.evidence_date if profiles else None,
        "profiles": [p.to_dict() for p in profiles],
    }
    peer_data = {
        "knowledge_count": len(profiles),
        "peer_comparisons_generated": len(comparisons),
        "generated_at": comparisons[0].generated_at if comparisons else None,
        "comparisons": [c.to_dict() for c in comparisons],
    }
    confidence_data = {
        "knowledge_count": len(profiles),
        "confidence_scores_generated": len(confidences),
        "generated_at": confidences[0].assessed_at if confidences else None,
        "scores": [s.to_dict() for s in confidences],
    }
    risk_data = {
        "knowledge_count": len(profiles),
        "risk_assessments_generated": len(risks),
        "generated_at": risks[0].assessed_at if risks else None,
        "assessments": [a.to_dict() for a in risks],
    }
    reasoning_data = {
        "knowledge_count": len(profiles),
        "reasoning_outputs_generated": len(reasonings),
        "generated_at": reasonings[0].aggregated_at if reasonings else None,
        "reasoning_outputs": [r.to_dict() for r in reasonings],
    }
    aggregator_data = {
        "profiles_count": len(profiles),
        "recommendations_generated": len(recommendations),
        "generated_at": recommendations[0].recommended_at if recommendations else None,
        "recommendations": [r.to_dict() for r in recommendations],
    }
    timeline_data = {ticker: t.to_dict() for ticker, t in timelines.items()}
    layer1_data = layer1_pkg.to_dict()

    _atomic_write(DATA_DIR / "screening.json", screening_data)
    _atomic_write(DATA_DIR / "evidence.json", evidence_data)
    _atomic_write(DATA_DIR / "knowledge.json", knowledge_data)
    _atomic_write(DATA_DIR / "peer_results.json", peer_data)
    _atomic_write(DATA_DIR / "confidence_scores.json", confidence_data)
    _atomic_write(DATA_DIR / "risk_assessments.json", risk_data)
    _atomic_write(DATA_DIR / "reasoning_outputs.json", reasoning_data)
    _atomic_write(DATA_DIR / "final_recommendations.json", aggregator_data)
    _atomic_write(DATA_DIR / "historical_timeline.json", timeline_data)
    _atomic_write(DATA_DIR / "layer1_context.json", layer1_data)

    # Root reference snapshots — tracked in git, matches the convention
    # already established for evidence.json/knowledge.json/peer_results.json/
    # screening.json at the repo root.
    _atomic_write(ROOT / "screening.json", screening_data)
    _atomic_write(ROOT / "evidence.json", evidence_data)
    _atomic_write(ROOT / "knowledge.json", knowledge_data)
    _atomic_write(ROOT / "peer_results.json", peer_data)

    finished = datetime.now(timezone.utc)
    log.info(f"Full pipeline refresh complete in {(finished - started).total_seconds():.0f}s")
    return 0


if __name__ == "__main__":
    sys.exit(main())
