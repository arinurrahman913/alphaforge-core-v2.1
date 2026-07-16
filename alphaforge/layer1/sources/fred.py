"""Wrapper tipis di atas FRED API (https://fred.stlouisfed.org/docs/api/fred/).

Butuh FRED_API_KEY (gratis, daftar di https://fred.stlouisfed.org/docs/api/api_key.html).
Tanpa key, pemanggil harus menangani ValueError dan menandai komponen status=missing.
"""
from __future__ import annotations

import os

import requests

BASE_URL = "https://api.stlouisfed.org/fred/series/observations"


def api_key() -> str:
    key = os.environ.get("FRED_API_KEY")
    if not key:
        raise ValueError("FRED_API_KEY tidak diset")
    return key


def latest_observation(series_id: str) -> tuple[str, float]:
    """Kembalikan (date, value) observasi terbaru yang bukan '.' (missing di FRED)."""
    params = {
        "series_id": series_id,
        "api_key": api_key(),
        "file_type": "json",
        "sort_order": "desc",
        "limit": 20,
    }
    resp = requests.get(BASE_URL, params=params, timeout=15)
    resp.raise_for_status()
    obs = resp.json().get("observations", [])
    for o in obs:
        if o["value"] != ".":
            return o["date"], float(o["value"])
    raise ValueError(f"no valid observation for {series_id}")


def series_observations(series_id: str, limit: int = 24) -> list[tuple[str, float]]:
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
    return [(o["date"], float(o["value"])) for o in obs if o["value"] != "."]
