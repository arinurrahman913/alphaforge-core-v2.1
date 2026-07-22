"""Layer 2 tahap 3: Knowledge — structured understanding dari Evidence per ticker.

Bukan data mentah lagi, tapi profil terstruktur: tren, kategori, fakta terukur.
Tanpa penilaian kualitatif (itu tugas Confidence/Reasoning/Risk).

Input: list EvidencePackage dari Evidence
Output: list KnowledgeProfile

Lihat 03_LAYER2_SPECS/03_KNOWLEDGE.md.
"""
from __future__ import annotations

import sys
from datetime import datetime, timezone
from .contracts import EvidencePackage, ScreeningCandidate
from .knowledge_contracts import (
    KnowledgeProfile, KnowledgeMetadata, FinancialHealth, Ownership,
    RevenueTrend, MarginTrend, BalanceSheet, CashFlowTrend, CapExInfo,
    CompetitiveStructure, CompetitiveMomentum, HistoricalTrend, Valuation, Governance,
    GovernanceEvent
)
from .knowledge_helpers import (
    calculate_returns, calculate_volatility,
    calculate_financial_metrics, infer_size_category, compute_financial_trends
)


def build_knowledge_for_ticker(evidence: EvidencePackage, candidate: ScreeningCandidate | None = None) -> KnowledgeProfile:
    """Bangun Knowledge Profile dari satu Evidence package.

    #1 Tren Calculation — parse price_history untuk returns, volatility
    #2 Financial Trends — compute dari fundamental fields
    #3 Field Extraction — better metrics calculation
    #4 Screening Flags — map ke Knowledge structure
    """

    # 1. Identitas & Klasifikasi
    screening_flags = list(candidate.soft_flags) if candidate else []
    # no_institutional_data baru bisa diketahui di sini (Knowledge), bukan
    # Screening — kepemilikan institusional cuma ada setelah Evidence fetch
    # Yahoo .info, panggilan yang sengaja tidak dilakukan di Screening biar
    # tetap murah di skala full-market (lihat sources/yahoo_evidence.py).
    if not evidence.institutional_ownership.percentage:
        screening_flags.append("no_institutional_data")
    size_category = infer_size_category(evidence.price_market.market_cap, screening_flags)
    sector = evidence.fundamental.sector

    # #1: TREN CALCULATION — Parse price_history
    # (high_52w/low_52w tidak dihitung ulang di sini — sudah tersedia langsung
    # dari Evidence via evidence.price_market.high_52w/low_52w dari Yahoo)
    price_history = evidence.price_market.price_history or []
    returns = calculate_returns(price_history)
    volatility = calculate_volatility(price_history)

    # 2. Kesehatan Finansial
    # #2: Compute trends dari quarterly data jika ada
    trends = compute_financial_trends(evidence.fundamental.quarterly_data)

    # #3: FIELD EXTRACTION — dihitung di sini (bukan di bawah) supaya
    # metrics['net_margin_pct'] bisa dipakai sebagai fallback net_margin_q4
    # yang benar kalau data kuartalan kosong (lihat net_margin_trend di bawah)
    metrics = calculate_financial_metrics(
        revenue=evidence.fundamental.revenue,
        net_income=evidence.fundamental.net_income,
        free_cash_flow=evidence.fundamental.free_cash_flow,
        market_cap=evidence.price_market.market_cap,
        shares_outstanding=evidence.price_market.shares_outstanding,
        last_price=evidence.price_market.last_price,
        eps=evidence.fundamental.eps
    )

    # Nominal CapEx per kuartal dari quarterly_data — quarterly_data[0] =
    # kuartal terbaru (q4), [1]=q3, [2]=q2, [3]=q1, sama seperti pemetaan
    # di compute_financial_trends().
    qdata = evidence.fundamental.quarterly_data or []
    capex_nominal = {}
    for i, period in enumerate(qdata[:4]):
        q_key = f"capex_nominal_q{4 - i}"
        capex_nominal[q_key] = getattr(period, "capital_expenditures", None)

    financial_health = FinancialHealth(
        revenue_trend=RevenueTrend(
            yoy_q1=trends.get('revenue_yoy_q1'),
            yoy_q2=trends.get('revenue_yoy_q2'),
            yoy_q3=trends.get('revenue_yoy_q3'),
            yoy_q4=trends.get('revenue_yoy_q4')
        ),
        gross_margin_trend=MarginTrend(
            q1=trends.get('gross_margin_q1'),
            q2=trends.get('gross_margin_q2'),
            q3=trends.get('gross_margin_q3'),
            q4=trends.get('gross_margin_q4')
        ),
        operating_margin_trend=MarginTrend(
            q1=trends.get('operating_margin_q1'),
            q2=trends.get('operating_margin_q2'),
            q3=trends.get('operating_margin_q3'),
            q4=trends.get('operating_margin_q4')
        ),
        net_margin_trend=MarginTrend(
            q1=trends.get('net_margin_q1'),
            q2=trends.get('net_margin_q2'),
            q3=trends.get('net_margin_q3'),
            # Fallback kalau data kuartalan kosong: net_income/revenue TTM
            # dari fundamental (metrics['net_margin_pct']) — BUKAN
            # operating_margin seperti sebelumnya, yang mensubstitusi metrik
            # yang beda sama sekali sebagai "net margin".
            q4=trends.get('net_margin_q4') if trends.get('net_margin_q4') is not None else metrics['net_margin_pct']
        ),
        balance_sheet=BalanceSheet(
            debt_to_equity=evidence.fundamental.debt_to_equity,
            current_ratio=evidence.fundamental.current_ratio,
            quick_ratio=evidence.fundamental.quick_ratio
        ),
        cash_flow_trend=CashFlowTrend(
            fcf_q4=evidence.fundamental.free_cash_flow,
            fcf_margin_q4=_fcf_margin_pct(evidence.fundamental.free_cash_flow, evidence.fundamental.revenue)
        ),
        capex_info=CapExInfo(
            capex_nominal_q1=capex_nominal.get('capex_nominal_q1'),
            capex_nominal_q2=capex_nominal.get('capex_nominal_q2'),
            capex_nominal_q3=capex_nominal.get('capex_nominal_q3'),
            capex_nominal_q4=capex_nominal.get('capex_nominal_q4'),
            capex_pct_revenue_q4=trends.get('capex_pct_revenue_q4')
        )
    )

    # 3a. Struktur Kompetitif
    competitive_structure = CompetitiveStructure(
        business_model=None,  # TODO: infer dari industry
        total_revenue_ttm=evidence.fundamental.revenue
    )

    # 3b. Momentum — spec 03_KNOWLEDGE.md §3b.
    # Hanya acceleration_signal yang derivable dari Evidence saat ini: dibangun
    # dari revenue_yoy_q3/q4 (trends, dihitung di atas via compute_financial_trends)
    # — deskripsi faktual murni ("growth accelerating/decelerating"), sama
    # seperti contoh di spec, tanpa kata sifat evaluatif.
    # segment_growth & guidance_trend tetap None: Evidence tidak mengumpulkan
    # revenue per segmen (butuh parsing 10-K segment reporting) atau data
    # guidance vs konsensus analis — dua-duanya sumber data yang belum ada di
    # Evidence stage, bukan bug di Knowledge.
    competitive_momentum = CompetitiveMomentum(
        segment_growth=None,
        guidance_trend=None,
        acceleration_signal=_compute_acceleration_signal(trends)
    )

    # 4. Tren Historis
    # #1: use calculated returns & volatility
    historical_trend = HistoricalTrend(
        return_1y=returns.get('return_1y'),
        return_3y=returns.get('return_3y'),
        return_5y=returns.get('return_5y'),
        volatility_daily=volatility,
        beta=evidence.price_market.beta
    )

    # 5. Kepemilikan
    ownership = Ownership(
        institutional_pct=evidence.institutional_ownership.percentage,
        insider_transactions=[]  # TODO: dari news/SEC filings
    )

    # 6. Valuasi
    # #3: FIELD EXTRACTION — metrics sudah dihitung di atas (dipakai juga
    # untuk fallback net_margin_q4)
    valuation = Valuation(
        pe_ratio_trailing=evidence.fundamental.pe_ratio,
        ps_ratio=metrics['ps_ratio'],
        ev_ebitda=None,  # TODO: compute jika EBITDA ada
        pb_ratio=evidence.fundamental.book_value_per_share,
        fcf_yield=metrics['fcf_yield_pct']
    )

    # 7. Governance — spec 03_KNOWLEDGE.md §7.
    governance = _build_governance(evidence)

    # Count completed fields untuk Confidence downstream
    completed_fields, expected_fields = _count_completed_fields(
        returns, volatility, financial_health, ownership, valuation
    )

    # Metadata
    metadata = KnowledgeMetadata(
        evidence_date=evidence.generated_at,
        method_version="1.1",
        fields_completed=completed_fields,
        fields_expected=expected_fields,
        sources_used=_extract_sources(evidence),
        data_quality_notes=_generate_quality_notes(evidence, returns, volatility)
    )

    return KnowledgeProfile(
        ticker=evidence.ticker,
        exchange=evidence.exchange,
        sector=sector,
        size_category=size_category,
        screening_flags=screening_flags,
        financial_health=financial_health,
        competitive_structure=competitive_structure,
        competitive_momentum=competitive_momentum,
        historical_trend=historical_trend,
        ownership=ownership,
        valuation=valuation,
        governance=governance,
        metadata=metadata
    )


