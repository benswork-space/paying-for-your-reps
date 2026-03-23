#!/usr/bin/env python3
"""
Fetch campaign finance data from the FEC API (OpenFEC) and update member files.

Usage:
    FEC_API_KEY=your_key python3 fetch_fec.py --members P000197,S001150,P000145
    FEC_API_KEY=your_key python3 fetch_fec.py --all

Get a free key at: https://api.data.gov/signup/
Rate limit: 1,000 requests/hour with registered key.
"""
from __future__ import annotations

import json
import os
import sys
import time
import argparse
import urllib.request
import urllib.parse
from pathlib import Path

API_KEY = os.environ.get("FEC_API_KEY", "")
BASE_URL = "https://api.open.fec.gov/v1"
MEMBERS_DIR = Path(__file__).parent.parent / "civic-receipts" / "public" / "data" / "members"
CYCLE = 2024
CALLS_MADE = 0


def api_call(endpoint, params=None):
    """Make an FEC API call."""
    global CALLS_MADE
    params = params or {}
    params["api_key"] = API_KEY
    url = BASE_URL + "/" + endpoint + "?" + urllib.parse.urlencode(params, doseq=True)

    try:
        time.sleep(0.4)
        req = urllib.request.Request(url, headers={"User-Agent": "CivicReceipts/1.0"})
        with urllib.request.urlopen(req, timeout=60) as resp:
            CALLS_MADE += 1
            return json.loads(resp.read().decode())
    except Exception as e:
        print(f"  ERROR: {endpoint} failed: {e}", file=sys.stderr)
        return None


def find_candidate_id(member_data):
    """Find the FEC candidate ID for a member, trying Senate then House."""
    name = member_data["name"]
    last_name = name.split()[-1]
    chamber = member_data.get("chamber", "house")
    state = member_data.get("state", "")

    # Try current chamber first, then the other
    offices = ["S", "H"] if chamber == "senate" else ["H", "S"]

    for office in offices:
        data = api_call("candidates/search/", {
            "name": last_name,
            "cycle": CYCLE,
            "office": office,
            "state": state,
            "per_page": 20,
        })
        if not data:
            continue

        for r in data.get("results", []):
            # Match on last name being in the candidate name
            if last_name.upper() in r.get("name", "").upper():
                if r.get("active_through", 0) >= CYCLE:
                    return r["candidate_id"]

    return None


def find_committee_id(candidate_id):
    """Find the principal campaign committee for a candidate."""
    data = api_call(f"candidate/{candidate_id}/committees/", {
        "cycle": CYCLE,
        "designation": "P",  # Principal campaign committee
    })
    if not data:
        return None

    for r in data.get("results", []):
        return r["committee_id"]
    return None


def fetch_totals(candidate_id):
    """Fetch total raised/spent for a candidate."""
    data = api_call(f"candidate/{candidate_id}/totals/", {
        "cycle": CYCLE,
        "per_page": 1,
    })
    if not data or not data.get("results"):
        return None

    r = data["results"][0]
    itemized = int(r.get("individual_itemized_contributions", 0) or 0)
    unitemized = int(r.get("individual_unitemized_contributions", 0) or 0)
    pac = int(r.get("other_political_committee_contributions", 0) or 0)
    total = int(r.get("receipts", 0) or 0)
    other = total - (itemized + unitemized) - pac
    return {
        "total_raised": total,
        "total_spent": int(r.get("disbursements", 0) or 0),
        "individual_contributions": itemized + unitemized,
        "individual_itemized": itemized,
        "individual_unitemized": unitemized,
        "pac_contributions": pac,
        "other_receipts": max(other, 0),
        "cash_on_hand": int(r.get("last_cash_on_hand_end_period", 0) or 0),
    }


def fetch_top_pac_contributors(committee_id, max_pages=10):
    """Fetch PAC/organization contributors from Schedule A, paginating."""
    seen = {}
    params = {
        "committee_id": committee_id,
        "two_year_transaction_period": CYCLE,
        "sort": "-contribution_receipt_amount",
        "per_page": 100,
        "is_individual": "false",
    }

    for page in range(max_pages):
        data = api_call("schedules/schedule_a/", params)
        if not data:
            break

        for r in data.get("results", []):
            name = r.get("contributor_name", "Unknown")
            amt = r.get("contribution_receipt_amount", 0) or 0
            if name not in seen:
                seen[name] = {"name": name, "total": 0, "count": 0}
            seen[name]["total"] += amt
            seen[name]["count"] += 1

        # Cursor-based pagination
        pagination = data.get("pagination", {})
        last_indexes = pagination.get("last_indexes")
        if not last_indexes or not pagination.get("pages", 0) > page + 1:
            break
        # Add cursor params for next page
        params = {
            "committee_id": committee_id,
            "two_year_transaction_period": CYCLE,
            "sort": "-contribution_receipt_amount",
            "per_page": 100,
            "is_individual": "false",
        }
        for k, v in last_indexes.items():
            if v is not None:
                params[f"last_{k}"] = v

    contributors = sorted(seen.values(), key=lambda x: -x["total"])
    # Filter out joint fundraising transfers (they're not really "donors")
    filtered = []
    for c in contributors:
        name_upper = c["name"].upper()
        if any(skip in name_upper for skip in ["VICTORY FUND", "JOINT FUNDRAIS"]):
            continue
        filtered.append(c)

    return filtered


