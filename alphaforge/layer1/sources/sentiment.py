"""Sumber sentimen tambahan untuk market_sentiment — strategi hybrid.

Baik CBOE put/call ratio maupun AAII Investor Sentiment Survey tidak punya API
resmi gratis (lihat 04_DATA_SOURCES/01_PROVIDERS_OVERVIEW.md §2b). Solusinya:

- **put/call**: diambil best-effort dari endpoint publik CNN Fear & Greed
  (`put_call_options`). Ini endpoint TIDAK RESMI — kalau strukturnya berubah
  atau putus, `fetch_put_call()` mengembalikan None dan komponen degrade dengan
  jujur (tidak pernah melempar error).
- **AAII**: dibaca dari file manual `dashboard/data/sentiment_manual.json` yang
  diisi pengguna dari aaii.com (survei mingguan). Absen/rusak/kadaluarsa →
  tidak dipakai.

Semua skor pada skala 0–100 dengan konvensi yang sama seperti market_sentiment:
tinggi = greed / risk-on, rendah = fear. (CNN sudah menormalkan put/call ke
skala ini: put/call ratio tinggi = fear = skor rendah.)
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import requests

from ... import cache

CNN_URL = "https://production.dataviz.cnn.io/index/fearandgreed/graphdata"
# Header lengkap ala browser — tanpa ini CNN membalas HTTP 418 (blokir bot).
CNN_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "en-US,en;q=0.9",
    "Referer": "https://www.cnn.com/markets/fear-and-greed",
    "Origin": "https://www.cnn.com",
}
CACHE_NS = "sentiment"
PUT_CALL_TTL = 12 * 3600
MANUAL_PATH = Path(__file__).resolve().parents[3] / "dashboard" / "data" / "sentiment_manual.json"
AAII_MAX_AGE_DAYS = 30


def fetch_put_call() -> dict | None:
    """{'score_0_100': float, 'as_of': 'YYYY-MM-DD'} atau None (best-effort, cached 12 jam)."""
    cached = cache.get(CACHE_NS, "cnn_put_call", PUT_CALL_TTL)
    if cached is not None:
        return cached
    try:
        r = requests.get(CNN_URL, headers=CNN_HEADERS, timeout=10)
        r.raise_for_status()
        pc = r.json()["put_call_options"]
        score = float(pc["score"])
        ts = pc.get("timestamp")
        if ts:
            as_of = datetime.fromtimestamp(ts / 1000, tz=timezone.utc).strftime("%Y-%m-%d")
        else:
            as_of = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        data = {"score_0_100": score, "as_of": as_of}
    except Exception:
        return None
    cache.set(CACHE_NS, "cnn_put_call", data)
    return data


def _fresh_enough(as_of: str) -> bool:
    if not as_of:
        return True  # tanpa tanggal, percayakan ke pengguna
    try:
        d = datetime.strptime(as_of[:10], "%Y-%m-%d").replace(tzinfo=timezone.utc)
    except Exception:
        return True
    return (datetime.now(timezone.utc) - d).days <= AAII_MAX_AGE_DAYS


def read_manual() -> dict:
    """Baca override manual dari MANUAL_PATH. Return dict yang bisa berisi
    key 'aaii' dan/atau 'put_call' (masing-masing {'score_0_100', 'as_of', ...}).
    File absen/rusak/kadaluarsa → {}."""
    if not MANUAL_PATH.exists():
        return {}
    try:
        raw = json.loads(MANUAL_PATH.read_text(encoding="utf-8"))
    except Exception:
        return {}

    out: dict = {}
    aaii = raw.get("aaii")
    if isinstance(aaii, dict):
        bull, bear = aaii.get("bullish_pct"), aaii.get("bearish_pct")
        as_of = aaii.get("as_of", "")
        if isinstance(bull, (int, float)) and isinstance(bear, (int, float)) and (bull + bear) > 0 and _fresh_enough(as_of):
            out["aaii"] = {
                "score_0_100": bull / (bull + bear) * 100.0,
                "bullish_pct": bull,
                "bearish_pct": bear,
                "as_of": as_of,
            }

    pcs = raw.get("put_call_score")
    if isinstance(pcs, (int, float)):
        out["put_call"] = {"score_0_100": float(pcs), "as_of": raw.get("put_call_as_of", "")}

    return out
