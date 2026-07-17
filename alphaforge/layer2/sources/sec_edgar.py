"""Fetch SEC filings list dari EDGAR — stub untuk MVP.

SEC EDGAR API sering 403 (rate limit/access restriction). Implementasi full
parsing 10-K/10-Q/8-K diwacanakan nanti kalau Knowledge modul benar-benar
membutuhkan detail filing (leverage, debt structure detail, segment breakdowns).

Untuk MVP: SEC filings placeholder, status=missing/degraded. Evidence tetap
lengkap dari Yahoo + Finnhub. Risk/Red-Flag Check akan mengintegrasikan
EDGAR kemudian kalau butuh detect restatement/auditor change/dll.

Lihat 03_LAYER2_SPECS/02_EVIDENCE.md §1.5 & 04_DATA_SOURCES/01_PROVIDERS_OVERVIEW.md.
"""
from __future__ import annotations

from datetime import datetime, timezone
from ..contracts import SourceMetadata, SecFilings


def fetch_sec_filings(ticker: str, max_filings: int = 10) -> SecFilings:
    """Placeholder: SEC filings lookup tidak reliabel di MVP.

    Kembalikan empty dengan status=missing sampai:
    1. Infrastructure EDGAR parsing stabil (rate limit / auth)
    2. Knowledge/Risk-Check modul real-real butuh filing detail
    """
    metadata = SourceMetadata(
        source="sec_edgar",
        fetched_at=datetime.now(timezone.utc).isoformat(),
        status="missing"
    )
    return SecFilings(filings=[], metadata=metadata)
