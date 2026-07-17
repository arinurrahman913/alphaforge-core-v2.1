"""Confidence module — Layer 2 Fase B, stage 2: Data Quality Scoring.

Menilai confidence level setiap Knowledge profile untuk downstream reasoning stages.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import TYPE_CHECKING

from .confidence_contracts import ConfidenceScore, DataQualityScore

if TYPE_CHECKING:
    from .knowledge_contracts import KnowledgeProfile
    from .peer_contracts import PeerComparisonResult


def assess_confidence(
    knowledge_profile: KnowledgeProfile,
    peer_comparison: PeerComparisonResult | None = None,
) -> ConfidenceScore:
    """Assess confidence level untuk satu Knowledge profile.

    Args:
        knowledge_profile: KnowledgeProfile dari Fase A
        peer_comparison: PeerComparisonResult dari Fase B stage 1 (optional)

    Returns:
        ConfidenceScore dengan breakdown per kategori
    """
    ticker = knowledge_profile.ticker
    exchange = knowledge_profile.exchange

    # Score masing-masing kategori
    price_score = _score_price_data(knowledge_profile)
    fundamental_score = _score_fundamental_data(knowledge_profile)
    ownership_score = _score_ownership_data(knowledge_profile)
    news_score = _score_news_data(knowledge_profile)
    governance_score = _score_governance_data(knowledge_profile)
    peer_score = _score_peer_group(peer_comparison)

    # Weighted average untuk overall confidence
    weights = {
        "price": 0.25,
        "fundamentals": 0.30,
        "ownership": 0.15,
        "news": 0.10,
        "governance": 0.10,
        "peer_group": 0.10,
    }

    overall = (
        price_score * weights["price"]
        + fundamental_score * weights["fundamentals"]
        + ownership_score * weights["ownership"]
        + news_score * weights["news"]
        + governance_score * weights["governance"]
        + peer_score * weights["peer_group"]
    )

    # Rating
    if overall >= 70:
        rating = "high"
    elif overall >= 40:
        rating = "medium"
    else:
        rating = "low"

    # Flags
    low_sample_peer = peer_comparison and peer_comparison.peer_group.group_size < 3
    insufficient_price = len(knowledge_profile.metadata.evidence_date or "") == 0 or price_score < 50
    missing_recent = knowledge_profile.metadata.evidence_date and _is_data_stale(
        knowledge_profile.metadata.evidence_date, days=30
    )
    incomplete_fundamentals = (
        knowledge_profile.metadata.fields_completed / knowledge_profile.metadata.fields_expected < 0.5
    )

    # Notes
    notes_parts = []
    if low_sample_peer:
        notes_parts.append("Peer group sample size too small (<3)")
    if insufficient_price:
        notes_parts.append("Limited price history")
    if missing_recent:
        notes_parts.append("Data > 30 days old")
    if incomplete_fundamentals:
        notes_parts.append(
            f"Low fundamental completeness ({knowledge_profile.metadata.fields_completed}/{knowledge_profile.metadata.fields_expected})"
        )

    confidence_notes = " | ".join(notes_parts) if notes_parts else "Sufficient data for reasoning"

    # Quality scores breakdown
    quality_scores = [
        DataQualityScore(
            category="price",
            field_count=5,  # return_1y, return_3y, return_5y, volatility, beta
            field_completed=_count_price_fields(knowledge_profile),
            completion_pct=price_score,
            data_age_days=_get_data_age_days(knowledge_profile.metadata.evidence_date),
        ),
        DataQualityScore(
            category="fundamentals",
            field_count=18,
            field_completed=_count_fundamental_fields(knowledge_profile),
            completion_pct=fundamental_score,
            data_age_days=_get_data_age_days(knowledge_profile.metadata.evidence_date),
        ),
        DataQualityScore(
            category="ownership",
            field_count=3,  # institutional, insider, transactions
            field_completed=_count_ownership_fields(knowledge_profile),
            completion_pct=ownership_score,
            data_age_days=_get_data_age_days(knowledge_profile.metadata.evidence_date),
        ),
        DataQualityScore(
            category="news",
            field_count=1,  # news_collection
            field_completed=1 if knowledge_profile.metadata.data_quality_notes else 0,
            completion_pct=news_score,
            data_age_days=_get_data_age_days(knowledge_profile.metadata.evidence_date),
        ),
        DataQualityScore(
            category="governance",
            field_count=5,  # shares_change, auditor_changes, restatements, litigation, filings
            field_completed=_count_governance_fields(knowledge_profile),
            completion_pct=governance_score,
            data_age_days=_get_data_age_days(knowledge_profile.metadata.evidence_date),
        ),
    ]

    return ConfidenceScore(
        ticker=ticker,
        exchange=exchange,
        overall_confidence=round(overall, 1),
        confidence_rating=rating,
        price_data_confidence=round(price_score, 1),
        fundamental_data_confidence=round(fundamental_score, 1),
        ownership_data_confidence=round(ownership_score, 1),
        news_data_confidence=round(news_score, 1),
        governance_data_confidence=round(governance_score, 1),
        peer_group_confidence=round(peer_score, 1),
        quality_scores=quality_scores,
        low_sample_size_peer=bool(low_sample_peer),
        insufficient_price_history=insufficient_price,
        missing_recent_data=bool(missing_recent),
        incomplete_fundamentals=incomplete_fundamentals,
        confidence_notes=confidence_notes,
        assessed_at=datetime.now(timezone.utc).isoformat(),
    )


def _score_price_data(profile: KnowledgeProfile) -> float:
    """Score harga/trend data (returns, volatility, beta)."""
    ht = profile.historical_trend
    score = 0.0
    count = 0

    if ht.return_1y is not None:
        score += 25
    count += 25

    if ht.return_3y is not None:
        score += 20
    count += 20

    if ht.return_5y is not None:
        score += 20
    count += 20

    if ht.volatility_daily is not None:
        score += 20
    count += 20

    if ht.beta is not None:
        score += 15
    count += 15

    return (score / count * 100) if count > 0 else 0.0


def _score_fundamental_data(profile: KnowledgeProfile) -> float:
    """Score financial data completeness."""
    fh = profile.financial_health
    val = profile.valuation
    score = 0.0
    count = 0

    # Balance sheet
    if fh.balance_sheet.current_ratio is not None:
        score += 5
    count += 5

    if fh.balance_sheet.debt_to_equity is not None:
        score += 5
    count += 5

    # Cash flow
    if fh.cash_flow_trend.fcf_q4 is not None:
        score += 8
    count += 8

    # Margins
    if fh.net_margin_trend.q4 is not None:
        score += 5
    count += 5

    # Valuation
    if val.pe_ratio_trailing is not None:
        score += 8
    count += 8

    if val.ps_ratio is not None:
        score += 7
    count += 7

    if val.pb_ratio is not None:
        score += 7
    count += 7

    if val.fcf_yield is not None:
        score += 6
    count += 6

    # Revenue
    if profile.competitive_structure.total_revenue_ttm is not None:
        score += 8
    count += 8

    return (score / count * 100) if count > 0 else 0.0


def _score_ownership_data(profile: KnowledgeProfile) -> float:
    """Score ownership data completeness."""
    own = profile.ownership
    score = 0.0
    count = 0

    if own.institutional_pct is not None:
        score += 40
    count += 40

    if own.insider_pct is not None:
        score += 35
    count += 35

    if len(own.insider_transactions or []) > 0:
        score += 25
    count += 25

    return (score / count * 100) if count > 0 else 0.0


def _score_news_data(profile: KnowledgeProfile) -> float:
    """Score news/sentiment data availability."""
    # Fallback: check if news was attempted
    if "No news data" in (profile.metadata.data_quality_notes or ""):
        return 0.0
    elif "news" in (profile.metadata.sources_used or []):
        return 70.0  # News data available
    else:
        return 30.0  # Attempted but limited


def _score_governance_data(profile: KnowledgeProfile) -> float:
    """Score governance data completeness."""
    gov = profile.governance
    score = 0.0
    count = 0

    if gov.shares_outstanding_change_12m is not None:
        score += 25
    count += 25

    if len(gov.auditor_changes or []) >= 0:
        score += 15
    count += 15

    if len(gov.restatements or []) >= 0:
        score += 20
    count += 20

    if len(gov.material_litigation or []) >= 0:
        score += 20
    count += 20

    if len(gov.unusual_filings or []) >= 0:
        score += 20
    count += 20

    return (score / count * 100) if count > 0 else 50.0  # Governance assumed ok if no data


def _score_peer_group(peer_comparison: PeerComparisonResult | None) -> float:
    """Score peer group quality."""
    if not peer_comparison:
        return 20.0  # No peer data yet

    group_size = peer_comparison.peer_group.group_size

    if group_size >= 10:
        return 100.0
    elif group_size >= 5:
        return 80.0
    elif group_size >= 3:
        return 60.0
    else:
        return 20.0  # Too small to be useful


def _count_price_fields(profile: KnowledgeProfile) -> int:
    """Count non-null price/trend fields."""
    ht = profile.historical_trend
    count = 0
    if ht.return_1y is not None:
        count += 1
    if ht.return_3y is not None:
        count += 1
    if ht.return_5y is not None:
        count += 1
    if ht.volatility_daily is not None:
        count += 1
    if ht.beta is not None:
        count += 1
    return count


def _count_fundamental_fields(profile: KnowledgeProfile) -> int:
    """Count non-null fundamental fields."""
    count = 0
    fh = profile.financial_health
    val = profile.valuation
    cs = profile.competitive_structure

    if fh.balance_sheet.current_ratio is not None:
        count += 1
    if fh.balance_sheet.debt_to_equity is not None:
        count += 1
    if fh.cash_flow_trend.fcf_q4 is not None:
        count += 1
    if fh.net_margin_trend.q4 is not None:
        count += 1
    if val.pe_ratio_trailing is not None:
        count += 1
    if val.ps_ratio is not None:
        count += 1
    if val.pb_ratio is not None:
        count += 1
    if val.fcf_yield is not None:
        count += 1
    if cs.total_revenue_ttm is not None:
        count += 1

    return count


def _count_ownership_fields(profile: KnowledgeProfile) -> int:
    """Count non-null ownership fields."""
    own = profile.ownership
    count = 0
    if own.institutional_pct is not None:
        count += 1
    if own.insider_pct is not None:
        count += 1
    if len(own.insider_transactions or []) > 0:
        count += 1
    return count


def _count_governance_fields(profile: KnowledgeProfile) -> int:
    """Count governance data points."""
    gov = profile.governance
    count = 4  # Assume auditor, restatements, litigation, filings tracked
    if gov.shares_outstanding_change_12m is not None:
        count += 1
    return count


def _is_data_stale(iso_datetime: str, days: int = 30) -> bool:
    """Check if ISO datetime is older than N days."""
    try:
        data_time = datetime.fromisoformat(iso_datetime.replace("+00:00", "+00:00"))
        now = datetime.now(timezone.utc)
        age = (now - data_time).days
        return age > days
    except (ValueError, AttributeError):
        return False


def _get_data_age_days(iso_datetime: str | None) -> int | None:
    """Get age of data in days."""
    if not iso_datetime:
        return None

    try:
        data_time = datetime.fromisoformat(iso_datetime.replace("+00:00", "+00:00"))
        now = datetime.now(timezone.utc)
        return (now - data_time).days
    except (ValueError, AttributeError):
        return None


def run_confidence(profiles: list[KnowledgeProfile], comparisons: list[PeerComparisonResult] | None = None) -> list[ConfidenceScore]:
    """Run confidence scoring untuk semua profiles.

    Args:
        profiles: List of KnowledgeProfile dari Fase A
        comparisons: List of PeerComparisonResult dari Fase B stage 1 (optional)

    Returns:
        List of ConfidenceScore
    """
    # Build lookup map untuk peer comparisons
    peer_map = {}
    if comparisons:
        for comp in comparisons:
            peer_map[comp.ticker] = comp

    scores = []
    for profile in profiles:
        peer_comp = peer_map.get(profile.ticker)
        score = assess_confidence(profile, peer_comp)
        scores.append(score)

    return scores
