"""Cache lokal berbasis file, TTL sederhana — 04_DATA_SOURCES/05_RATE_LIMIT_CACHING_STRATEGY.md
prinsip #2: "Caching wajib, bukan opsional."
"""
from __future__ import annotations

import json
import time
from pathlib import Path

CACHE_DIR = Path(__file__).resolve().parent.parent / ".cache"


def _path(namespace: str, key: str) -> Path:
    d = CACHE_DIR / namespace
    d.mkdir(parents=True, exist_ok=True)
    safe_key = key.replace("/", "_").replace("\\", "_")
    return d / f"{safe_key}.json"


def get(namespace: str, key: str, ttl_seconds: float):
    p = _path(namespace, key)
    if not p.exists():
        return None
    try:
        payload = json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return None
    if time.time() - payload["cached_at"] > ttl_seconds:
        return None
    return payload["data"]


def set(namespace: str, key: str, data) -> None:
    p = _path(namespace, key)
    p.write_text(json.dumps({"cached_at": time.time(), "data": data}), encoding="utf-8")


def get_stale(namespace: str, key: str):
    """Baca cache TANPA cek TTL — fallback darurat kalau fetch fresh gagal
    (mis. sumber down). Mendingan pakai data lama yang masih ada daripada
    pipeline berhenti total. Return (data, age_seconds) atau None kalau
    belum pernah di-cache sama sekali."""
    p = _path(namespace, key)
    if not p.exists():
        return None
    try:
        payload = json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return None
    age = time.time() - payload["cached_at"]
    return payload["data"], age
