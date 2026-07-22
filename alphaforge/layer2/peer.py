"""Layer 2 Fase B: Peer Comparison — bandingkan ticker terhadap peer group.

Input: Knowledge profiles (entire population dari Fase A)
Output: PeerComparisonResult per ticker

Lihat 06_PEER_RELATIVE_COMPARISON.md.
"""
from __future__ import annotations

import sys
import statistics
from datetime import datetime, timezone
from .knowledge_contracts import KnowledgeProfile
from .peer_contracts import (
    PeerComparisonResult, PeerGroupInfo, PeerMetricComparison
)


def group_by_sector(profiles: list[KnowledgeProfile]) -> dict[str, list[KnowledgeProfile]]:
    """Group Knowledge profiles by sector.

    Returns: {
        'Technology': [profile1, profile2, ...],
        'Healthcare': [profile3, profile4, ...],
        ...
    }

    Sectors tanpa nama dikelompokkan jadi 'Unknown'.
    """
    groups = {}
    for profile in profiles:
        sector = profile.sector or "Unknown"
        if sector not in groups:
            groups[sector] = []
        groups[sector].append(profile)
    return groups


def calculate_percentile(ticker_value: float | None, peer_values: list[float]) -> float | None:
    """Calculate percentile position dari ticker dalam peer group.

    Percentile: 0-100, dimana 50 = median, >50 = better than median.

    Formula: (count of values <= ticker_value) / total * 100
    """
    if ticker_value is None or not peer_values:
        return None

    sorted_values = sorted(peer_values)
    count_lte = sum(1 for v in sorted_values if v <= ticker_value)
    percentile = (count_lte / len(sorted_values)) * 100
    return percentile


def calculate_metric_comparison(
    metric_name: str,
    ticker_value: float | None,
    peer_values: list[float],
    peer_tickers: list[str],
    peer_failures: list[str],
    min_group_size: int = 3
) -> PeerMetricComparison | None:
    """Calculate comparison untuk satu metrik.

    Returns: PeerMetricComparison atau None jika group terlalu kecil.
    """
    # Ambang minimum dihitung dari jumlah peer yang PUNYA nilai valid untuk
    # metrik ini (len(peer_values)), bukan dari total peer group (peer_tickers).
    # peer_tickers ukurannya sama untuk semua metrik seorang ticker, sementara
    # tiap metrik bisa punya null berbeda-beda di antar peer -- pakai
    # len(peer_tickers) di sini membuat median/percentile bisa dihitung dari
    # cuma 1-2 nilai valid sambil tetap dilabeli "ok"/"low_sample_size" seolah
    # didukung oleh seluruh peer group (lihat bug: pe_ratio_comparison AAL di
    # peer_results.json -- peer_group_count=4 tapi median==min==max, cuma 1
    # nilai valid yang masuk kalkulasi).
    group_size = len(peer_values)

    # Check minimum group size
    if group_size < min_group_size:
        return None  # Don't calculate untuk grup terlalu kecil

    status = "ok"
    if group_size < 5:
        status = "low_sample_size"

    # Calculate median + min/max
    median = statistics.median(peer_values) if peer_values else None
    min_val = min(peer_values) if peer_values else None
    max_val = max(peer_values) if peer_values else None

    # Calculate percentile
    percentile = calculate_percentile(ticker_value, peer_values)

    return PeerMetricComparison(
        metric_name=metric_name,
        ticker_value=ticker_value,
        peer_group_median=median,
        peer_group_min=min_val,
        peer_group_max=max_val,
        peer_group_count=group_size,
        percentile=percentile,
        status=status
    )