def _fcf_margin_pct(fcf: float | None, revenue: float | None) -> float | None:
    """Calculate FCF margin % (FCF / Revenue)."""
    if not fcf or not revenue or revenue <= 0:
        return None
    return (fcf / revenue) * 100


def _count_completed_fields(returns: dict, volatility: float | None, financial_health, ownership, valuation) -> tuple[int, int]:
    """#5: Count non-null fields untuk data quality tracking.

    Returns (fields_completed, fields_expected) — keduanya dihitung dari list
    checks yang sama, supaya fields_expected otomatis selalu sama dengan
    jumlah field yang benar-benar dicek di sini (sebelumnya fields_expected
    di-hardcode ke 50 di caller padahal cuma ~13 field yang pernah dicek).
    """
    checks = [
        returns.get('return_1y'),
        returns.get('return_3y'),
        returns.get('return_5y'),
        volatility,
        financial_health.balance_sheet.debt_to_equity,
        financial_health.balance_sheet.current_ratio,
        financial_health.balance_sheet.quick_ratio,
        financial_health.cash_flow_trend.fcf_q4,
        ownership.institutional_pct,
        valuation.pe_ratio_trailing,
        valuation.ps_ratio,
        valuation.pb_ratio,
        valuation.fcf_yield,
    ]
    fields_completed = sum(1 for v in checks if v)
    fields_expected = len(checks)
    return fields_completed, fields_expected


