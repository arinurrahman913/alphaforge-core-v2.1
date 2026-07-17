"""Historical tracking contracts — Layer 2 Fase B, stage 6 (post-pipeline)

Track recommendations over time untuk backtesting dan learning.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal


@dataclass
class DecisionRecord:
    """Satu recommendation record di waktu tertentu."""
    ticker: str
    recommendation: Literal["strong_buy", "buy", "hold", "sell", "strong_sell"]
    conviction: float  # 0-100
    recommendation_date: str  # ISO datetime
    reasoning_summary: str

    # Scores at decision time
    confidence_score: float
    risk_score: float
    reasoning_score: float

    # Context
    tracking_id: str  # UUID dari aggregator
    next_review_date: str

    # Outcome (filled in later)
    actual_return_pct: float | None = None  # Return antara recommendation_date dan outcome_date
    outcome_date: str | None = None  # Kapan outcome diukur
    decision_correct: bool | None = None  # Apakah prediction benar (buying + return > 0, dll)

    def to_dict(self) -> dict:
        from dataclasses import asdict
        return asdict(self)


@dataclass
class HistoricalTimeline:
    """Timeline of recommendations untuk satu ticker."""
    ticker: str
    total_recommendations: int = 0
    first_recommendation_date: str | None = None
    last_recommendation_date: str | None = None

    # Records (sorted chronologically)
    records: list[DecisionRecord] = field(default_factory=list)

    # Accuracy tracking
    correct_predictions: int = 0
    total_outcomes: int = 0
    accuracy_pct: float | None = None

    def to_dict(self) -> dict:
        from dataclasses import asdict
        d = asdict(self)
        return d
