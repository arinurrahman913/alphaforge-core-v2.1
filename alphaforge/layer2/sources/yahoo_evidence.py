"""Fetch fundamental data & institutional ownership dari Yahoo Finance.

Evidence stage: lengkap dari Yahoo fast_info, extended historical OHLCV,
banyak fundamental fields. Dengan caching untuk performance.

Lihat 03_LAYER2_SPECS/02_EVIDENCE.md §1.1-1.2.
"""
from __future__ import annotations

import os
from datetime import datetime, timezone
import yfinance as yf
from ...cache import get as cache_get, set as cache_set
from ..contracts import (
    SourceMetadata, PriceMarketData, PriceBar, FundamentalData, InstitutionalOwnership
)

PRICE_CACHE_TTL = 6 * 3600  # 6 jam
FUNDAMENTAL_CACHE_TTL = 24 * 3600  # 24 jam
OWNERSHIP_CACHE_TTL = 24 * 3600  # 24 jam


def fetch_price_market_data(ticker: str) -> PriceMarketData:
    """Ambil harga & 1-year historical OHLCV dari Yahoo Finance."""
    try:
        t = yf.Ticker(ticker)
        fi = t.fast_info

        # Fetch 1-year history
        hist = t.history(period="1y")
        if hist is None or hist.empty:
            raise ValueError(f"no price data for {ticker}")

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

        # 52-week high/low
        high_52w = float(hist["High"].max()) if not hist.empty else None
        low_52w = float(hist["Low"].min()) if not hist.empty else None

        # Convert historical data ke PriceBar list
        price_history = []
        for idx, row in hist.iterrows():
            date_str = idx.strftime("%Y-%m-%d") if hasattr(idx, 'strftime') else str(idx)
            price_history.append(PriceBar(
                date=date_str,
                open=float(row["Open"]),
                high=float(row["High"]),
                low=float(row["Low"]),
                close=float(row["Close"]),
                volume=int(row["Volume"])
            ))

        metadata = SourceMetadata(
            source="yahoo_finance",
            fetched_at=datetime.now(timezone.utc).isoformat(),
            status="ok"
        )

        return PriceMarketData(
            metadata=metadata,
            last_price=last_price,
            open=open_price,
            high=high,
            low=low,
            close=close,
            volume=volume,
            market_cap=market_cap,
            shares_outstanding=shares_outstanding,
            beta=beta,
            high_52w=high_52w,
            low_52w=low_52w,
            price_history=price_history
        )
    except Exception as e:
        metadata = SourceMetadata(
            source="yahoo_finance",
            fetched_at=datetime.now(timezone.utc).isoformat(),
            status="missing"
        )
        return PriceMarketData(
            metadata=metadata,
            last_price=None, open=None, high=None, low=None, close=None,
            volume=None, market_cap=None, shares_outstanding=None, beta=None,
            high_52w=None, low_52w=None, price_history=[]
        )