def fetch_top_employers(committee_id, max_pages=10):
    """Fetch all employers of individual contributors, paginating."""
    all_employers = []
    skip_names = {"NOT EMPLOYED", "SELF EMPLOYED", "SELF-EMPLOYED", "RETIRED",
                  "NONE", "NULL", "N/A", "HOMEMAKER", "INFORMATION REQUESTED",
                  "NOT APPLICABLE", "STUDENT"}

    params = {
        "committee_id": committee_id,
        "cycle": CYCLE,
        "sort": "-total",
        "per_page": 100,
    }

    for page in range(max_pages):
        data = api_call("schedules/schedule_a/by_employer/", params)
        if not data:
            break

        for r in data.get("results", []):
            name = r.get("employer", "")
            if name.upper() in skip_names or not name:
                continue
            all_employers.append({
                "name": name,
                "total": int(r.get("total", 0)),
                "count": r.get("count", 0),
            })

        # Check if there are more pages
        pagination = data.get("pagination", {})
        last_indexes = pagination.get("last_indexes")
        if not last_indexes or not pagination.get("pages", 0) > page + 1:
            break
        params = {
            "committee_id": committee_id,
            "cycle": CYCLE,
            "sort": "-total",
            "per_page": 100,
        }
        for k, v in last_indexes.items():
            if v is not None:
                params[f"last_{k}"] = v

    return all_employers


def find_leadership_pacs(candidate_id):
    """Find leadership PACs sponsored by this candidate."""
    data = api_call("committees/", {
        "sponsor_candidate_id": candidate_id,
        "cycle": CYCLE,
        "per_page": 10,
    })
    if not data:
        return []

    pacs = []
    for r in data.get("results", []):
        # Designation D = leadership PAC
        if r.get("designation") == "D":
            cmte_id = r["committee_id"]
            name = r["name"]

            # Get totals for this PAC
            totals_data = api_call(f"committee/{cmte_id}/totals/", {
                "cycle": CYCLE,
                "per_page": 1,
            })
            receipts = 0
            if totals_data and totals_data.get("results"):
                receipts = int(totals_data["results"][0].get("receipts", 0) or 0)

            # Get top contributors to this PAC
            contributors = fetch_top_pac_contributors(cmte_id)
            employers = fetch_top_employers(cmte_id)

            pacs.append({
                "committee_id": cmte_id,
                "name": name,
                "receipts": receipts,
                "contributors": contributors,
                "top_employers": employers,
            })

    return pacs