def _extract_sources(evidence: EvidencePackage) -> list[str]:
    """Extract source list dari Evidence metadata."""
    sources = set()

    if evidence.price_market.metadata.status != "missing":
        sources.add(evidence.price_market.metadata.source)
    if evidence.fundamental.metadata.status != "missing":
        sources.add(evidence.fundamental.metadata.source)
    if evidence.institutional_ownership.metadata.status != "missing":
        sources.add(evidence.institutional_ownership.metadata.source)
    if evidence.news.metadata and evidence.news.metadata.status != "missing":
        sources.add(evidence.news.metadata.source)
    if evidence.sec_filings.metadata and evidence.sec_filings.metadata.status != "missing":
        sources.add(evidence.sec_filings.metadata.source)

    return sorted(list(sources))


def _generate_quality_notes(evidence: EvidencePackage, returns: dict, volatility: float | None) -> str | None:
    """#5: Generate data quality notes untuk flag issues."""
    notes = []

    # Price history
    price_hist_count = len(evidence.price_market.price_history) if evidence.price_market.price_history else 0
    if price_hist_count < 100:
        notes.append(f"Limited price history ({price_hist_count} bars)")

    # Fundamental gaps
    if not evidence.fundamental.revenue:
        notes.append("Revenue missing")
    if evidence.fundamental.net_income is None:
        notes.append("Net income missing")
    if not evidence.fundamental.free_cash_flow:
        notes.append("FCF missing")

    # Ownership gaps
    if not evidence.institutional_ownership.percentage:
        notes.append("Institutional ownership missing")

    # News gap
    news_count = len(evidence.news.news) if evidence.news and evidence.news.news else 0
    if news_count == 0:
        notes.append("No news data")

    return " | ".join(notes) if notes else None


