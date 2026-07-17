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


def build_knowledge_for_ticker(evidence: EvidencePackage, candidate: ScreeningCandidate | None = None) -> KnowledgeProfile:
    """Bangun Knowledge Profile dari satu Evidence package."""

    # 1. Identitas & Klasifikasi
    screening_flags = candidate.soft_flags if candidate else []
    size_category = candidate.size_category if candidate else None
    sector = None  # TODO: map dari industry/company type jika ada di Evidence

    # 2. Kesehatan Finansial
    # TODO: Extend Evidence.price_history untuk compute revenue/margin trend
    # Untuk MVP: basic fields dari fundamental
    financial_health = FinancialHealth(
        revenue_trend=RevenueTrend(),
        gross_margin_trend=MarginTrend(),
        operating_margin_trend=MarginTrend(),
        net_margin_trend=MarginTrend(
            q4=evidence.fundamental.operating_margin  # placeholder
        ),
        balance_sheet=BalanceSheet(
            debt_to_equity=evidence.fundamental.debt_to_equity,
            current_ratio=evidence.fundamental.current_ratio,
            quick_ratio=evidence.fundamental.quick_ratio
        ),
        cash_flow_trend=CashFlowTrend(
            fcf_q4=evidence.fundamental.free_cash_flow
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
    historical_trend = HistoricalTrend(
        beta=evidence.price_market.beta
    )

    # 5. Kepemilikan
    ownership = Ownership(
        institutional_pct=evidence.institutional_ownership.percentage,
        insider_transactions=[]  # TODO: dari news/SEC filings
    )

    # 6. Valuasi
    valuation = Valuation(
        pe_ratio_trailing=evidence.fundamental.pe_ratio,
        ps_ratio=evidence.fundamental.pe_ratio,  # Placeholder
        pb_ratio=evidence.fundamental.book_value_per_share,
        fcf_yield=_calculate_fcf_yield(evidence.fundamental.free_cash_flow, evidence.price_market.market_cap)
    )

    # 7. Governance
    governance = Governance()

    # Metadata
    metadata = KnowledgeMetadata(
        evidence_date=evidence.generated_at,
        method_version="1.0",
        fields_completed=0,  # TODO: count non-null fields
        fields_expected=50,  # Rough estimate
        sources_used=["yahoo_finance", "finnhub", "sec_edgar"]
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


def _calculate_fcf_yield(fcf: float | None, market_cap: float | None) -> float | None:
    """Calculate FCF yield (FCF / Market Cap %)."""
    if not fcf or not market_cap or market_cap <= 0:
        return None
    return (fcf / market_cap) * 100


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
