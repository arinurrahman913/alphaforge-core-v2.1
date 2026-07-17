"""Fetch SEC filings list dari EDGAR.

API gratis: `company-facts` (daily.json) atau CIK lookup. Di sini pakai
EDGAR-ONLINE API atau parsing direct dari SEC (minimal parsing untuk terbaru).

Lihat 03_LAYER2_SPECS/02_EVIDENCE.md §1.5 — EDGAR yang dijamin gratis.
"""
from __future__ import annotations

import requests
from datetime import datetime, timezone
from ..contracts import SourceMetadata, SecFiling, SecFilings


SEC_EDGAR_BASE = "https://www.sec.gov"
SEC_CIKS_JSON = "https://www.sec.gov/files/company_tickers.json"


def _get_cik_for_ticker(ticker: str) -> str | None:
    """Ambil CIK dari ticker via SEC company_tickers.json."""
    try:
        resp = requests.get(SEC_CIKS_JSON, timeout=10)
        resp.raise_for_status()
        data = resp.json()

        for entry in data.values():
            if entry.get("ticker", "").upper() == ticker.upper():
                return str(entry.get("cik_str", "")).zfill(10)
        return None
    except Exception:
        return None


def fetch_sec_filings(ticker: str, max_filings: int = 10) -> SecFilings:
    """Ambil daftar SEC filings terkini untuk satu ticker (10-K, 10-Q, 8-K)."""
    try:
        cik = _get_cik_for_ticker(ticker)
        if not cik:
            metadata = SourceMetadata(
                source="sec_edgar",
                fetched_at=datetime.now(timezone.utc).isoformat(),
                status="missing"
            )
            return SecFilings(filings=[], metadata=metadata)

        # Fetch company facts JSON dari EDGAR (gratis, updated daily)
        url = f"{SEC_EDGAR_BASE}/cgi-bin/browse-edgar?action=getcompany&CIK={cik}&type=&dateb=&owner=exclude&count=100&output=json"

        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
        data = resp.json()

        filings_list = []
        for filing in data.get("filings", {}).get("recent", [])[:max_filings]:
            form_type = filing.get("form", "")
            # Filter hanya tipe penting: 10-K, 10-Q, 8-K, 20-F (foreign), dll
            if form_type not in ["10-K", "10-Q", "8-K", "20-F", "20-F/A", "10-K/A", "10-Q/A"]:
                continue

            filing_date = filing.get("filingDate", "")
            accession = filing.get("accessionNumber", "").replace("-", "")

            url_filing = f"{SEC_EDGAR_BASE}/cgi-bin/viewer?action=view&cik={cik}&accession_number={filing.get('accessionNumber', '')}&xbrl_type=v"

            filings_list.append(SecFiling(
                form_type=form_type,
                filing_date=filing_date,
                url=url_filing if accession else None
            ))

        metadata = SourceMetadata(
            source="sec_edgar",
            fetched_at=datetime.now(timezone.utc).isoformat(),
            status="ok" if filings_list else "degraded"
        )

        return SecFilings(filings=filings_list, metadata=metadata)

    except Exception:
        metadata = SourceMetadata(
            source="sec_edgar",
            fetched_at=datetime.now(timezone.utc).isoformat(),
            status="missing"
        )
        return SecFilings(filings=[], metadata=metadata)
