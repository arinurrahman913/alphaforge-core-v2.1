"""Parse SEC EDGAR 10-K/10-Q filings untuk extract quarterly fundamental data.

SEC menyediakan free JSON access ke company facts via XBRL converter.
Endpoint: https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK=<cik>&type=10-K&dateb=&owner=exclude&count=10&output=json

Lihat: https://www.sec.gov/cgi-bin/viewer?action=view&cik=<cik>&accession_number=<accession>&xbrl_type=v
"""
from __future__ import annotations

import requests
from datetime import datetime, timezone


def get_cik_from_ticker(ticker: str) -> str | None:
    """Lookup CIK dari ticker via SEC company_tickers.json."""
    try:
        # Note: SEC endpoint sometimes blocks direct access. Fallback ke simple mapping.
        # For production, cache this lookup hasil
        url = "https://www.sec.gov/files/company_tickers.json"
        resp = requests.get(url, timeout=5)
        if resp.status_code == 403:
            return None  # Endpoint blocked, return None gracefully
        resp.raise_for_status()
        data = resp.json()

        for entry in data.values():
            if entry.get("ticker", "").upper() == ticker.upper():
                return str(entry.get("cik_str", "")).zfill(10)
        return None
    except Exception:
        return None


def fetch_quarterly_financials(ticker: str, max_periods: int = 8) -> dict[str, dict] | None:
    """Fetch quarterly financial data dari SEC EDGAR.

    Returns: {
        'periods': [
            {
                'period': '2024-Q1',  # atau '2024-09-30' format
                'revenue': float,
                'gross_profit': float,
                'operating_income': float,
                'net_income': float,
                'cash_from_operations': float,
                'capital_expenditures': float,
                'date': ISO datetime
            },
            ...
        ],
        'source': 'sec_edgar',
        'last_updated': ISO datetime
    }

    Jika data tidak tersedia, return None (graceful degradation).
    """
    try:
        cik = get_cik_from_ticker(ticker)
        if not cik:
            return None

        # Try to fetch company facts (quarterly XBRL data)
        # This is more reliable than parsing HTML
        url = f"https://www.sec.gov/cgi-bin/browse-edgar"
        params = {
            "action": "getcompany",
            "CIK": cik,
            "type": "10-Q",
            "dateb": "",
            "owner": "exclude",
            "count": 40,
            "output": "json"
        }

        resp = requests.get(url, params=params, timeout=10)
        if resp.status_code == 403:
            return None  # Rate limited or blocked
        resp.raise_for_status()
        filings = resp.json()

        # Extract quarterly data dari filing list
        # For MVP, just mark as attempted but return None (full parsing would require XML/JSON XBRL parsing)
        # This is intentionally limited to show requirement for full implementation
        periods = []

        for filing in filings.get("filings", {}).get("recent", [])[:max_periods]:
            form_type = filing.get("form", "")
            if form_type not in ["10-Q", "10-Q/A"]:
                continue

            filing_date = filing.get("filingDate", "")
            # Would need to fetch actual filing document and parse XBRL to extract quarterly figures
            # For now, return empty (this is placeholder showing where quarterly data would come from)

        # Return structure even if empty (shows attempt was made)
        return {
            "periods": periods,
            "source": "sec_edgar",
            "last_updated": datetime.now(timezone.utc).isoformat(),
            "status": "limited" if not periods else "ok"
        }

    except Exception:
        return None


def extract_quarterly_metrics(quarterly_data: dict | None) -> dict:
    """Extract key metrics dari quarterly financial data untuk Knowledge.

    Returns: {
        'revenue_yoy_q1': float % or None,  # YoY growth Q-3 vs prior year Q-3
        'revenue_yoy_q2': float % or None,
        'revenue_yoy_q3': float % or None,
        'revenue_yoy_q4': float % or None,
        'gross_margin_q1': float % or None,  # Q-3
        'gross_margin_q2': float % or None,
        'gross_margin_q3': float % or None,
        'gross_margin_q4': float % or None,
        'operating_margin_q1': float % or None,
        'operating_margin_q2': float % or None,
        'operating_margin_q3': float % or None,
        'operating_margin_q4': float % or None,
        'net_margin_q1': float % or None,
        'net_margin_q2': float % or None,
        'net_margin_q3': float % or None,
        'net_margin_q4': float % or None,
        'capex_pct_revenue_q1': float % or None,
        'capex_pct_revenue_q2': float % or None,
        'capex_pct_revenue_q3': float % or None,
        'capex_pct_revenue_q4': float % or None,
    }
    """
    if not quarterly_data or not quarterly_data.get("periods"):
        return {}

    periods = quarterly_data["periods"]
    if len(periods) < 4:
        return {}  # Need at least 4 quarters

    metrics = {}

    # Process last 4 quarters (most recent)
    # periods[0] is most recent, periods[1] is Q-1, etc.
    for i in range(4):
        period = periods[i]
        q_key = f"q{4-i}"  # q4, q3, q2, q1

        # YoY growth (compare to same quarter last year, typically periods[i+4])
        if len(periods) > i + 4:
            prior_year = periods[i + 4]
            if period.get("revenue") and prior_year.get("revenue"):
                yoy = ((period["revenue"] - prior_year["revenue"]) / prior_year["revenue"]) * 100
                metrics[f"revenue_yoy_{q_key}"] = yoy

        # Margins
        if period.get("gross_profit") and period.get("revenue"):
            metrics[f"gross_margin_{q_key}"] = (period["gross_profit"] / period["revenue"]) * 100
        if period.get("operating_income") and period.get("revenue"):
            metrics[f"operating_margin_{q_key}"] = (period["operating_income"] / period["revenue"]) * 100
        if period.get("net_income") and period.get("revenue"):
            metrics[f"net_margin_{q_key}"] = (period["net_income"] / period["revenue"]) * 100

        # CapEx as % of revenue
        if period.get("capital_expenditures") and period.get("revenue"):
            metrics[f"capex_pct_revenue_{q_key}"] = (period["capital_expenditures"] / period["revenue"]) * 100

    return metrics
