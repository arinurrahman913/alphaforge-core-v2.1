"""Reasoning module contracts — Layer 2 Fase B, stage 4

3 reasoning lens dengan field access control berbeda:
- Quality: fundamental analysis (sections 1,2,3a,4,6,7)
- Speculative: technical + sentiment (sections 1,3a,4-volatility,5)
- Multibagger: growth + momentum (sections 1,3a,3b,4,6)

Masing-masing menghasilkan score + stance.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal


@dataclass
class ReasoningOutput:
    """Output dari satu reasoning lens."""
    lens_name: Literal["quality", "speculative", "multibagger"]
    ticker: str
    exchange: str

    # Score & stance
    conviction_score: float  # 0-100: confidence level
    stance: Literal["strong_buy", "buy", "hold", "sell", "strong_sell"]  # Positioning
    score_breakdown: dict[str, float] = field(default_factory=dict)  # Komponen-komponen score

    # Key factors
    positive_factors: list[str] = field(default_factory=list)  # Yang bullish
    negative_factors: list[str] = field(default_factory=list)  # Yang bearish
    key_metrics: dict[str, float | str] = field(default_factory=dict)  # Metrik yang dipakai

    # Notes
    reasoning_notes: str = ""  # Penjelasan stance

    # Metadata
    assessed_at: str = ""  # ISO datetime
    fields_accessed: list[str] = field(default_factory=list)  # Untuk audit field access

    def to_dict(self) -> dict:
        from dataclasses import asdict
        return asdict(self)


@dataclass
class AggregatedReasoning:
    """Hasil aggregasi 3 lens menjadi final recommendation."""
    ticker: str
    exchange: str

    # Aggregated score (non-default)
    final_score: float  # 0-100: weighted average of 3 lens
    final_stance: Literal["strong_buy", "buy", "hold", "sell", "strong_sell"]

    # Consensus (non-default)
    lens_agreement: float  # 0-100: berapa % lens setuju dgn final_stance
    divergence_level: Literal["high", "medium", "low"]  # Apakah ada perbedaan besar antar lens

    # Final recommendation (non-default)
    recommendation: str  # E.g. "Strong Buy (Quality bullish, Multibagger growth)"
    risk_adjusted_score: float  # Final score setelah risk adjustment

    # Individual lens outputs (with defaults)
    quality_output: ReasoningOutput | None = None
    speculative_output: ReasoningOutput | None = None
    multibagger_output: ReasoningOutput | None = None

    # Metadata
    aggregated_at: str = ""  # ISO datetime

    def to_dict(self) -> dict:
        from dataclasses import asdict
        return asdict(self)
