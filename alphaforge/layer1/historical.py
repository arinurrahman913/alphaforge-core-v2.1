"""Historical tracking untuk LayerScore — ditambahkan pasca-audit (2026-07).

Sebelumnya tidak ada satu pun mekanisme yang melacak LayerScore dari waktu
ke waktu: tiap run cuma snapshot titik-waktu, tidak ada yang tahu apakah
skor 62 hari ini "normal" atau "tidak biasa" dibanding beberapa minggu
terakhir — dan tanpa histori, LayerScore juga tidak pernah bisa divalidasi
terhadap hasil pasar nyata (mis. dibandingkan versus return S&P 500 forward).

Modul ini cuma menyimpan; validasi/backtest adalah langkah terpisah nanti
setelah histori cukup terkumpul (beberapa bulan minimum untuk bermakna
secara statistik).

Satu entry per HARI KALENDER (UTC) — kalau refresh_layer1.py dipanggil
berkali-kali sehari (mis. tiap ~2 jam via scheduled task), entry hari itu
DIGANTI oleh run terbaru, bukan diakumulasi — mendekati konvensi "snapshot
akhir hari" pada deret waktu finansial, dan mencegah file membengkak.
"""
from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .contracts import MarketContextPackage

MAX_ENTRIES = 730  # ~2 tahun kalender kalau satu entry/hari


def load_history(path: str | Path) -> list[dict]:
    p = Path(path)
    if not p.exists():
        return []
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return []


def _entry_from_package(pkg: "MarketContextPackage") -> dict | None:
    if not pkg.layer_score:
        return None
    n_ok = sum(1 for c in pkg.components.values() if c.status == "ok")
    return {
        "date": pkg.generated_at[:10],  # YYYY-MM-DD, UTC (generated_at pakai now_iso() = UTC)
        "generated_at": pkg.generated_at,
        "final_score": pkg.layer_score.final_score,
        "formula_version": pkg.layer_score.formula_version,
        "n_ok": n_ok,
        "n_total": len(pkg.components),
        "confidence_score": round(pkg.context_summary.confidence.score, 1) if pkg.context_summary else None,
    }


def append_entry(path: str | Path, pkg: "MarketContextPackage", max_entries: int = MAX_ENTRIES) -> list[dict]:
    """Tambah snapshot LayerScore hari ini ke histori, tulis atomik. Kalau
    sudah ada entry untuk tanggal (UTC) yang sama, GANTI (bukan tambah) —
    lihat catatan modul. Return histori lengkap setelah update."""
    entry = _entry_from_package(pkg)
    if entry is None:
        return load_history(path)  # layer_score kosong (semua komponen gagal) — tidak ada yang dicatat

    history = load_history(path)
    if history and history[-1].get("date") == entry["date"]:
        history[-1] = entry
    else:
        history.append(entry)
    history = history[-max_entries:]

    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    tmp = p.with_name(p.name + ".tmp")
    tmp.write_text(json.dumps(history, indent=2, ensure_ascii=False), encoding="utf-8")
    os.replace(tmp, p)
    return history
