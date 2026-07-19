"""02_LAYER1_SPECS/12_MARKET_SENTIMENT.md — kind=derived, satu-satunya
composite Layer 1 (butuh minimal VIX + Market Breadth, dihitung terakhir).

Sejak 2026-07 (integrasi hybrid) memakai s.d. 4 input sentimen:
  1. VIX          — dari komponen volatility_index (sumber sendiri)
  2. Market Breadth — dari komponen market_breadth (universe internal)
  3. Put/Call     — otomatis best-effort dari CNN Fear & Greed (tidak resmi;
                     lihat sources/sentiment.py). Bisa di-override manual.
  4. AAII survey  — input manual opsional (dashboard/data/sentiment_manual.json),
                     karena AAII tidak punya API resmi gratis.

status:
  - `ok`       bila ≥3 dari 4 input tersedia (mis. VIX+breadth+put/call otomatis)
  - `degraded` bila hanya 1–2 input
  - `missing`  bila tidak ada input sama sekali

`status` menilai KELENGKAPAN DATA, bukan arah sinyal. Arah ada di `value.label`
(fear/neutral/greed), field terpisah. Skor tinggi = sentimen mendukung risk
assets (bukan warning contrarian "kelewat greedy").
"""
from __future__ import annotations

from ..contracts import ComponentReading, now_iso
from ..sources import sentiment as sentiment_src
from ._util import ev, source, th

NAME = "market_sentiment"
METHOD_VERSION = "2.0.0"

VIX_SCORE_MAP = {"low": 75, "normal": 50, "high": 20}
OK_MIN_INPUTS = 3  # ≥3 dari 4 input → status ok


def compute(vix_reading: ComponentReading, breadth_reading: ComponentReading) -> ComponentReading:
    available: list[tuple[str, float]] = []  # (nama_input, skor_0_100)
    missing_inputs: list[str] = []
    evidence = []
    sources_used = []

    # 1. VIX
    if vix_reading.status == "ok":
        vlevel = vix_reading.value["level"]
        vas = vix_reading.evidence[0].as_of if vix_reading.evidence else now_iso()[:10]
        available.append(("vix", float(VIX_SCORE_MAP[vlevel])))
        evidence.append(ev("vix_level", vlevel, vas, "volatility_index (komponen ini)"))
    else:
        missing_inputs.append("vix")

    # 2. Market breadth
    if breadth_reading.status == "ok":
        bpct = breadth_reading.value["pct_above_ma200"]
        bas = breadth_reading.evidence[0].as_of if breadth_reading.evidence else now_iso()[:10]
        available.append(("market_breadth", float(min(100, max(0, bpct)))))
        evidence.append(ev("breadth_pct_above_ma200", bpct, bas, "market_breadth (komponen ini)"))
    else:
        missing_inputs.append("market_breadth")

    # 3. Put/Call — override manual > CNN otomatis
    manual = sentiment_src.read_manual()
    pc = manual.get("put_call") or sentiment_src.fetch_put_call()
    if pc:
        is_manual = "put_call" in manual
        available.append(("put_call", float(pc["score_0_100"])))
        evidence.append(ev("put_call_score", round(pc["score_0_100"], 1), pc.get("as_of") or now_iso()[:10],
                           "manual" if is_manual else "CNN Fear & Greed (put/call, tidak resmi)"))
        sources_used.append(source("manual" if is_manual else "CNN Fear & Greed"))
    else:
        missing_inputs.append("put_call_ratio")

    # 4. AAII survey — hanya dari input manual
    aaii = manual.get("aaii")
    if aaii:
        available.append(("aaii", float(aaii["score_0_100"])))
        evidence.append(ev("aaii_bull_bear", f"bull {aaii['bullish_pct']}% / bear {aaii['bearish_pct']}%",
                           aaii.get("as_of") or now_iso()[:10], "AAII (input manual)"))
        sources_used.append(source("AAII (manual)"))
    else:
        missing_inputs.append("aaii_survey")

    if not available:
        return ComponentReading(
            name=NAME, value=None, status="missing", kind="derived",
            method_version=METHOD_VERSION, inputs=["volatility_index", "market_breadth"],
            note=f"Tidak ada input tersedia — hilang: {', '.join(missing_inputs)}.",
            rule="score = rata-rata skor input yang tersedia; tidak ada input → missing",
        )

    score = sum(s for _, s in available) / len(available)
    label = "greed" if score >= 65 else "fear" if score <= 35 else "neutral"
    n = len(available)
    status = "ok" if n >= OK_MIN_INPUTS else "degraded"

    used_names = [n for n, _ in available]
    narrative = (
        f"Signal: {label}. Skor sentimen {score:.0f}/100, dari {n} dari 4 input "
        f"({', '.join(used_names)}), dibobot rata."
    )
    if missing_inputs:
        narrative += f" Belum ada: {', '.join(missing_inputs)}."

    note = None
    if missing_inputs:
        note = (f"Hilang: {', '.join(missing_inputs)}. "
                "put/call diambil best-effort dari CNN Fear & Greed (tidak resmi); "
                "AAII dari input manual dashboard/data/sentiment_manual.json.")

    rule = (
        "score = rata-rata tak berbobot dari input tersedia (skala 0-100, tinggi=greed) — "
        "vix: low→75/normal→50/high→20; breadth: %ticker di atas MA200; "
        "put/call: skor CNN F&G (tinggi=greed); aaii: bull/(bull+bear)×100. "
        f"score≥65→greed, ≤35→fear, selain itu→neutral. status=ok bila ≥{OK_MIN_INPUTS}/4 input tersedia."
    )

    return ComponentReading(
        name=NAME,
        value={"score_0_100": score, "label": label, "inputs_used": used_names},
        status=status,
        kind="derived",
        method_version=METHOD_VERSION,
        inputs=["volatility_index", "market_breadth"],
        sources=sources_used,
        note=note,
        narrative=narrative,
        narrative_version="2.0.0",
        evidence=evidence,
        rule=rule,
        thresholds=[
            th("greed jika score di atas ini", ">=", 65),
            th("fear jika score di bawah ini", "<=", 35),
        ],
        raw_score=score,
    )
