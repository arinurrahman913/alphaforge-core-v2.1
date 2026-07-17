"""Fetch company news dari Finnhub.

Endpoint `company-news` sudah terkonfirmasi free tier 60 req/menit.
Kalau premium atau 403, graceful degradation ke status=missing (bukan error).

Lihat 03_LAYER2_SPECS/02_EVIDENCE.md §1.4 — verifikasi free tier endpoint.
"""
from __future__ import annotations

import os
import requests
from datetime import datetime, timedelta, timezone
from ..contracts import SourceMetadata, CompanyNews, NewsCollection


FINNHUB_API_KEY = os.environ.get("FINNHUB_API_KEY")
FINNHUB_BASE_URL = "https://finnhub.io/api/v1"


def fetch_company_news(ticker: str, lookback_days: int = 30) -> NewsCollection:
    """Ambil berita terkini dari Finnhub — 30-90 hari terakhir default."""
    if not FINNHUB_API_KEY:
        metadata = SourceMetadata(
            source="finnhub",
            fetched_at=datetime.now(timezone.utc).isoformat(),
            status="missing"
        )
        return NewsCollection(news=[], metadata=metadata)

    try:
        to_date = datetime.now(timezone.utc).date().isoformat()
        from_date = (datetime.now(timezone.utc) - timedelta(days=lookback_days)).date().isoformat()

        url = f"{FINNHUB_BASE_URL}/company-news"
        params = {
            "symbol": ticker,
            "from": from_date,
            "to": to_date,
            "token": FINNHUB_API_KEY,
        }

        resp = requests.get(url, params=params, timeout=10)

        # 403 = premium-only endpoint
        if resp.status_code == 403:
            metadata = SourceMetadata(
                source="finnhub",
                fetched_at=datetime.now(timezone.utc).isoformat(),
                status="missing"
            )
            return NewsCollection(news=[], metadata=metadata)

        resp.raise_for_status()
        data = resp.json()

        news_list = []
        for item in data:
            news_list.append(CompanyNews(
                headline=item.get("headline", ""),
                source=item.get("source", ""),
                published_at=datetime.fromtimestamp(item.get("datetime", 0), tz=timezone.utc).isoformat(),
                url=item.get("url")
            ))

        metadata = SourceMetadata(
            source="finnhub",
            fetched_at=datetime.now(timezone.utc).isoformat(),
            status="ok" if news_list else "degraded"
        )

        return NewsCollection(news=news_list, metadata=metadata)

    except requests.exceptions.RequestException:
        metadata = SourceMetadata(
            source="finnhub",
            fetched_at=datetime.now(timezone.utc).isoformat(),
            status="missing"
        )
        return NewsCollection(news=[], metadata=metadata)
