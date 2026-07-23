#!/usr/bin/env python3
"""Inspect actual TSLA Form 4 filing details dari SEC."""
import sys
sys.path.insert(0, ".")

import requests
from alphaforge.layer2.sources.sec_parser import SEC_USER_AGENT, apply_sec_rate_limit

_HEADERS = {"User-Agent": SEC_USER_AGENT}

# TSLA Form 4 archive from our earlier test
# Try to fetch and parse actual filing to see transaction details
url = "https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK=0001318605&type=4&dateb=&owner=exclude&count=100"

print("Fetching TSLA Form 4 listing from SEC EDGAR...\n")
apply_sec_rate_limit()
try:
    r = requests.get(url, headers=_HEADERS, timeout=15)
    r.raise_for_status()

    # Extract Form 4 filing links
    import re
    # Look for filing links
    matches = re.findall(r'<td><a href="(/Archives/edgar/data/\d+/\d+/[^"]*)"[^>]*>([^<]+)</a></td>', r.text)

    print(f"Found {len(matches)} Form 4 filing links\n")
    for i, (href, text) in enumerate(matches[:5]):
        print(f"{i+1}. {text}")
        print(f"   Path: {href}\n")

        # Try to find the actual Form 4 document link
        if i == 0:  # Get latest filing
            full_url = f"https://www.sec.gov{href}"
            print(f"   Fetching: {full_url}")
            apply_sec_rate_limit()

            try:
                r_filing = requests.get(full_url, headers=_HEADERS, timeout=15)

                # Extract transaction table data
                if "<table" in r_filing.text:
                    # Look for "Derivative" and "Non-Derivative" sections
                    import re

                    # Simple extraction: look for transaction patterns
                    transactions = re.findall(
                        r'<td[^>]*>([^<]*Shares?[^<]*)</td>.*?<td[^>]*>([^<]*[0-9.,]+[^<]*)</td>',
                        r_filing.text, re.IGNORECASE | re.DOTALL
                    )

                    if transactions:
                        print(f"   Found transaction details:")
                        for t in transactions[:3]:
                            print(f"     - {t[0][:50]} @ {t[1][:50]}")
                    else:
                        print(f"   (HTML structure complex, may need better parsing)")

            except Exception as e:
                print(f"   Error fetching filing: {e}")

            break

except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
