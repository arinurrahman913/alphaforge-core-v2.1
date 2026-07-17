"""Fetch fundamental data & institutional ownership dari Yahoo Finance.

Evidence stage (Layer 2) menyukai detail — ringkasan lengkap dari Yahoo fast_info
& balance sheet dasar. Lihat 03_LAYER2_SPECS/02_EVIDENCE.md §1.1-1.2.
"""
from __future__ import annotations

from datetime import datetime, timezone
import yfinance as yf
from ..contracts import SourceMetadata, PriceMarketData, FundamentalData, InstitutionalOwnership


def fetch_price_market_data(ticker: str) -> PriceMarketData:
    """Ambil harga & data pasar dari Yahoo Finance."""
    try:
        t = yf.Ticker(ticker)

        # Harga terkini & OHLCV hari terakhir
        fi = t.fast_info
        hist = t.history(period="1d")

        last_price = fi.get("lastPrice") or (hist["Close"].iloc[-1] if not hist.empty else None)
        market_cap = fi.get("marketCap")
        shares_outstanding = fi.get("shares")
        beta = fi.get("beta")

        # OHLCV dari bar terakhir
        open_price = float(hist["Open"].iloc[-1]) if not hist.empty else None
        high = float(hist["High"].iloc[-1]) if not hist.empty else None
        low = float(hist["Low"].iloc[-1]) if not hist.empty else None
        close = float(hist["Close"].iloc[-1]) if not hist.empty else None
        volume = int(hist["Volume"].iloc[-1]) if not hist.empty else None

        metadata = SourceMetadata(
            source="yahoo_finance",
            fetched_at=datetime.now(timezone.utc).isoformat(),
            status="ok"
        )

        return PriceMarketData(
            last_price=last_price,
            open=open_price,
            high=high,
            low=low,
            close=close,
            volume=volume,
            market_cap=market_cap,
            shares_outstanding=shares_outstanding,
            beta=beta,
            metadata=metadata
        )
    except Exception as e:
        metadata = SourceMetadata(
            source="yahoo_finance",
            fetched_at=datetime.now(timezone.utc).isoformat(),
            status="missing"
        )
        return PriceMarketData(
            last_price=None, open=None, high=None, low=None, close=None,
            volume=None, market_cap=None, shares_outstanding=None, beta=None,
            metadata=metadata
        )


def fetch_fundamental_data(ticker: str) -> FundamentalData:
    """Ambil fundamental ringkas dari Yahoo Finance."""
    try:
        t = yf.Ticker(ticker)
        info = t.info

        metadata = SourceMetadata(
            source="yahoo_finance",
            fetched_at=datetime.now(timezone.utc).isoformat(),
            status="ok"
        )

        return FundamentalData(
            revenue=info.get("totalRevenue"),
            net_income=info.get("netIncomeToCommon"),
            eps=info.get("trailingEps"),
            pe_ratio=info.get("trailingPE"),
            debt_to_equity=info.get("debtToEquity"),
            current_ratio=info.get("currentRatio"),
            roe=info.get("returnOnEquity"),
            operating_margin=info.get("operatingMargins"),
            metadata=metadata
        )
    except Exception as e:
        metadata = SourceMetadata(
            source="yahoo_finance",
            fetched_at=datetime.now(timezone.utc).isoformat(),
            status="missing"
        )
        return FundamentalData(
            revenue=None, net_income=None, eps=None, pe_ratio=None,
            debt_to_equity=None, current_ratio=None, roe=None,
            operating_margin=None, metadata=metadata
        )


def fetch_institutional_ownership(ticker: str) -> InstitutionalOwnership:
    """Ambil persentase kepemilikan institusional dari Yahoo Finance."""
    try:
        t = yf.Ticker(ticker)
        info = t.info

        percentage = info.get("heldPercentInstitutions")

        metadata = SourceMetadata(
            source="yahoo_finance",
            fetched_at=datetime.now(timezone.utc).isoformat(),
            status="ok" if percentage is not None else "missing"
        )

        return InstitutionalOwnership(
            percentage=percentage,
            metadata=metadata
        )
    except Exception as e:
        metadata = SourceMetadata(
            source="yahoo_finance",
            fetched_at=datetime.now(timezone.utc).isoformat(),
            status="missing"
        )
        return InstitutionalOwnership(
            percentage=None,
            metadata=metadata
        )