def update_member(bioguide_id):
    """Fetch and update funding data for a single member."""
    filepath = MEMBERS_DIR / f"{bioguide_id}.json"
    if not filepath.exists():
        print(f"  SKIP: No file for {bioguide_id}")
        return False

    with open(filepath) as f:
        member = json.load(f)

    print(f"  {member['name']}...")

    # Find FEC candidate ID
    candidate_id = find_candidate_id(member)
    if not candidate_id:
        print(f"    WARN: No FEC candidate ID found")
        return False
    print(f"    FEC ID: {candidate_id}")

    # Get campaign committee totals
    totals = fetch_totals(candidate_id)
    if not totals:
        print(f"    WARN: No totals found")
        return False

    # Get principal campaign committee for contribution queries
    committee_id = find_committee_id(candidate_id)
    campaign_pac_contributors = []
    campaign_top_employers = []

    if committee_id:
        print(f"    Campaign committee: {committee_id}")
        campaign_pac_contributors = fetch_top_pac_contributors(committee_id)
        campaign_top_employers = fetch_top_employers(committee_id)

    # Get leadership PACs
    leadership_pacs = find_leadership_pacs(candidate_id)
    for lp in leadership_pacs:
        print(f"    Leadership PAC: {lp['name']} ({lp['committee_id']}) — ${lp['receipts']:,}")

    # Build funding structure
    # Campaign committee data
    campaign = {
        "committee_id": committee_id,
        "total_raised": totals["total_raised"],
        "individual_contributions": totals["individual_contributions"],
        "individual_itemized": totals["individual_itemized"],
        "individual_unitemized": totals["individual_unitemized"],
        "pac_contributions": totals["pac_contributions"],
        "other_receipts": totals["other_receipts"],
        "top_employers": [
            {"name": e["name"], "type": "Organization", "amount": e["total"]}
            for e in campaign_top_employers
        ],
        "top_pac_donors": [
            {"name": c["name"], "type": "PAC", "amount": int(c["total"])}
            for c in campaign_pac_contributors
        ],
    }

    # Leadership PAC data
    leadership_pac_data = []
    for lp in leadership_pacs:
        leadership_pac_data.append({
            "committee_id": lp["committee_id"],
            "name": lp["name"],
            "total_raised": lp["receipts"],
            "top_employers": [
                {"name": e["name"], "type": "Organization", "amount": e["total"]}
                for e in lp["top_employers"]
            ],
            "top_pac_donors": [
                {"name": c["name"], "type": "PAC", "amount": int(c["total"])}
                for c in lp["contributors"]
            ],
        })

    # Combined total across all committees
    leadership_total = sum(lp["receipts"] for lp in leadership_pacs)
    combined_total = totals["total_raised"] + leadership_total

    # Build top_industries for backward compatibility + new structure
    # Merge employer data across campaign + leadership PACs
    all_employers = {}
    for e in campaign_top_employers:
        all_employers[e["name"]] = all_employers.get(e["name"], 0) + e["total"]
    for lp in leadership_pacs:
        for e in lp["top_employers"]:
            all_employers[e["name"]] = all_employers.get(e["name"], 0) + e["total"]

    sorted_employers = sorted(all_employers.items(), key=lambda x: -x[1])[:15]

    all_pac_donors = {}
    for c in campaign_pac_contributors:
        all_pac_donors[c["name"]] = all_pac_donors.get(c["name"], 0) + int(c["total"])
    for lp in leadership_pacs:
        for c in lp["contributors"]:
            all_pac_donors[c["name"]] = all_pac_donors.get(c["name"], 0) + int(c["total"])

    sorted_pac_donors = sorted(all_pac_donors.items(), key=lambda x: -x[1])[:15]

    top_industries = []
    combined_indiv = totals["individual_contributions"]
    combined_pac = totals["pac_contributions"]
    for lp in leadership_pacs:
        # Leadership PAC receipts are mostly from individuals and PACs
        combined_pac += lp["receipts"]  # Conservative: count leadership PAC as PAC money

    if combined_indiv > 0:
        top_industries.append({
            "code": "IND",
            "name": "Individual Contributions",
            "amount": combined_indiv,
            "donors": [{"name": n, "type": "Organization", "amount": a} for n, a in sorted_employers],
        })

    if combined_pac > 0 or leadership_total > 0:
        top_industries.append({
            "code": "PAC",
            "name": "PAC & Committee Contributions",
            "amount": totals["pac_contributions"],
            "donors": [{"name": n, "type": "PAC", "amount": a} for n, a in sorted_pac_donors],
        })

    if leadership_total > 0:
        top_industries.append({
            "code": "LPAC",
            "name": "Leadership PAC",
            "amount": leadership_total,
            "donors": [{"name": n, "type": "PAC", "amount": a} for n, a in sorted_pac_donors],
            "details": leadership_pac_data,
        })

    # Update member data
    member["funding"] = {
        "cycle": str(CYCLE),
        "total_raised": combined_total,
        "campaign_raised": totals["total_raised"],
        "leadership_pac_raised": leadership_total,
        "top_industries": top_industries,
        "campaign": campaign,
        "leadership_pacs": leadership_pac_data,
    }

    # Save FEC metadata in sidecar
    fec_file = MEMBERS_DIR / f"{bioguide_id}_fec.json"
    with open(fec_file, "w") as f:
        json.dump({
            "bioguide_id": bioguide_id,
            "fec_candidate_id": candidate_id,
            "fec_committee_id": committee_id,
            "cycle": CYCLE,
            "totals": totals,
            "campaign_pac_contributors": campaign_pac_contributors,
            "campaign_top_employers": campaign_top_employers,
            "leadership_pacs": leadership_pacs,
        }, f, indent=2)

    # Save updated member
    with open(filepath, "w") as f:
        json.dump(member, f, indent=2)

    lp_str = f" + ${leadership_total:,} leadership PAC" if leadership_total else ""
    print(f"    ${totals['total_raised']:,} campaign{lp_str} = ${combined_total:,} total")
    return True


def main():
    parser = argparse.ArgumentParser(description="Fetch FEC finance data")
    parser.add_argument("--members", help="Comma-separated bioguide IDs")
    parser.add_argument("--all", action="store_true", help="Process all members")
    args = parser.parse_args()

    if not API_KEY:
        print("ERROR: Set FEC_API_KEY environment variable", file=sys.stderr)
        print("Get a free key at: https://api.data.gov/signup/")
        sys.exit(1)

    if args.all:
        member_ids = [f.stem for f in MEMBERS_DIR.glob("*.json") if "_" not in f.stem]
    elif args.members:
        member_ids = args.members.split(",")
    else:
        print("Specify --members or --all")
        sys.exit(1)

    print(f"Cycle: {CYCLE}")
    print(f"Processing {len(member_ids)} members...\n")

    success = 0
    for bid in member_ids:
        if update_member(bid.strip()):
            success += 1

    print(f"\nDone. Updated {success}/{len(member_ids)} members. API calls: {CALLS_MADE}")


if __name__ == "__main__":
    main()