def fetch_fundamental_data(ticker: str) -> FundamentalData:
    """Ambil fundamental lengkap dari Yahoo Finance (cached 24h)."""
    # Check cache
    cached = cache_get("fundamental_data", ticker, FUNDAMENTAL_CACHE_TTL)
    if cached is not None:
        meta = cached.get("_metadata", {})
        return FundamentalData(
            metadata=SourceMetadata(**meta) if meta else SourceMetadata(
                source="yahoo_finance", fetched_at=datetime.now(timezone.utc).isoformat(), status="ok"
            ),
            revenue=cached.get("revenue"),
            net_income=cached.get("net_income"),
            eps=cached.get("eps"),
            pe_ratio=cached.get("pe_ratio"),
            debt_to_equity=cached.get("debt_to_equity"),
            current_ratio=cached.get("current_ratio"),
            quick_ratio=cached.get("quick_ratio"),
            roe=cached.get("roe"),
            roa=cached.get("roa"),
            operating_margin=cached.get("operating_margin"),
            gross_margin=cached.get("gross_margin"),
            free_cash_flow=cached.get("free_cash_flow"),
            dividend_yield=cached.get("dividend_yield"),
            payout_ratio=cached.get("payout_ratio"),
            book_value_per_share=cached.get("book_value_per_share"),
            asset_turnover=cached.get("asset_turnover"),
            inventory_turnover=cached.get("inventory_turnover"),
            interest_coverage=cached.get("interest_coverage"),
            sector=cached.get("sector"),
            industry=cached.get("industry")
        )

    try:
        t = yf.Ticker(ticker)
        info = t.info

        metadata = SourceMetadata(
            source="yahoo_finance",
            fetched_at=datetime.now(timezone.utc).isoformat(),
            status="ok"
        )

        data = FundamentalData(
            metadata=metadata,
            revenue=info.get("totalRevenue"),
            net_income=info.get("netIncomeToCommon"),
            eps=info.get("trailingEps"),
            pe_ratio=info.get("trailingPE"),
            debt_to_equity=info.get("debtToEquity"),
            current_ratio=info.get("currentRatio"),
            quick_ratio=info.get("quickRatio"),
            roe=info.get("returnOnEquity"),
            roa=info.get("returnOnAssets"),
            operating_margin=info.get("operatingMargins"),
            gross_margin=info.get("grossMargins"),
            free_cash_flow=info.get("freeCashflow"),
            dividend_yield=info.get("dividendYield"),
            payout_ratio=info.get("payoutRatio"),
            book_value_per_share=info.get("bookValue"),
            asset_turnover=info.get("assetTurnover"),
            inventory_turnover=info.get("inventoryTurnover"),
            interest_coverage=info.get("interestCoverage"),
            sector=info.get("sector"),
            industry=info.get("industry")
        )

        # Cache
        to_cache = {
            "revenue": data.revenue,
            "net_income": data.net_income,
            "eps": data.eps,
            "pe_ratio": data.pe_ratio,
            "debt_to_equity": data.debt_to_equity,
            "current_ratio": data.current_ratio,
            "quick_ratio": data.quick_ratio,
            "roe": data.roe,
            "roa": data.roa,
            "operating_margin": data.operating_margin,
            "gross_margin": data.gross_margin,
            "free_cash_flow": data.free_cash_flow,
            "dividend_yield": data.dividend_yield,
            "payout_ratio": data.payout_ratio,
            "book_value_per_share": data.book_value_per_share,
            "asset_turnover": data.asset_turnover,
            "inventory_turnover": data.inventory_turnover,
            "interest_coverage": data.interest_coverage,
            "sector": data.sector,
            "industry": data.industry,
            "_metadata": {"source": metadata.source, "fetched_at": metadata.fetched_at, "status": metadata.status}
        }
        cache_set("fundamental_data", ticker, to_cache)

        return data
    except Exception as e:
        metadata = SourceMetadata(
            source="yahoo_finance",
            fetched_at=datetime.now(timezone.utc).isoformat(),
            status="missing"
        )
        return FundamentalData(
            metadata=metadata,
            revenue=None, net_income=None, eps=None, pe_ratio=None,
            debt_to_equity=None, current_ratio=None, quick_ratio=None,
            roe=None, roa=None, operating_margin=None, gross_margin=None,
            free_cash_flow=None, dividend_yield=None, payout_ratio=None,
            book_value_per_share=None, asset_turnover=None, inventory_turnover=None,
            interest_coverage=None
        )


def fetch_institutional_ownership(ticker: str) -> InstitutionalOwnership:
    """Ambil kepemilikan institusional (cached 24h)."""
    cached = cache_get("institutional_ownership", ticker, OWNERSHIP_CACHE_TTL)
    if cached is not None:
        meta = cached.get("_metadata", {})
        return InstitutionalOwnership(
            metadata=SourceMetadata(**meta) if meta else SourceMetadata(
                source="yahoo_finance", fetched_at=datetime.now(timezone.utc).isoformat(), status="ok"
            ),
            percentage=cached.get("percentage")
        )

    try:
        t = yf.Ticker(ticker)
        info = t.info

        percentage = info.get("heldPercentInstitutions")

        metadata = SourceMetadata(
            source="yahoo_finance",
            fetched_at=datetime.now(timezone.utc).isoformat(),
            status="ok" if percentage is not None else "missing"
        )

        data = InstitutionalOwnership(metadata=metadata, percentage=percentage)

        # Cache
        to_cache = {
            "percentage": percentage,
            "_metadata": {"source": metadata.source, "fetched_at": metadata.fetched_at, "status": metadata.status}
        }
        cache_set("institutional_ownership", ticker, to_cache)

        return data
    except Exception as e:
        metadata = SourceMetadata(
            source="yahoo_finance",
            fetched_at=datetime.now(timezone.utc).isoformat(),
            status="missing"
        )
        return InstitutionalOwnership(metadata=metadata)