def _compute_acceleration_signal(trends: dict) -> str | None:
    """#3b Momentum: bandingkan revenue YoY growth kuartal terakhir (q4) vs
    kuartal sebelumnya (q3) — sinyal deskriptif murni angka, tanpa kata sifat
    evaluatif (spec 03_KNOWLEDGE.md §3b, contoh: "QoQ growth accelerating").

    trends di sini adalah dict hasil compute_financial_trends() yang sudah
    dihitung di build_knowledge_for_ticker (bukan panggilan baru ke Evidence —
    invariant Knowledge murni per-ticker tetap utuh).
    """
    yoy_q3 = trends.get('revenue_yoy_q3')
    yoy_q4 = trends.get('revenue_yoy_q4')
    if yoy_q3 is None or yoy_q4 is None:
        return None

    delta = yoy_q4 - yoy_q3
    if delta > 0:
        return f"Revenue YoY growth accelerating: {yoy_q3:.1f}% (Q-1) -> {yoy_q4:.1f}% (Q terkini)"
    elif delta < 0:
        return f"Revenue YoY growth decelerating: {yoy_q3:.1f}% (Q-1) -> {yoy_q4:.1f}% (Q terkini)"
    else:
        return f"Revenue YoY growth flat: {yoy_q4:.1f}% (Q terkini, tidak berubah dari Q-1)"


def _build_governance(evidence: EvidencePackage) -> Governance:
    """#7 Governance & Filing Events (spec 03_KNOWLEDGE.md §7).

    Derivable dari Evidence saat ini:
      - unusual_filings: filing amandemen (form_type diakhiri "/A" — 10-K/A,
        10-Q/A, 8-K/A) dari sec_edgar.py fetch_sec_filings(). Amandemen filing
        itu sendiri adalah fakta ("filing tidak biasa"), bukan interpretasi —
        cocok dengan contoh spec ("filing tidak biasa lainnya").

    TIDAK derivable dari Evidence saat ini (sengaja dibiarkan kosong/None,
    bukan bug — butuh data yang belum dikumpulkan di Evidence stage):
      - shares_outstanding_change_12m: Evidence cuma simpan shares_outstanding
        snapshot SAAT INI (Yahoo fast_info, lihat sources/yahoo_evidence.py),
        bukan angka 12 bulan lalu — tidak ada baseline untuk hitung % perubahan.
      - auditor_changes / restatements / material_litigation: butuh parsing isi
        filing (mis. item number 8-K 4.01 untuk auditor change, 4.02 untuk
        restatement, atau teks litigation disclosure). sec_edgar.py cuma
        menyimpan form_type + tanggal + URL filing, bukan isi/item filing.
    """
    unusual_filings: list[GovernanceEvent] = []
    for f in evidence.sec_filings.filings or []:
        if f.form_type and f.form_type.endswith("/A"):
            unusual_filings.append(GovernanceEvent(
                event_type="filing_amendment",
                date=f.filing_date,
                description=f"{f.form_type} filed (amended filing)"
            ))

    return Governance(
        shares_outstanding_change_12m=None,
        auditor_changes=[],
        restatements=[],
        material_litigation=[],
        unusual_filings=unusual_filings
    )


def run_knowledge(evidence_packages: list[EvidencePackage], screening_candidates: list[ScreeningCandidate] | None = None) -> list[KnowledgeProfile]:
    """Jalankan Knowledge generation untuk semua Evidence packages."""
    candidates_map = {}
    if screening_candidates:
        candidates_map = {c.ticker: c for c in screening_candidates}

    profiles = []
    total = len(evidence_packages)

    for i, evidence in enumerate(evidence_packages, 1):
        if i % 10 == 0 or i == 1:
            print(f"Knowledge {i}/{total}: {evidence.ticker}", file=sys.stderr)

        try:
            candidate = candidates_map.get(evidence.ticker)
            profile = build_knowledge_for_ticker(evidence, candidate)
            profiles.append(profile)
        except Exception as e:
            print(f"Error building knowledge for {evidence.ticker}: {e}", file=sys.stderr)

    print(f"Knowledge complete: {len(profiles)} profiles", file=sys.stderr)
    return profiles
