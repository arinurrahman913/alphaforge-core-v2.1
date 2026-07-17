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
    CompetitiveStructure, CompetitiveMomentum, HistoricalTrend, Valuation, Governance
)
from .knowledge_helpers import (
    calculate_returns, calculate_volatility, calculate_high_low_52w,
    calculate_financial_metrics, infer_size_category
)


def build_knowledge_for_ticker(evidence: EvidencePackage, candidate: ScreeningCandidate | None = None) -> KnowledgeProfile:
    """Bangun Knowledge Profile dari satu Evidence package.

    #1 Tren Calculation — parse price_history untuk returns, volatility
    #2 Financial Trends — compute dari fundamental fields
    #3 Field Extraction — better metrics calculation
    #4 Screening Flags — map ke Knowledge structure
    """

    # 1. Identitas & Klasifikasi
    screening_flags = candidate.soft_flags if candidate else []
    size_category = infer_size_category(evidence.price_market.market_cap, screening_flags)
    sector = None  # TODO: map dari industry/company type jika ada di Evidence

    # #1: TREN CALCULATION — Parse price_history
    price_history = evidence.price_market.price_history or []
    returns = calculate_returns(price_history)
    volatility = calculate_volatility(price_history)
    high_low = calculate_high_low_52w(price_history)

    # 2. Kesehatan Finansial
    financial_health = FinancialHealth(
        revenue_trend=RevenueTrend(),  # TODO: #2 — compute YoY jika quarterly data ada
        gross_margin_trend=MarginTrend(),
        operating_margin_trend=MarginTrend(),
        net_margin_trend=MarginTrend(
            q4=evidence.fundamental.operating_margin
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
        capex_info=CapExInfo()
    )

    # 3a. Struktur Kompetitif
    competitive_structure = CompetitiveStructure(
        business_model=None,  # TODO: infer dari industry
        total_revenue_ttm=evidence.fundamental.revenue
    )

    # 3b. Momentum
    competitive_momentum = CompetitiveMomentum()

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
    # #3: FIELD EXTRACTION — better metrics
    metrics = calculate_financial_metrics(
        revenue=evidence.fundamental.revenue,
        net_income=evidence.fundamental.net_income,
        free_cash_flow=evidence.fundamental.free_cash_flow,
        market_cap=evidence.price_market.market_cap,
        shares_outstanding=evidence.price_market.shares_outstanding,
        last_price=evidence.price_market.last_price,
        eps=evidence.fundamental.eps
    )

    valuation = Valuation(
        pe_ratio_trailing=evidence.fundamental.pe_ratio,
        ps_ratio=metrics['ps_ratio'],
        ev_ebitda=None,  # TODO: compute jika EBITDA ada
        pb_ratio=evidence.fundamental.book_value_per_share,
        fcf_yield=metrics['fcf_yield_pct']
    )

    # 7. Governance
    governance = Governance()

    # Count completed fields untuk Confidence downstream
    completed_fields = _count_completed_fields(
        returns, volatility, financial_health, ownership, valuation
    )

    # Metadata
    metadata = KnowledgeMetadata(
        evidence_date=evidence.generated_at,
        method_version="1.1",
        fields_completed=completed_fields,
        fields_expected=50,
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


def _count_completed_fields(returns: dict, volatility: float | None, financial_health, ownership, valuation) -> int:
    """#5: Count non-null fields untuk data quality tracking."""
    count = 0

    # Returns
    if returns.get('return_1y'): count += 1
    if returns.get('return_3y'): count += 1
    if returns.get('return_5y'): count += 1

    # Volatility
    if volatility: count += 1

    # Financial
    if financial_health.balance_sheet.debt_to_equity: count += 1
    if financial_health.balance_sheet.current_ratio: count += 1
    if financial_health.balance_sheet.quick_ratio: count += 1
    if financial_health.cash_flow_trend.fcf_q4: count += 1

    # Ownership
    if ownership.institutional_pct: count += 1

    # Valuation
    if valuation.pe_ratio_trailing: count += 1
    if valuation.ps_ratio: count += 1
    if valuation.pb_ratio: count += 1
    if valuation.fcf_yield: count += 1

    return count


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