def build_peer_comparison(
    target_profile: KnowledgeProfile,
    peer_profiles: list[KnowledgeProfile],
    basis: str = "screening_universe"
) -> PeerComparisonResult:
    """Bangun Peer Comparison untuk satu ticker terhadap peer group-nya.

    target_profile: ticker yang akan dianalisis
    peer_profiles: seluruh peers dalam grup (including target)
    """
    ticker = target_profile.ticker
    exchange = target_profile.exchange

    # Exclude target dari peer group
    peers = [p for p in peer_profiles if p.ticker != ticker]
    peer_tickers = [p.ticker for p in peers]
    peer_failures = []  # TODO: track failures dari Evidence stage

    # Build peer group info
    peer_group = PeerGroupInfo(
        ticker=ticker,
        sector=target_profile.sector,
        industry=None,  # TODO: industry classification
        peer_tickers=peer_tickers,
        group_size=len(peers),
        peer_failures=peer_failures
    )

    # Extract metric values dari peers
    pe_values = [p.valuation.pe_ratio_trailing for p in peers if p.valuation.pe_ratio_trailing]
    ps_values = [p.valuation.ps_ratio for p in peers if p.valuation.ps_ratio]
    pb_values = [p.valuation.pb_ratio for p in peers if p.valuation.pb_ratio and p.valuation.pb_ratio > 0]
    fcf_yield_values = [p.valuation.fcf_yield for p in peers if p.valuation.fcf_yield]

    gm_values = [p.financial_health.gross_margin_trend.q4 for p in peers
                  if p.financial_health.gross_margin_trend.q4]
    om_values = [p.financial_health.operating_margin_trend.q4 for p in peers
                  if p.financial_health.operating_margin_trend.q4]
    nm_values = [p.financial_health.net_margin_trend.q4 for p in peers
                  if p.financial_health.net_margin_trend.q4]

    roe_values = [p.ownership.institutional_pct for p in peers if p.ownership.institutional_pct]  # TODO: proper ROE
    dte_values = [p.financial_health.balance_sheet.debt_to_equity for p in peers
                   if p.financial_health.balance_sheet.debt_to_equity]

    # Calculate comparisons
    pe_comp = calculate_metric_comparison("pe_ratio", target_profile.valuation.pe_ratio_trailing, pe_values, peer_tickers, peer_failures)
    ps_comp = calculate_metric_comparison("ps_ratio", target_profile.valuation.ps_ratio, ps_values, peer_tickers, peer_failures)
    pb_comp = calculate_metric_comparison("pb_ratio", target_profile.valuation.pb_ratio, pb_values, peer_tickers, peer_failures) if target_profile.valuation.pb_ratio and target_profile.valuation.pb_ratio > 0 else None
    fcf_comp = calculate_metric_comparison("fcf_yield", target_profile.valuation.fcf_yield, fcf_yield_values, peer_tickers, peer_failures)

    gm_comp = calculate_metric_comparison("gross_margin", target_profile.financial_health.gross_margin_trend.q4, gm_values, peer_tickers, peer_failures)
    om_comp = calculate_metric_comparison("operating_margin", target_profile.financial_health.operating_margin_trend.q4, om_values, peer_tickers, peer_failures)
    nm_comp = calculate_metric_comparison("net_margin", target_profile.financial_health.net_margin_trend.q4, nm_values, peer_tickers, peer_failures)

    roe_comp = calculate_metric_comparison("roe", None, roe_values, peer_tickers, peer_failures)  # TODO: use actual ROE
    dte_comp = calculate_metric_comparison("debt_to_equity", target_profile.financial_health.balance_sheet.debt_to_equity, dte_values, peer_tickers, peer_failures)

    return PeerComparisonResult(
        ticker=ticker,
        exchange=exchange,
        peer_group=peer_group,
        pe_ratio_comparison=pe_comp,
        ps_ratio_comparison=ps_comp,
        pb_ratio_comparison=pb_comp,
        fcf_yield_comparison=fcf_comp,
        gross_margin_comparison=gm_comp,
        operating_margin_comparison=om_comp,
        net_margin_comparison=nm_comp,
        roe_comparison=roe_comp,
        debt_to_equity_comparison=dte_comp,
        generated_at=datetime.now(timezone.utc).isoformat(),
        peer_group_basis=basis,
        low_sample_size=len(peers) < 3
    )


def run_peer_comparison(profiles: list[KnowledgeProfile]) -> list[PeerComparisonResult]:
    """Jalankan Peer Comparison untuk seluruh Knowledge population.

    Fase B: butuh complete Knowledge dari seluruh screening candidates.
    """
    # Group by sector
    sectors = group_by_sector(profiles)

    results = []
    total = len(profiles)

    for i, profile in enumerate(profiles, 1):
        if i % 50 == 0 or i == 1:
            print(f"Peer {i}/{total}: {profile.ticker}", file=sys.stderr)

        try:
            sector = profile.sector or "Unknown"
            sector_group = sectors.get(sector, [])

            if len(sector_group) >= 2:
                # peer_group_basis kontraknya cuma "screening_universe" | "manual"
                # (lihat peer_contracts.py) -- narrowing per-sektor tetap masih
                # bersumber dari populasi screening yang sama, jadi basis-nya
                # tetap "screening_universe", bukan label "sector" yang bukan
                # bagian dari kontrak.
                peer_group, basis = sector_group, "screening_universe"
            else:
                # Sektor tidak diketahui atau kepesertaannya terlalu kecil di
                # universe ini untuk perbandingan bermakna (mis. cuma 1
                # ticker di sektor itu) — dulu ticker ini di-skip total dari
                # Peer. Sekarang fallback ke seluruh screening universe
                # supaya tetap dapat hasil, dengan basis yang jujur di label.
                print(f"  Info: {profile.ticker} sector '{sector}' punya <2 peers, fallback ke screening_universe", file=sys.stderr)
                peer_group, basis = profiles, "screening_universe"

            comparison = build_peer_comparison(profile, peer_group, basis=basis)
            results.append(comparison)
        except Exception as e:
            print(f"Error for {profile.ticker}: {e}", file=sys.stderr)

    print(f"Peer Comparison complete: {len(results)} results", file=sys.stderr)
    return results
