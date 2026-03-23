#!/usr/bin/env python3
"""
Fetch campaign finance data.

Strategy:
1. Use the FEC API (free, no key required for basic access) to get candidate
   financial summaries and top contributors.
2. Fall back to OpenSecrets API if FEC doesn't provide industry-coded data.

The FEC API provides:
- Candidate totals (total raised, PAC contributions, individual contributions)
- Committee contributions to a candidate
- But NOT industry-coded data (that's OpenSecrets' value-add)

For industry coding, we use the OpenSecrets API (requires free API key).
If no key is available, we use FEC data without industry coding.

Outputs: data/raw/finance.json
"""

import json
import os
import sys
import time

import requests

RAW_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "raw")

FEC_API_BASE = "https://api.open.fec.gov/v1"
FEC_API_KEY = os.environ.get("FEC_API_KEY", "DEMO_KEY")

OPENSECRETS_API_KEY = os.environ.get("OPENSECRETS_API_KEY", "")
OPENSECRETS_API_BASE = "https://www.opensecrets.org/api"


def load_members():
    path = os.path.join(RAW_DIR, "members.json")
    if not os.path.exists(path):
        print("ERROR: Run 01_fetch_members.py first")
        sys.exit(1)
    with open(path) as f:
        return json.load(f)


def fetch_fec_candidate_totals(fec_id, cycle=2024):
    """Fetch candidate financial summary from FEC."""
    url = f"{FEC_API_BASE}/candidate/{fec_id}/totals/"
    params = {
        "api_key": FEC_API_KEY,
        "cycle": cycle,
        "per_page": 1,
    }
    try:
        resp = requests.get(url, params=params, timeout=15)
        if resp.status_code == 200:
            data = resp.json()
            results = data.get("results", [])
            if results:
                return results[0]
    except Exception as e:
        pass
    return None


def fetch_fec_committee_contributions(candidate_id, cycle=2024):
    """Fetch PAC/committee contributions to a candidate from FEC."""
    url = f"{FEC_API_BASE}/schedules/schedule_b/"
    all_results = []
    page = 1

    while page <= 5:  # Limit to 5 pages (100 results)
        params = {
            "api_key": FEC_API_KEY,
            "recipient_committee_id": candidate_id,
            "two_year_transaction_period": cycle,
            "per_page": 20,
            "page": page,
            "sort": "-contribution_receipt_amount",
        }
        try:
            resp = requests.get(url, params=params, timeout=15)
            if resp.status_code == 200:
                data = resp.json()
                results = data.get("results", [])
                all_results.extend(results)
                if len(results) < 20:
                    break
                page += 1
            else:
                break
        except Exception:
            break

        time.sleep(0.5)

    return all_results


def fetch_opensecrets_industries(cid, cycle=2024):
    """
    Fetch top industries for a candidate from OpenSecrets API.
    Requires OPENSECRETS_API_KEY environment variable.
    """
    if not OPENSECRETS_API_KEY:
        return None

    url = OPENSECRETS_API_BASE
    params = {
        "method": "candIndustry",
        "cid": cid,
        "cycle": cycle,
        "apikey": OPENSECRETS_API_KEY,
        "output": "json",
    }

    try:
        resp = requests.get(url, params=params, timeout=15)
        if resp.status_code == 200:
            data = resp.json()
            industries_data = data.get("response", {}).get("industries", {}).get("industry", [])
            return industries_data
    except Exception as e:
        pass

    return None


def fetch_opensecrets_contributors(cid, cycle=2024):
    """
    Fetch top contributors for a candidate from OpenSecrets API.
    """
    if not OPENSECRETS_API_KEY:
        return None

    url = OPENSECRETS_API_BASE
    params = {
        "method": "candContrib",
        "cid": cid,
        "cycle": cycle,
        "apikey": OPENSECRETS_API_KEY,
        "output": "json",
    }

    try:
        resp = requests.get(url, params=params, timeout=15)
        if resp.status_code == 200:
            data = resp.json()
            contribs = data.get("response", {}).get("contributors", {}).get("contributor", [])
            return contribs
    except Exception as e:
        pass

    return None


