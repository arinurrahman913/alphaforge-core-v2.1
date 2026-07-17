"""Fetch daftar SEC filings terkini dari EDGAR submissions API.

Endpoint `https://data.sec.gov/submissions/CIK{cik}.json` resmi dan gratis,
tapi wajib header User-Agent (https://www.sec.gov/os/webmaster-faq#developers)
— tanpa header ini semua request di-403. Fix ini yang sebelumnya bikin modul
selalu return status=missing walau data-nya sebenarnya tersedia.

Lihat 03_LAYER2_SPECS/02_EVIDENCE.md §1.5 & 04_DATA_SOURCES/01_PROVIDERS_OVERVIEW.md.
"""
from __future__ import annotations

from datetime import datetime, timezone

import requests

from ... import cache
from ..contracts import SecFiling, SecFilings, SourceMetadata
from .sec_parser import SEC_USER_AGENT, get_cik_from_ticker

SUBMISSIONS_URL = "https://data.sec.gov/submissions/CIK{cik}.json"
_SUBMISSIONS_TTL = 24 * 3600  # 24 jam

_HEADERS = {"User-Agent": SEC_USER_AGENT}

# Form yang relevan untuk analisis fundamental/governance; abaikan Form 3/4/144
# (insider transaction) yang volumenya tinggi tapi tidak dibutuhkan di sini.
_RELEVANT_FORMS = {"10-K", "10-K/A", "10-Q", "10-Q/A", "8-K", "8-K/A", "DEF 14A"}


def fetch_sec_filings(ticker: str, max_filings: int = 10) -> SecFilings:
    """Ambil daftar filing terkini (10-K/10-Q/8-K/proxy) untuk satu ticker."""
    cik = get_cik_from_ticker(ticker)
    if not cik:
        metadata = SourceMetadata(
            source="sec_edgar",
            fetched_at=datetime.now(timezone.utc).isoformat(),
            status="missing",
        )
        return SecFilings(filings=[], metadata=metadata)

    cache_key = f"submissions_{cik}"
    data = cache.get("sec_edgar", cache_key, _SUBMISSIONS_TTL)
    if data is None:
        try:
            resp = requests.get(SUBMISSIONS_URL.format(cik=cik), headers=_HEADERS, timeout=15)
            resp.raise_for_status()
            data = resp.json()
            cache.set("sec_edgar", cache_key, data)
        except Exception:
            data = None

    if not data:
        metadata = SourceMetadata(
            source="sec_edgar",
            fetched_at=datetime.now(timezone.utc).isoformat(),
            status="missing",
        )
        return SecFilings(filings=[], metadata=metadata)

    recent = data.get("filings", {}).get("recent", {})
    forms = recent.get("form", [])
    dates = recent.get("filingDate", [])
    accessions = recent.get("accessionNumber", [])
    docs = recent.get("primaryDocument", [])

    filings: list[SecFiling] = []
    for form, date, accn, doc in zip(forms, dates, accessions, docs):
        if form not in _RELEVANT_FORMS:
            continue
        accn_nodash = accn.replace("-", "")
        url = f"https://www.sec.gov/Archives/edgar/data/{int(cik)}/{accn_nodash}/{doc}"
        filings.append(SecFiling(form_type=form, filing_date=date, url=url))
        if len(filings) >= max_filings:
            break

    metadata = SourceMetadata(
        source="sec_edgar",
        fetched_at=datetime.now(timezone.utc).isoformat(),
        status="ok" if filings else "degraded",
    )
    return SecFilings(filings=filings, metadata=metadata)
