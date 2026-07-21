"""Retry+backoff+logging helper dipakai semua sources/* — pola yang sama
persis dipakai di screening.py & listing.py (lihat commit fix Screening),
diekstrak ke sini karena Evidence butuh pola identik di 6+ tempat berbeda
(Yahoo x3, Finnhub, SEC EDGAR, SEC parser). Kegagalan sekarang selalu ada
jejaknya di stderr, bukan silently downgrade ke status="missing" tanpa
penjelasan sama sekali soal sumber mana yang gagal dan kenapa.
"""
from __future__ import annotations

import sys
import time
from typing import Callable, TypeVar

T = TypeVar("T")


def retry(fn: Callable[[], T], *, retries: int, backoff_seconds: float, label: str) -> T:
    """Panggil fn() sampai `retries` kali (backoff linear antar percobaan,
    tidak dipanggil setelah percobaan terakhir). Kalau semua gagal, log ke
    stderr lalu re-raise exception terakhir — caller yang putuskan mau
    fallback ke status="missing" atau propagate lebih jauh."""
    last_exc: Exception | None = None
    for attempt in range(1, retries + 1):
        try:
            return fn()
        except Exception as exc:  # noqa: BLE001
            last_exc = exc
            if attempt < retries:
                print(f"[{label}] percobaan {attempt}/{retries} gagal: {exc} — retry dalam {backoff_seconds}s",
                      file=sys.stderr)
                time.sleep(backoff_seconds)
    print(f"[{label}] gagal total setelah {retries}x percobaan: {last_exc}", file=sys.stderr)
    raise last_exc
