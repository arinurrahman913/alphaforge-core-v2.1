"""02_LAYER1_SPECS/12_MARKET_SENTIMENT.md — kind=derived, satu-satunya
composite Layer 1 (butuh VIX + Market Breadth, wajib dihitung terakhir).

Catatan jujur: AAII Investor Sentiment Survey dan CBOE Put/Call Ratio belum
diintegrasikan di repo ini (keduanya tidak punya API resmi gratis — lihat
04_DATA_SOURCES/01_PROVIDERS_OVERVIEW.md §2b; mengintegrasikannya butuh
scraping yang belum diverifikasi amannya). Sampai itu ada, komponen ini
dihitung cuma dari VIX + Market Breadth (2 dari 4 input spec), dan SELALU
`status=degraded` (tidak pernah `ok`) sampai AAII+put/call terpasang —
supaya tidak diam-diam terlihat lengkap.

Penting: `status=degraded` di sini artinya KUALITAS DATA kurang lengkap
(2 dari 4 input spec), BUKAN penilaian bahwa sinyalnya bearish — sinyal
arahnya sendiri ada di `value.label` (fear/neutral/greed), field terpisah
dari status. "Data Quality" yang diminta review tim (Moderate/dst) adalah
band dari `confidence` yang diisi pipeline.py setelah komponen ini
selesai (base 100 - 25 karena status=degraded → confidence≈75, "moderate"),
bukan field baru — biar tidak ada dua formula confidence yang beda-beda.
"""
from __future__ import annotations

from ..contracts import ComponentReading, now_iso
from ._util import ev, th

NAME = "market_sentiment"
METHOD_VERSION = "1.0.0"

MISSING_INPUTS_ALWAYS = ["aaii_survey", "put_call_ratio"]  # belum diintegrasikan
VIX_SCORE_MAP = {"low": 75, "normal": 50, "high": 20}


def compute(vix_reading: ComponentReading, breadth_reading: ComponentReading) -> ComponentReading:
    missing_inputs = list(MISSING_INPUTS_ALWAYS)
    available = []
    evidence = []

    if vix_reading.status == "ok":
        available.append(("vix", vix_reading.value["level"]))
        vix_as_of = vix_reading.evidence[0].as_of if vix_reading.evidence else now_iso()[:10]
        evidence.append(ev("vix_level", vix_reading.value["level"], vix_as_of, "volatility_index (komponen ini)"))
    else:
        missing_inputs.append("vix")

    if breadth_reading.status == "ok":
        available.append(("market_breadth", breadth_reading.value["pct_above_ma200"]))
        breadth_as_of = breadth_reading.evidence[0].as_of if breadth_reading.evidence else now_iso()[:10]
        evidence.append(ev("breadth_pct_above_ma200", breadth_reading.value["pct_above_ma200"], breadth_as_of, "market_breadth (komponen ini)"))
    else:
        missing_inputs.append("market_breadth")

    if not available:
        return ComponentReading(
            name=NAME,
            value=None,
            status="missing",
            kind="derived",
            method_version=METHOD_VERSION,
            inputs=["volatility_index", "market_breadth"],
            note=f"Tidak ada input tersedia — hilang: {', '.join(missing_inputs)}.",
            rule="score = rata-rata dari input yang tersedia (vix: low=75/normal=50/high=20, breadth: %ATAS MA200 langsung); tidak ada input tersedia",
        )

    # skala kasar 0 (extreme fear) - 100 (extreme greed) dari input yang tersedia,
    # dibobot rata (50/50 kalau dua-duanya ada, 100% ke satu-satunya yang ada
    # kalau cuma satu) — bukan sinyal contrarian, skor tinggi = sentimen
    # mendukung risk assets, bukan warning "kelewat greedy".
    scores = []
    for name, val in available:
        if name == "vix":
            scores.append(VIX_SCORE_MAP[val])
        elif name == "market_breadth":
            scores.append(min(100, max(0, val)))
    score = sum(scores) / len(scores)

    if score >= 65:
        label = "greed"
    elif score <= 35:
        label = "fear"
    else:
        label = "neutral"

    narrative = (
        f"Signal: {label}. Skor sentimen kasar {score:.0f}/100, dihitung dari {len(available)} dari 4 input spec "
        f"({', '.join(n for n, _ in available)}), dibobot rata. Hilang: {', '.join(missing_inputs)}."
    )
    rule = (
        "score = rata-rata tak berbobot dari input tersedia — vix: low→75, normal→50, high→20; "
        "breadth: %ticker di atas MA200 langsung; score≥65→greed, score≤35→fear, selain itu→neutral. "
        "status=degraded artinya cuma 2/4 input spec tersedia (AAII survey & put/call ratio belum ada), "
        "BUKAN penilaian bahwa signal-nya bearish."
    )

    return ComponentReading(
        name=NAME,
        value={"score_0_100": score, "label": label, "inputs_used": [n for n, _ in available]},
        status="degraded",
        kind="derived",
        method_version=METHOD_VERSION,
        inputs=["volatility_index", "market_breadth"],
        note=f"AAII survey & put/call ratio belum diintegrasikan (lihat docstring modul). "
             f"Hilang: {', '.join(missing_inputs)}.",
        narrative=narrative,
        narrative_version="1.0.0",
        evidence=evidence,
        rule=rule,
        thresholds=[
            th("greed jika score di atas ini", ">=", 65),
            th("fear jika score di bawah ini", "<=", 35),
        ],
        raw_score=score,
    )
