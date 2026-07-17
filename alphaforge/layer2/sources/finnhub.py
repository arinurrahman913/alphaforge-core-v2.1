"""Fetch company news dari Finnhub dengan rate limiting.

Free tier: 60 req/menit. Implementation includes batching + delay
untuk 5000+ ticker run tanpa 429 errors.

Lihat 03_LAYER2_SPECS/02_EVIDENCE.md §1.4.
"""
from __future__ import annotations

import os
import time
import requests
from datetime import datetime, timedelta, timezone
from ..contracts import SourceMetadata, CompanyNews, NewsCollection


FINNHUB_API_KEY = os.environ.get("FINNHUB_API_KEY")
FINNHUB_BASE_URL = "https://finnhub.io/api/v1"
FINNHUB_BATCH_SIZE = int(os.environ.get("FINNHUB_BATCH_SIZE", "30"))
FINNHUB_BATCH_DELAY_SECONDS = float(os.environ.get("FINNHUB_BATCH_DELAY_SECONDS", "2.0"))

# Tracking untuk batch processing global (untuk orchestrator)
_batch_counter = 0
_batch_last_time = None


def reset_batch_tracking():
    """Reset batch counter (dipanggil di awal evidence run)."""
    global _batch_counter, _batch_last_time
    _batch_counter = 0
    _batch_last_time = None


def _apply_batch_delay():
    """Apply delay jika sudah breach batch size."""
    global _batch_counter, _batch_last_time
    _batch_counter += 1
    if _batch_counter >= FINNHUB_BATCH_SIZE:
        if _batch_last_time is None:
            _batch_last_time = time.time()
        elapsed = time.time() - _batch_last_time
        if elapsed < FINNHUB_BATCH_DELAY_SECONDS:
            time.sleep(FINNHUB_BATCH_DELAY_SECONDS - elapsed)
        _batch_counter = 0
        _batch_last_time = time.time()


def fetch_company_news(ticker: str, lookback_days: int = 30) -> NewsCollection:
    """Ambil berita terkini dari Finnhub — dengan rate limit handling."""
    if not FINNHUB_API_KEY:
        metadata = SourceMetadata(
            source="finnhub",
            fetched_at=datetime.now(timezone.utc).isoformat(),
            status="missing"
        )
        return NewsCollection(news=[], metadata=metadata)

    try:
        _apply_batch_delay()

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

        # 403 = premium-only endpoint, 429 = rate limited
        if resp.status_code in [403, 429]:
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
