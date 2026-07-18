"""Wrapper tipis di atas FRED API (https://fred.stlouisfed.org/docs/api/fred/).

Butuh FRED_API_KEY (gratis, daftar di https://fred.stlouisfed.org/docs/api/api_key.html).
Tanpa key, pemanggil harus menangani ValueError dan menandai komponen status=missing.

Cached 12 jam — seri FRED (GDP, UNRATE, WALCL, dst) rilis paling cepat
harian, biasanya mingguan/bulanan, jadi run Layer 1 yang sering (mis.
refresh dashboard berkala) tidak perlu menembak FRED tiap kali.
"""
from __future__ import annotations

import os

import requests

from ... import cache

BASE_URL = "https://api.stlouisfed.org/fred/series/observations"
OBSERVATIONS_CACHE_TTL = 12 * 3600  # 12 jam


def api_key() -> str:
    key = os.environ.get("FRED_API_KEY")
    if not key:
        raise ValueError("FRED_API_KEY tidak diset")
    return key


def latest_observation(series_id: str) -> tuple[str, float]:
    """Kembalikan (date, value) observasi terbaru yang bukan '.' (missing di FRED)."""
    obs = series_observations(series_id, limit=20)
    if obs:
        return obs[0]
    raise ValueError(f"no valid observation for {series_id}")


def series_observations(series_id: str, limit: int = 24) -> list[tuple[str, float]]:
    cache_key = f"{series_id}_{limit}"
    cached = cache.get("layer1_fred_observations", cache_key, OBSERVATIONS_CACHE_TTL)
    if cached is not None:
        return [tuple(pair) for pair in cached]

    params = {
        "series_id": series_id,
        "api_key": api_key(),
        "file_type": "json",
        "sort_order": "desc",
        "limit": limit,
    }
    resp = requests.get(BASE_URL, params=params, timeout=15)
    resp.raise_for_status()
    obs = resp.json().get("observations", [])
    result = [(o["date"], float(o["value"])) for o in obs if o["value"] != "."]

    cache.set("layer1_fred_observations", cache_key, result)
    return result
