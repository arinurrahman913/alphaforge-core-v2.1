"""Aggregator module — Layer 2 Fase B, stage 5: Final Recommendation

Kombinasi 6 stages menjadi actionable recommendation + tracking.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone
from typing import TYPE_CHECKING

from .aggregator_contracts import FinalRecommendation

if TYPE_CHECKING:
    from .confidence_contracts import ConfidenceScore
    from .knowledge_contracts import KnowledgeProfile
    from .peer_contracts import PeerComparisonResult
    from .reasoning_contracts import AggregatedReasoning
    from .risk_contracts import RiskAssessment


def aggregate_recommendation(
    ticker: str,
    exchange: str,
    knowledge: KnowledgeProfile | None = None,
    peer: PeerComparisonResult | None = None,
    confidence: ConfidenceScore | None = None,
    risk: RiskAssessment | None = None,
    reasoning: AggregatedReasoning | None = None,
) -> FinalRecommendation:
    """Aggregate all outputs menjadi final recommendation.

    Args:
        ticker: Stock ticker
        exchange: Exchange
        knowledge: KnowledgeProfile dari Fase A
        peer: PeerComparisonResult dari Fase B-1
        confidence: ConfidenceScore dari Fase B-2
        risk: RiskAssessment dari Fase B-3
        reasoning: AggregatedReasoning dari Fase B-4

    Returns:
        FinalRecommendation dengan stance + conviction
    """
    # Extract base scores
    confidence_score = confidence.overall_confidence if confidence else 50.0
    risk_score = 100 - (risk.risk_score if risk else 50.0)  # Invert: lower risk = higher score
    reasoning_score = reasoning.final_score if reasoning else 50.0

    # Weighted aggregate
    final_score = (
        confidence_score * 0.20 +  # Data quality matters less than analysis
        risk_score * 0.25 +  # Risk adjustment important
        reasoning_score * 0.55  # Reasoning is main driver
    )

    # Recommendation stance
    if final_score >= 75:
        stance = "strong_buy"
        conviction = min(95, (final_score - 75) / 25 * 20 + 80)
    elif final_score >= 60:
        stance = "buy"
        conviction = (final_score - 60) / 15 * 15 + 65
    elif final_score >= 40:
        stance = "hold"
        conviction = 50
    elif final_score >= 25:
        stance = "sell"
        conviction = (40 - final_score) / 15 * 15 + 65
    else:
        stance = "strong_sell"
        conviction = min(95, (25 - final_score) / 25 * 20 + 80)

    # Build bull/bear case
    bull_parts = []
    bear_parts = []

    if reasoning and reasoning.quality_output:
        if "strong_buy" in reasoning.quality_output.stance or "buy" in reasoning.quality_output.stance:
            bull_parts.append("Strong fundamentals" if reasoning.quality_output.positive_factors else "Fundamentals acceptable")
        else:
            bear_parts.append("Fundamental weakness")

    if reasoning and reasoning.multibagger_output:
        if "strong_buy" in reasoning.multibagger_output.stance or "buy" in reasoning.multibagger_output.stance:
            bull_parts.append("High growth potential")
        if reasoning.multibagger_output.negative_factors:
            for factor in reasoning.multibagger_output.negative_factors[:1]:
                bear_parts.append(factor)

    if risk and risk.high_severity_count > 0:
        bear_parts.append(f"High-risk issues detected")

    if confidence and confidence.confidence_rating == "low":
        bear_parts.append("Insufficient data for conviction")

    bull_case = " • ".join(bull_parts) if bull_parts else "Mixed signals"
    bear_case = " • ".join(bear_parts) if bear_parts else "No major issues identified"

    # Red flags
    red_flags = []
    if risk:
        for flag in risk.red_flags[:3]:
            red_flags.append(f"{flag.flag_type}: {flag.description}")

    if confidence and confidence.incomplete_fundamentals:
        red_flags.append("Incomplete fundamental data")

    # Peer percentile
    percentile = None
    peer_group_size = peer.peer_group.group_size if peer else 0

    # Data quality notes
    quality_notes_parts = []
    if confidence:
        if confidence.overall_confidence < 40:
            quality_notes_parts.append(f"Low data confidence ({confidence.overall_confidence}%)")
        if confidence.insufficient_price_history:
            quality_notes_parts.append("Limited price history")
        if confidence.missing_recent_data:
            quality_notes_parts.append("Data >30 days old")

    data_quality_notes = " • ".join(quality_notes_parts) if quality_notes_parts else "Sufficient data quality"

    # Tracking ID and dates
    tracking_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc)
    review_date = now + timedelta(days=30)

    # Summary
    reasoning_summary = ""
    if reasoning:
        reasoning_summary = reasoning.recommendation
    else:
        reasoning_summary = f"{stance.replace('_', ' ').title()} based on available data"

    return FinalRecommendation(
        ticker=ticker,
        exchange=exchange,
        recommendation=stance,
        conviction=round(conviction, 0),
        reasoning_summary=reasoning_summary,
        confidence_score=round(confidence_score, 1),
        risk_score=round(risk_score, 1),
        reasoning_score=round(reasoning_score, 1),
        bull_case=bull_case,
        bear_case=bear_case,
        key_catalysts=[],  # TODO: extract from guidance_trend, acceleration signals
        peer_group_size=peer_group_size,
        percentile_vs_peer=percentile,
        red_flags=red_flags,
        data_quality_notes=data_quality_notes,
        recommended_at=now.isoformat(),
        next_review_date=review_date.isoformat(),
        tracking_id=tracking_id,
    )


def run_aggregator(
    profiles: list[KnowledgeProfile],
    peers: list[PeerComparisonResult] | None = None,
    confidences: list[ConfidenceScore] | None = None,
    risks: list[RiskAssessment] | None = None,
    reasonings: list[AggregatedReasoning] | None = None,
) -> list[FinalRecommendation]:
    """Run aggregator untuk semua profiles.

    Args:
        profiles: List of KnowledgeProfile
        peers: List of PeerComparisonResult (optional)
        confidences: List of ConfidenceScore (optional)
        risks: List of RiskAssessment (optional)
        reasonings: List of AggregatedReasoning (optional)

    Returns:
        List of FinalRecommendation
    """
    # Build lookup maps
    peer_map = {}
    if peers:
        for peer in peers:
            peer_map[peer.ticker] = peer

    confidence_map = {}
    if confidences:
        for conf in confidences:
            confidence_map[conf.ticker] = conf

    risk_map = {}
    if risks:
        for risk in risks:
            risk_map[risk.ticker] = risk

    reasoning_map = {}
    if reasonings:
        for reasoning in reasonings:
            reasoning_map[reasoning.ticker] = reasoning

    # Aggregate each profile
    recommendations = []
    for profile in profiles:
        rec = aggregate_recommendation(
            ticker=profile.ticker,
            exchange=profile.exchange,
            knowledge=profile,
            peer=peer_map.get(profile.ticker),
            confidence=confidence_map.get(profile.ticker),
            risk=risk_map.get(profile.ticker),
            reasoning=reasoning_map.get(profile.ticker),
        )
        recommendations.append(rec)

    return recommendations
