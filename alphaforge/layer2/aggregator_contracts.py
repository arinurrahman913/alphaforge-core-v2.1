"""Aggregator module contracts — Layer 2 Fase B, stage 5 (final)

Kombinasi output dari semua 6 stages:
Evidence → Knowledge → Peer → Confidence → Risk → Reasoning → Final Recommendation
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal


@dataclass
class FinalRecommendation:
    """Final output dari AlphaForge v2 pipeline."""
    ticker: str
    exchange: str

    # Final decision
    recommendation: Literal["strong_buy", "buy", "hold", "sell", "strong_sell"]
    conviction: float  # 0-100: confidence in recommendation
    reasoning_summary: str  # Brief explanation

    # Aggregated scores from stages
    confidence_score: float  # 0-100: data quality
    risk_score: float  # 0-100: risk level
    reasoning_score: float  # 0-100: fundamental quality + growth + momentum

    # Key thesis
    bull_case: str  # Bullish arguments
    bear_case: str  # Bearish arguments
    key_catalysts: list[str] = field(default_factory=list)  # Upcoming events/changes

    # Peer context
    peer_group_size: int = 0
    percentile_vs_peer: float | None = None  # E.g. 75th percentile on valuation

    # Risk factors
    red_flags: list[str] = field(default_factory=list)  # Top 3 risk factors
    data_quality_notes: str = ""  # Whether data is sufficient for decision

    # Recommendation tracking (for historical)
    recommended_at: str = ""  # ISO datetime
    next_review_date: str = ""  # When to reassess
    tracking_id: str = ""  # UUID untuk historical tracking

    def to_dict(self) -> dict:
        from dataclasses import asdict
        return asdict(self)