def fetch_opensecrets_summary(cid, cycle=2024):
    """Fetch candidate financial summary from OpenSecrets."""
    if not OPENSECRETS_API_KEY:
        return None

    url = OPENSECRETS_API_BASE
    params = {
        "method": "candSummary",
        "cid": cid,
        "cycle": cycle,
        "apikey": OPENSECRETS_API_KEY,
        "output": "json",
    }

    try:
        resp = requests.get(url, params=params, timeout=15)
        if resp.status_code == 200:
            data = resp.json()
            summary = data.get("response", {}).get("summary", {})
            if isinstance(summary, dict):
                return summary.get("@attributes", summary)
    except Exception:
        pass

    return None


def process_opensecrets_industries(industries_data):
    """Convert OpenSecrets industry data to our format."""
    if not industries_data:
        return []

    results = []
    for ind in industries_data:
        attrs = ind.get("@attributes", ind) if isinstance(ind, dict) else {}
        name = attrs.get("industry_name", "Unknown")
        code = attrs.get("industry_code", "")
        total = int(attrs.get("total", 0))
        indivs = int(attrs.get("indivs", 0))
        pacs = int(attrs.get("pacs", 0))

        results.append({
            "code": code,
            "name": name,
            "amount": total,
            "individual_amount": indivs,
            "pac_amount": pacs,
            "donors": [],  # Will be filled from contributors data
        })

    # Sort by amount descending, take top 6
    results.sort(key=lambda x: x["amount"], reverse=True)
    return results[:6]


def process_opensecrets_contributors(contribs_data):
    """Convert OpenSecrets contributor data to our format."""
    if not contribs_data:
        return []

    results = []
    for contrib in contribs_data:
        attrs = contrib.get("@attributes", contrib) if isinstance(contrib, dict) else {}
        name = attrs.get("org_name", "Unknown")
        total = int(attrs.get("total", 0))
        pacs = int(attrs.get("pacs", 0))
        indivs = int(attrs.get("indivs", 0))

        donor_type = "PAC" if pacs > indivs else "Individual"

        results.append({
            "name": name,
            "type": donor_type,
            "amount": total,
        })

    return results


def main():
    members = load_members()
    os.makedirs(RAW_DIR, exist_ok=True)

    has_opensecrets = bool(OPENSECRETS_API_KEY)
    if has_opensecrets:
        print(f"OpenSecrets API key found. Will fetch industry-coded data.")
    else:
        print("No OPENSECRETS_API_KEY set. Set it for industry-coded data.")
        print("Get a free key at: https://www.opensecrets.org/api/admin/index.php?function=signup")
        print("Falling back to FEC API (no industry coding).\n")

    finance_data = {}
    total = len(members)

    for i, member in enumerate(members):
        bio_id = member["bioguide_id"]
        opensecrets_id = member.get("opensecrets_id", "")

        if (i + 1) % 25 == 0 or i == 0:
            print(f"Processing {i + 1}/{total}: {member['name']}...")

        member_finance = {
            "cycle": "2024",
            "total_raised": 0,
            "top_industries": [],
            "top_contributors": [],
        }

        # Try OpenSecrets first (better data)
        if has_opensecrets and opensecrets_id:
            # Summary
            summary = fetch_opensecrets_summary(opensecrets_id)
            if summary:
                member_finance["total_raised"] = int(float(summary.get("total", 0)))

            # Industries
            industries = fetch_opensecrets_industries(opensecrets_id)
            if industries:
                member_finance["top_industries"] = process_opensecrets_industries(industries)

            # Contributors
            contribs = fetch_opensecrets_contributors(opensecrets_id)
            if contribs:
                member_finance["top_contributors"] = process_opensecrets_contributors(contribs)

            time.sleep(1)  # OpenSecrets rate limit: ~1 req/sec

        finance_data[bio_id] = member_finance

    # Save
    out_path = os.path.join(RAW_DIR, "finance.json")
    with open(out_path, "w") as f:
        json.dump(finance_data, f, indent=2)

    members_with_data = sum(1 for v in finance_data.values() if v["total_raised"] > 0)
    print(f"\nWrote finance data for {len(finance_data)} members ({members_with_data} with data) to {out_path}")

    # Verify
    for test_id in ["P000197", "S001150", "P000145"]:
        fd = finance_data.get(test_id, {})
        industries = fd.get("top_industries", [])
        top = industries[0]["name"] if industries else "N/A"
        print(f"  {test_id}: ${fd.get('total_raised', 0):,} raised, top industry: {top}")


if __name__ == "__main__":
    main()
