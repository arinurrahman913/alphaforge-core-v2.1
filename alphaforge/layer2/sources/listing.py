"""04_DATA_SOURCES/03_MARKET_LISTING_SOURCES.md — daftar ticker NASDAQ + NYSE.

Sumber: NASDAQ Trader symbol directory (gratis, publik, tidak perlu API key).
"""
from __future__ import annotations

import io

import requests

from ...cache import get as cache_get, set as cache_set
from ..contracts import ListingRow

NASDAQ_URL = "https://www.nasdaqtrader.com/dynamic/SymDir/nasdaqlisted.txt"
OTHER_URL = "https://www.nasdaqtrader.com/dynamic/SymDir/otherlisted.txt"

LISTING_TTL_SECONDS = 24 * 3600  # daftar ticker tidak berubah drastis harian

# Kata kunci nama sekuritas yang menandakan BUKAN common stock — dipakai untuk
# hard exclude "tipe listing" (03_LAYER2_SPECS/01_SCREENING.md). Ini heuristik
# berbasis teks karena listing file tidak punya kolom "instrument type" eksplisit
# selain ETF; didokumentasikan sebagai simplifikasi sadar, bukan disamarkan.
NON_COMMON_STOCK_KEYWORDS = [
    "warrant", " right", " rights", " unit", " units", "preferred",
    "depositary share", "depository share", "trust preferred", " notes",
    "acquisition corp - class", "acquisition corp. - class",
]


def _parse_pipe_table(text: str) -> list[list[str]]:
    lines = [ln for ln in text.splitlines() if ln.strip()]
    # baris terakhir NASDAQ Trader adalah footer "File Creation Time: ..."
    if lines and lines[-1].lower().startswith("file creation time"):
        lines = lines[:-1]
    rows = [ln.split("|") for ln in lines]
    return rows


def _fetch_text(url: str) -> str:
    resp = requests.get(url, timeout=30)
    resp.raise_for_status()
    return resp.text


def fetch_universe(use_cache: bool = True) -> list[ListingRow]:
    """Gabungan NASDAQ + NYSE, sudah melewati exclude ETF/test issue/non-common-stock
    (hard exclude "tipe listing" — zero panggilan API, langsung dari kolom listing file)."""
    cached = cache_get("listing", "universe", LISTING_TTL_SECONDS) if use_cache else None
    if cached is not None:
        return [ListingRow(**row) for row in cached]

    rows: list[ListingRow] = []

    nasdaq_text = _fetch_text(NASDAQ_URL)
    header, *data = _parse_pipe_table(nasdaq_text)
    idx = {name: i for i, name in enumerate(header)}
    for r in data:
        if len(r) != len(header):
            continue
        symbol = r[idx["Symbol"]].strip()
        name = r[idx["Security Name"]].strip()
        is_etf = r[idx["ETF"]].strip() == "Y"
        is_test = r[idx["Test Issue"]].strip() == "Y"
        rows.append(ListingRow(symbol=symbol, security_name=name, exchange="NASDAQ",
                                is_etf=is_etf, is_test_issue=is_test))

    other_text = _fetch_text(OTHER_URL)
    header2, *data2 = _parse_pipe_table(other_text)
    idx2 = {name: i for i, name in enumerate(header2)}
    for r in data2:
        if len(r) != len(header2):
            continue
        if r[idx2["Exchange"]].strip() != "N":  # 'N' = NYSE; spec cuma minta NASDAQ+NYSE
            continue
        symbol = r[idx2["ACT Symbol"]].strip()
        name = r[idx2["Security Name"]].strip()
        is_etf = r[idx2["ETF"]].strip() == "Y"
        is_test = r[idx2["Test Issue"]].strip() == "Y"
        rows.append(ListingRow(symbol=symbol, security_name=name, exchange="NYSE",
                                is_etf=is_etf, is_test_issue=is_test))

    cache_set("listing", "universe", [vars(r) for r in rows])
    return rows


def is_common_stock(row: ListingRow) -> bool:
    if row.is_etf or row.is_test_issue:
        return False
    if "$" in row.symbol or "." in row.symbol:  # kelas saham/unit khusus, notasi non-standar
        return False
    name_lower = row.security_name.lower()
    return not any(kw in name_lower for kw in NON_COMMON_STOCK_KEYWORDS)


def cheap_filter(universe: list[ListingRow]) -> list[ListingRow]:
    """Hard exclude tipe listing & test issue — tanpa panggilan API sama sekali
    (03_LAYER2_SPECS/01_SCREENING.md, "Cara Kerja — Sumber Data per Tahap Filter" #1)."""
    return [r for r in universe if is_common_stock(r)]
