"""Risk & Red-Flag module contracts — Layer 2 Fase B, stage 3

Deteksi anomali dan warning signs:
- Governance anomalies (auditor changes, restatements, litigation)
- Financial extremes (margins, debt levels, valuation)
- Momentum reversals (guidance misses, earnings streak breaks)
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal


@dataclass
class RedFlag:
    """Satu warning sign yang terdeteksi."""
    flag_type: Literal[
        "auditor_change", "restatement", "litigation", "unusual_filing",
        "high_debt", "low_liquidity", "declining_margin", "negative_fcf",
        "valuation_extreme", "severe_drawdown",
        "guidance_miss", "earnings_streak_break", "high_volatility"
    ]
    severity: Literal["high", "medium", "low"]  # Risk level
    description: str  # Penjelasan flag
    context: str | None = None  # Detail konteks
    affected_metrics: list[str] = field(default_factory=list)  # Metrik yang terdampak


@dataclass
class RiskAssessment:
    """Risk & Red-Flag assessment untuk satu ticker — Fase B output.

    Mengidentifikasi warning signs yang perlu dipertimbangkan dalam reasoning.
    """
    ticker: str
    exchange: str

    # Overall risk
    risk_score: float  # 0-100: 0=low risk, 100=high risk
    risk_rating: Literal["low", "medium", "high", "critical"]  # Kategorisasi

    # Risk categories
    governance_risk_score: float  # 0-100
    financial_risk_score: float  # 0-100
    momentum_risk_score: float  # 0-100
    valuation_risk_score: float  # 0-100

    # Detected flags
    red_flags: list[RedFlag] = field(default_factory=list)
    high_severity_count: int = 0  # Jumlah high-severity flags
    medium_severity_count: int = 0  # Jumlah medium-severity flags
    low_severity_count: int = 0  # Jumlah low-severity flags

    # Risk summary
    risk_notes: str = ""  # Catatan risk
    recommended_risk_adjustment: float = 0.0  # -0.3 to +0.3 adjustment untuk confidence

    # Metadata
    assessed_at: str = ""  # ISO datetime

    def to_dict(self) -> dict:
        from dataclasses import asdict
        return asdict(self)
