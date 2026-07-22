"""Aggregator module — Layer 2 Fase B, stage 5: Final Recommendation

Kombinasi 6 stages menjadi actionable recommendation + tracking.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone
from typing import TYPE_CHECKING

from .aggregator_contracts import FinalRecommendation

if TYPE_CHECKING:
    from .confidence_contracts import ConfidenceReport
    from .knowledge_contracts import KnowledgeProfile
    from .peer_contracts import PeerComparisonResult
    from .reasoning_contracts import ReasoningBundle
    from .risk_contracts import RiskAssessment

# INTERIM shim — dipakai cuma untuk mengisi FinalRecommendation.final_score/
# stance lama (D-04 sebenarnya MELARANG Aggregator punya skor tunggal macam
# ini sama sekali, lihat 11_AGGREGATOR_OUTPUT.md — belum dibongkar total di
# sini karena itu scope Fase 6/Synthesis, bukan Fase 4/reasoning). Urutan di
# dalam SATU kosakata modul memang sah dibandingkan (D-04: "Di dalam satu
# kosakata urutan tetap ada... satu lensa, satu sumbu") — yang tidak sah itu
# membandingkan ANTAR kosakata, dan pemetaan angka ini cuma dipakai untuk
# rata-rata sementara, bukan claim bahwa "ruang_terbuka" == "compounding_kuat".
_STANCE_ORDINAL = {
    "ruang_terbuka": 100, "ruang_sempit": 60, "ruang_tertutup": 20, "ruang_tak_terbaca": 50,
    "compounding_kuat": 100, "compounding_rapuh": 60, "bukan_compounder": 20, "mesin_tak_terbaca": 50,
    "asimetri_berkatalis": 100, "asimetri_tanpa_katalis": 70, "tanpa_asimetri": 30, "asimetri_tak_terbaca": 50,
}


def _reasoning_bundle_score(bundle: ReasoningBundle) -> float:
    values = [
        _STANCE_ORDINAL.get(bundle.quality_compound.stance, 50),
        _STANCE_ORDINAL.get(bundle.multibagger.stance, 50),
        _STANCE_ORDINAL.get(bundle.speculative.stance, 50),
    ]
    return sum(values) / len(values)


def aggregate_recommendation(
    ticker: str,
    exchange: str,
    knowledge: KnowledgeProfile | None = None,
    peer: PeerComparisonResult | None = None,
    confidence: ConfidenceReport | None = None,
    risk: RiskAssessment | None = None,
    reasoning: ReasoningBundle | None = None,
) -> FinalRecommendation:
    """Aggregate all outputs menjadi final recommendation.

    Args:
        ticker: Stock ticker
        exchange: Exchange
        knowledge: KnowledgeProfile dari Fase A
        peer: PeerComparisonResult dari Fase B-1
        confidence: ConfidenceReport dari Fase B-2
        risk: RiskAssessment dari Fase B-3
        reasoning: ReasoningBundle (3 ModuleOutput independen) dari Fase B-4

    Returns:
        FinalRecommendation dengan stance + conviction
    """
    # Extract base scores
    confidence_score = confidence.overall.score if confidence else 50.0
    risk_score = 100 - (risk.risk_score if risk else 50.0)  # Invert: lower risk = higher score
    reasoning_score = _reasoning_bundle_score(reasoning) if reasoning else 50.0

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
        # Was a flat 50 for the entire 40-60 band, so ~70% of tickers (the
        # ones landing in "hold", the widest band) showed an identical
        # conviction regardless of how decisively neutral they actually
        # were. Mirror the buy/sell bands instead: conviction is lowest
        # (50) at the dead center (final_score=50, truly undecided) and
        # rises toward 65 at either edge — continuous with buy's 65 at
        # final_score=60 and sell's 65 at final_score=40.
        distance_from_center = abs(final_score - 50)  # 0..10
        conviction = 50 + (distance_from_center / 10) * 15
    elif final_score >= 25:
        stance = "sell"
        conviction = (40 - final_score) / 15 * 15 + 65
    else:
        stance = "strong_sell"
        conviction = min(95, (25 - final_score) / 25 * 20 + 80)

    # Build bull/bear case
    bull_parts = []
    bear_parts = []

    if reasoning:
        if reasoning.quality_compound.stance == "compounding_kuat":
            bull_parts.append("Strong fundamentals" if reasoning.quality_compound.positive_factors else "Fundamentals acceptable")
        elif reasoning.quality_compound.stance == "bukan_compounder":
            bear_parts.append("Fundamental weakness")

        if reasoning.multibagger.stance == "ruang_terbuka":
            bull_parts.append("High growth potential")
        if reasoning.multibagger.negative_factors:
            for factor in reasoning.multibagger.negative_factors[:1]:
                bear_parts.append(factor)

    if risk and risk.high_severity_count > 0:
        bear_parts.append(f"High-risk issues detected")

    if confidence and confidence.overall.band == "low":
        bear_parts.append("Insufficient data for conviction")

    bull_case = " • ".join(bull_parts) if bull_parts else "Mixed signals"
    bear_case = " • ".join(bear_parts) if bear_parts else "No major issues identified"

    # Red flags
    red_flags = []
    if risk:
        for flag in risk.red_flags[:3]:
            red_flags.append(f"{flag.flag_type}: {flag.description}")

    if confidence and confidence.by_section["financial_health"].score < 50:
        red_flags.append("Incomplete fundamental data")

    # Peer percentile
    percentile = None
    peer_group_size = peer.peer_group.group_size if peer else 0

    # Data quality notes — ConfidenceReport.overall.limiters sudah membawa
    # alasan yang sama persis (section lemah, peer/context penalty, data
    # basi), jadi tinggal dipakai langsung, bukan dihitung ulang di sini.
    quality_notes_parts = []
    if confidence:
        quality_notes_parts.extend(confidence.overall.limiters)
    else:
        # Confidence stage never ran for this ticker (partial/degraded
        # pipeline run) — confidence_score above silently defaulted to a
        # neutral 50, which otherwise looks identical to a genuinely
        # assessed medium confidence. Surface the distinction instead of
        # letting it read as "checked, and fine".
        quality_notes_parts.append("Confidence assessment unavailable (stage skipped)")

    if risk is None:
        # Same issue: risk_score defaulted to the neutral midpoint (100-50)
        # above and high_severity_count-driven bear_case/red_flags checks
        # were silently skipped — this ticker was never actually screened
        # for red flags, it's not that none were found.
        quality_notes_parts.append("Risk assessment unavailable (stage skipped)")

    if reasoning is None:
        # reasoning_score defaulted to neutral 50 and carries the largest
        # weight (55%) in final_score — a "hold" driven by this default
        # should not look the same as a "hold" the reasoning modules
        # actually concluded.
        quality_notes_parts.append("Reasoning unavailable (stage skipped)")

    data_quality_notes = " • ".join(quality_notes_parts) if quality_notes_parts else "Sufficient data quality"

    # Tracking ID and dates
    tracking_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc)
    review_date = now + timedelta(days=30)

    # Summary — 3 lens punya kosakata stance sendiri-sendiri (D-09), jadi gak
    # ada satu "reasoning.recommendation" gabungan lagi seperti versi lama.
    if reasoning:
        reasoning_summary = (
            f"Quality: {reasoning.quality_compound.stance} · "
            f"Multibagger: {reasoning.multibagger.stance} · "
            f"Speculative: {reasoning.speculative.stance}"
        )
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
    confidences: list[ConfidenceReport] | None = None,
    risks: list[RiskAssessment] | None = None,
    reasonings: list[ReasoningBundle] | None = None,
) -> list[FinalRecommendation]:
    """Run aggregator untuk semua profiles.

    Args:
        profiles: List of KnowledgeProfile
        peers: List of PeerComparisonResult (optional)
        confidences: List of ConfidenceReport (optional)
        risks: List of RiskAssessment (optional)
        reasonings: List of ReasoningBundle (optional)

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
