"""Historical tracking module — Layer 2 Fase B, stage 6: Decision Tracking Over Time

Track recommendations, compare dengan actual outcomes, measure accuracy.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import TYPE_CHECKING

from .historical_contracts import DecisionRecord, HistoricalTimeline

if TYPE_CHECKING:
    from .aggregator_contracts import FinalRecommendation


def create_decision_record(recommendation: FinalRecommendation) -> DecisionRecord:
    """Create decision record dari FinalRecommendation."""
    return DecisionRecord(
        ticker=recommendation.ticker,
        recommendation=recommendation.recommendation,
        conviction=recommendation.conviction,
        recommendation_date=recommendation.recommended_at,
        reasoning_summary=recommendation.reasoning_summary,
        confidence_score=recommendation.confidence_score,
        risk_score=recommendation.risk_score,
        reasoning_score=recommendation.reasoning_score,
        tracking_id=recommendation.tracking_id,
        next_review_date=recommendation.next_review_date,
    )


def load_historical_timeline(timeline_file: str) -> dict[str, HistoricalTimeline]:
    """Load historical timeline dari file.

    Args:
        timeline_file: Path ke historical_timeline.json

    Returns:
        Dict mapping ticker → HistoricalTimeline
    """
    if not Path(timeline_file).exists():
        return {}

    with open(timeline_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    timelines = {}
    for ticker, timeline_dict in data.items():
        records = [
            DecisionRecord(**record_dict)
            for record_dict in timeline_dict.get("records", [])
        ]
        timeline = HistoricalTimeline(
            ticker=ticker,
            total_recommendations=timeline_dict.get("total_recommendations", 0),
            first_recommendation_date=timeline_dict.get("first_recommendation_date"),
            last_recommendation_date=timeline_dict.get("last_recommendation_date"),
            records=records,
            correct_predictions=timeline_dict.get("correct_predictions", 0),
            total_outcomes=timeline_dict.get("total_outcomes", 0),
            accuracy_pct=timeline_dict.get("accuracy_pct"),
        )
        timelines[ticker] = timeline

    return timelines


def update_timeline(
    timelines: dict[str, HistoricalTimeline],
    new_recommendations: list[FinalRecommendation],
) -> dict[str, HistoricalTimeline]:
    """Update timelines dengan new recommendations.

    Args:
        timelines: Existing timelines dict
        new_recommendations: New FinalRecommendation list

    Returns:
        Updated timelines dict
    """
    for rec in new_recommendations:
        if rec.ticker not in timelines:
            timelines[rec.ticker] = HistoricalTimeline(ticker=rec.ticker)

        timeline = timelines[rec.ticker]

        # Create record
        record = create_decision_record(rec)
        timeline.records.append(record)
        timeline.total_recommendations += 1
        timeline.last_recommendation_date = record.recommendation_date
        if not timeline.first_recommendation_date:
            timeline.first_recommendation_date = record.recommendation_date

    return timelines


def save_historical_timeline(timelines: dict[str, HistoricalTimeline], output_file: str) -> None:
    """Save historical timelines ke file.

    Args:
        timelines: Dict mapping ticker → HistoricalTimeline
        output_file: Path ke output file
    """
    data = {}
    for ticker, timeline in timelines.items():
        data[ticker] = timeline.to_dict()

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def compare_recommendations(
    old_record: DecisionRecord,
    new_recommendation: FinalRecommendation,
) -> dict:
    """Compare old recommendation vs new recommendation.

    Args:
        old_record: Historical DecisionRecord
        new_recommendation: New FinalRecommendation

    Returns:
        Comparison dict dengan changes
    """
    changed = old_record.recommendation != new_recommendation.recommendation
    conviction_change = new_recommendation.conviction - old_record.conviction
    score_change = new_recommendation.reasoning_score - old_record.reasoning_score

    return {
        "ticker": old_record.ticker,
        "recommendation_changed": changed,
        "old_stance": old_record.recommendation,
        "new_stance": new_recommendation.recommendation,
        "old_conviction": old_record.conviction,
        "new_conviction": new_recommendation.conviction,
        "conviction_change": round(conviction_change, 0),
        "old_score": old_record.reasoning_score,
        "new_score": new_recommendation.reasoning_score,
        "score_change": round(score_change, 1),
        "last_recommendation_date": old_record.recommendation_date,
        "new_recommendation_date": new_recommendation.recommended_at,
    }


def record_outcome(
    timeline: HistoricalTimeline,
    tracking_id: str,
    actual_return_pct: float,
) -> DecisionRecord | None:
    """Record actual outcome untuk satu decision.

    Args:
        timeline: HistoricalTimeline
        tracking_id: UUID dari decision yang ingin di-track
        actual_return_pct: Actual return sejak recommendation hingga sekarang

    Returns:
        Updated DecisionRecord atau None jika tracking_id tidak ditemukan
    """
    for record in timeline.records:
        if record.tracking_id == tracking_id:
            record.outcome_date = datetime.now(timezone.utc).isoformat()
            record.actual_return_pct = actual_return_pct

            # Evaluate correctness
            if record.recommendation in ["strong_buy", "buy"]:
                record.decision_correct = actual_return_pct > 0
            elif record.recommendation in ["strong_sell", "sell"]:
                record.decision_correct = actual_return_pct < 0
            else:  # hold
                record.decision_correct = -5 < actual_return_pct < 5

            # Update timeline stats
            timeline.total_outcomes += 1
            if record.decision_correct:
                timeline.correct_predictions += 1

            # Recalculate accuracy
            if timeline.total_outcomes > 0:
                timeline.accuracy_pct = (timeline.correct_predictions / timeline.total_outcomes) * 100

            return record

    return None


def get_recommendation_history(
    timeline: HistoricalTimeline,
    days_back: int | None = None,
) -> list[DecisionRecord]:
    """Get recommendation history untuk satu ticker.

    Args:
        timeline: HistoricalTimeline
        days_back: Limit ke N hari terakhir (None = semua)

    Returns:
        List of DecisionRecord sorted chronologically
    """
    records = timeline.records.copy()

    if days_back:
        cutoff = datetime.now(timezone.utc) - __import__("datetime").timedelta(days=days_back)
        records = [r for r in records if datetime.fromisoformat(r.recommendation_date) >= cutoff]

    return sorted(records, key=lambda r: r.recommendation_date)


def calculate_recommendation_confidence_trend(
    timeline: HistoricalTimeline,
) -> dict:
    """Calculate trend dalam conviction over time.

    Args:
        timeline: HistoricalTimeline

    Returns:
        Dict dengan trend analysis
    """
    if len(timeline.records) < 2:
        return {"trend": "insufficient_history"}

    recent = timeline.records[-5:] if len(timeline.records) >= 5 else timeline.records
    avg_conviction = sum(r.conviction for r in recent) / len(recent)

    old_conviction = timeline.records[0].conviction if timeline.records else 50
    conviction_delta = avg_conviction - old_conviction

    trend = "increasing" if conviction_delta > 5 else ("decreasing" if conviction_delta < -5 else "stable")

    return {
        "ticker": timeline.ticker,
        "trend": trend,
        "conviction_delta": round(conviction_delta, 1),
        "recent_avg_conviction": round(avg_conviction, 1),
        "first_conviction": old_conviction,
        "recommendation_count": len(timeline.records),
    }
