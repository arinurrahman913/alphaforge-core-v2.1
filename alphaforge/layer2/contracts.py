"""Bentuk output Screening — 03_LAYER2_SPECS/01_SCREENING.md."""
from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Literal

Exchange = Literal["NASDAQ", "NYSE"]


@dataclass
class ListingRow:
    symbol: str
    security_name: str
    exchange: Exchange
    is_etf: bool
    is_test_issue: bool


@dataclass
class ScreeningCandidate:
    ticker: str
    exchange: Exchange
    passed: bool
    hard_exclude_reason: str | None = None
    soft_flags: list[str] = field(default_factory=list)
    market_cap: float | None = None
    avg_dollar_volume_20d: float | None = None
    last_price: float | None = None
    price_history_days: int | None = None

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class ScreeningResult:
    universe_raw: int              # jumlah ticker mentah dari listing file
    universe_after_cheap_filter: int  # setelah exclude ETF/test issue/non-common-stock
    universe_scanned: int          # jumlah ticker yang benar-benar dicek (bisa dibatasi --limit)
    passed: list[ScreeningCandidate]
    hard_excluded: list[ScreeningCandidate]
    generated_at: str

    def to_dict(self) -> dict:
        return {
            "universe_raw": self.universe_raw,
            "universe_after_cheap_filter": self.universe_after_cheap_filter,
            "universe_scanned": self.universe_scanned,
            "passed_count": len(self.passed),
            "hard_excluded_count": len(self.hard_excluded),
            "generated_at": self.generated_at,
            "passed": [c.to_dict() for c in self.passed],
            "hard_excluded": [c.to_dict() for c in self.hard_excluded],
        }
