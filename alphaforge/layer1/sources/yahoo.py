"""Wrapper tipis di atas yfinance. Titik kegagalan tunggal terbesar sistem
(lihat 04_DATA_SOURCES/01_PROVIDERS_OVERVIEW.md §2b) — semua pemanggil wajib
menangkap exception dan mengubahnya jadi status=missing, bukan membiarkan
pipeline berhenti.
"""
from __future__ import annotations

import yfinance as yf
import pandas as pd


def history(ticker: str, period: str = "1y", interval: str = "1d") -> pd.DataFrame:
    df = yf.Ticker(ticker).history(period=period, interval=interval)
    if df is None or df.empty:
        raise ValueError(f"no data returned for {ticker}")
    return df


def last_close(ticker: str, period: str = "5d") -> float:
    df = history(ticker, period=period)
    return float(df["Close"].iloc[-1])


def pct_change(ticker: str, days: int, period: str = "1y") -> float:
    """Perubahan persentase close hari terakhir vs `days` hari (kalender bursa) sebelumnya."""
    df = history(ticker, period=period)
    if len(df) <= days:
        raise ValueError(f"insufficient history for {ticker}: {len(df)} rows, need > {days}")
    last = float(df["Close"].iloc[-1])
    prior = float(df["Close"].iloc[-1 - days])
    return (last - prior) / prior * 100.0
