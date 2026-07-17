"""Confidence module contracts — Layer 2 Fase B, stage 2: Data Quality Scoring

Setiap KnowledgeProfile dievaluasi untuk confidence level berdasarkan:
- Field completeness (berapa persen field terisi)
- Data freshness (kapan terakhir diupdate)
- Peer group quality (sample size, data availability)
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal


@dataclass
class DataQualityScore:
    """Skor kualitas data per kategori."""
    category: str  # "price", "fundamentals", "ownership", "news", "peer_group"
    field_count: int  # Berapa field di-scan
    field_completed: int  # Berapa field terisi
    completion_pct: float  # 0-100
    data_age_days: int | None  # Berapa hari lalu data terakhir diupdate


@dataclass
class ConfidenceScore:
    """Confidence assessment untuk satu ticker — Fase B output.

    Mengukur seberapa terpercaya (dan siap untuk reasoning) Knowledge profile ini.
    """
    ticker: str
    exchange: str

    # Overall confidence
    overall_confidence: float  # 0-100, weighted average
    confidence_rating: Literal["high", "medium", "low"]  # Kategorisasi

    # Breakdown by data category
    price_data_confidence: float  # 0-100
    fundamental_data_confidence: float  # 0-100
    ownership_data_confidence: float  # 0-100
    news_data_confidence: float  # 0-100
    governance_data_confidence: float  # 0-100
    peer_group_confidence: float  # 0-100

    # Flags (non-default)
    low_sample_size_peer: bool  # Peer group < 3
    insufficient_price_history: bool  # Price history < 200 days
    missing_recent_data: bool  # Data > 30 hari lalu
    incomplete_fundamentals: bool  # < 50% fundamental fields

    # Detailed scores (with default)
    quality_scores: list[DataQualityScore] = field(default_factory=list)

    # Notes for downstream stages
    confidence_notes: str = ""  # Catatan kualitas data

    # Metadata
    assessed_at: str = ""  # ISO datetime

    def to_dict(self) -> dict:
        from dataclasses import asdict
        return asdict(self)
