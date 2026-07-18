"""Bentuk output Screening & Evidence — 03_LAYER2_SPECS/."""
from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Literal
from datetime import datetime

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


@dataclass
class SourceMetadata:
    """Metadata untuk tracking provenance + completeness."""
    source: str  # "yahoo_finance", "sec_edgar", "finnhub", dll
    fetched_at: str  # ISO datetime string
    status: Literal["ok", "missing", "degraded"]  # ok=lengkap, missing=gagal fetch, degraded=partial


@dataclass
class PriceBar:
    """Satu bar OHLCV."""
    date: str  # ISO date
    open: float
    high: float
    low: float
    close: float
    volume: int


@dataclass
class PriceMarketData:
    metadata: SourceMetadata
    last_price: float | None = None
    open: float | None = None
    high: float | None = None
    low: float | None = None
    close: float | None = None
    volume: int | None = None
    market_cap: float | None = None
    shares_outstanding: int | None = None
    beta: float | None = None
    high_52w: float | None = None
    low_52w: float | None = None
    price_history: list[PriceBar] = field(default_factory=list)  # 1-year daily OHLCV


@dataclass
class QuarterlyFundamental:
    """Satu quarter fundamental data dari SEC EDGAR 10-K/10-Q."""
    period: str  # '2024-Q1' atau '2024-09-30'
    revenue: float | None = None
    gross_profit: float | None = None
    operating_income: float | None = None
    net_income: float | None = None
    cash_from_operations: float | None = None
    capital_expenditures: float | None = None
    fiscal_date: str | None = None  # ISO date end of period


@dataclass
class FundamentalData:
    """Ringkasan fundamental dari Yahoo Finance + quarterly dari SEC EDGAR."""
    metadata: SourceMetadata
    revenue: float | None = None
    net_income: float | None = None
    eps: float | None = None
    pe_ratio: float | None = None
    debt_to_equity: float | None = None
    current_ratio: float | None = None
    quick_ratio: float | None = None
    roe: float | None = None
    roa: float | None = None
    operating_margin: float | None = None
    gross_margin: float | None = None
    free_cash_flow: float | None = None
    dividend_yield: float | None = None
    payout_ratio: float | None = None
    book_value_per_share: float | None = None
    asset_turnover: float | None = None
    inventory_turnover: float | None = None
    interest_coverage: float | None = None
    sector: str | None = None
    industry: str | None = None
    quarterly_data: list[QuarterlyFundamental] = field(default_factory=list)  # Last 8 quarters dari EDGAR


@dataclass
class InstitutionalOwnership:
    """Kepemilikan institusional."""
    metadata: SourceMetadata
    percentage: float | None = None  # persentase agregat dari Yahoo


@dataclass
class CompanyNews:
    """Satu berita perusahaan."""
    headline: str
    source: str
    published_at: str  # ISO datetime
    url: str | None


@dataclass
class NewsCollection:
    """Kumpulan berita terkini."""
    news: list[CompanyNews] = field(default_factory=list)
    metadata: SourceMetadata | None = None


@dataclass
class SecFiling:
    """Ringkasan satu SEC filing."""
    form_type: str  # "10-K", "10-Q", "8-K", dll
    filing_date: str  # ISO date
    url: str | None


@dataclass
class SecFilings:
    """Daftar SEC filings terkini."""
    filings: list[SecFiling] = field(default_factory=list)
    metadata: SourceMetadata | None = None


@dataclass
class EvidencePackage:
    """Fakta terverifikasi per satu ticker — 03_LAYER2_SPECS/02_EVIDENCE.md."""
    ticker: str
    exchange: Exchange
    price_market: PriceMarketData
    fundamental: FundamentalData
    institutional_ownership: InstitutionalOwnership
    news: NewsCollection
    sec_filings: SecFilings
    generated_at: str

    def to_dict(self) -> dict:
        return {
            "ticker": self.ticker,
            "exchange": self.exchange,
            "price_market": asdict(self.price_market),
            "fundamental": asdict(self.fundamental),
            "institutional_ownership": asdict(self.institutional_ownership),
            "news": {
                "count": len(self.news.news),
                "items": [asdict(n) for n in self.news.news],
                "metadata": asdict(self.news.metadata) if self.news.metadata else None,
            },
            "sec_filings": {
                "count": len(self.sec_filings.filings),
                "items": [asdict(f) for f in self.sec_filings.filings],
                "metadata": asdict(self.sec_filings.metadata) if self.sec_filings.metadata else None,
            },
            "generated_at": self.generated_at,
        }
