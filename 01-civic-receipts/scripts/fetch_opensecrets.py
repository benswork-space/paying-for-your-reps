#!/usr/bin/env python3
"""
Fetch funding data from OpenSecrets API and update member JSON files.

Usage:
    OPENSECRETS_API_KEY=your_key python3 fetch_opensecrets.py [--members P000197,S001150] [--cycle 2024] [--all]

Rate limit: 200 calls/day. Each member requires 2 calls (candIndustry + candContrib).
So ~100 members/day max. Use --members for targeted fetches.
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

API_KEY = os.environ.get("OPENSECRETS_API_KEY", "")
BASE_URL = "https://www.opensecrets.org/api/"
MEMBERS_DIR = Path(__file__).parent.parent / "civic-receipts" / "public" / "data" / "members"
CYCLE = "2024"
CALLS_MADE = 0


def api_call(method: str, params: dict) -> dict | None:
    """Make an OpenSecrets API call with rate limiting."""
    global CALLS_MADE
    params.update({
        "method": method,
        "output": "json",
        "apikey": API_KEY,
    })
    url = BASE_URL + "?" + urllib.parse.urlencode(params)

    try:
        time.sleep(0.5)  # Be polite
        req = urllib.request.Request(url, headers={"User-Agent": "CivicReceipts/1.0"})
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode())
            CALLS_MADE += 1
            return data
    except Exception as e:
        print(f"  ERROR: {method} failed: {e}", file=sys.stderr)
        return None


def extract_crp_id(member_data: dict) -> str | None:
    """Extract CRP ID (e.g. N00007360) from the opensecrets URL in member data."""
    url = member_data.get("links", {}).get("opensecrets", "")
    if "cid=" in url:
        return url.split("cid=")[-1].split("&")[0]
    return None


def fetch_top_industries(crp_id: str, cycle: str) -> list[dict]:
    """Fetch top industries for a candidate via candIndustry."""
    data = api_call("candIndustry", {"cid": crp_id, "cycle": cycle})
    if not data:
        return []

    try:
        industries_raw = data["response"]["industries"]["industry"]
        if isinstance(industries_raw, dict):
            industries_raw = [industries_raw]

        industries = []
        for ind in industries_raw[:8]:  # Top 8 industries
            attrs = ind["@attributes"]
            industries.append({
                "code": attrs.get("industry_code", ""),
                "name": attrs.get("industry_name", "Unknown"),
                "amount": int(float(attrs.get("total", 0))),
                "indivs": int(float(attrs.get("indivs", 0))),
                "pacs": int(float(attrs.get("pacs", 0))),
                "donors": [],  # Will be populated from candContrib
            })
        return industries
    except (KeyError, TypeError) as e:
        print(f"  WARN: Could not parse candIndustry: {e}", file=sys.stderr)
        return []


def fetch_top_contributors(crp_id: str, cycle: str) -> list[dict]:
    """Fetch top organizational contributors via candContrib."""
    data = api_call("candContrib", {"cid": crp_id, "cycle": cycle})
    if not data:
        return []

    try:
        contribs_raw = data["response"]["contributors"]["contributor"]
        if isinstance(contribs_raw, dict):
            contribs_raw = [contribs_raw]

        contribs = []
        for c in contribs_raw:
            attrs = c["@attributes"]
            contribs.append({
                "name": attrs.get("org_name", "Unknown"),
                "total": int(float(attrs.get("total", 0))),
                "pacs": int(float(attrs.get("pacs", 0))),
                "indivs": int(float(attrs.get("indivs", 0))),
            })
        return contribs
    except (KeyError, TypeError) as e:
        print(f"  WARN: Could not parse candContrib: {e}", file=sys.stderr)
        return []


def fetch_summary(crp_id: str, cycle: str) -> dict | None:
    """Fetch candidate funding summary via candSummary."""
    data = api_call("candSummary", {"cid": crp_id, "cycle": cycle})
    if not data:
        return None

    try:
        attrs = data["response"]["summary"]["@attributes"]
        return {
            "total_raised": int(float(attrs.get("total", 0))),
            "spent": int(float(attrs.get("spent", 0))),
            "cash_on_hand": int(float(attrs.get("cash_on_hand", 0))),
            "source": attrs.get("source", ""),
        }
    except (KeyError, TypeError) as e:
        print(f"  WARN: Could not parse candSummary: {e}", file=sys.stderr)
        return None


def assign_contributors_to_industries(industries: list[dict], contributors: list[dict]):
    """
    Best-effort assignment of top contributors to industries.
    OpenSecrets doesn't directly link contributors to industries in the API,
    so we list top contributors as a separate "Top Contributors" section
    within the funding data.
    """
    # We can't perfectly map contributors to industries via the API alone.
    # Instead, we'll add contributors as donors on the first industry entry
    # and also store them separately. The bulk data would let us do this properly.
    for ind in industries:
        ind["donors"] = []  # Clear placeholder

    # Add top contributors as a virtual "top donors" list on each industry
    # For now, just attach them to the funding data at the top level
    return contributors


def update_member(bioguide_id: str, cycle: str) -> bool:
    """Fetch and update funding data for a single member."""
    filepath = MEMBERS_DIR / f"{bioguide_id}.json"
    if not filepath.exists():
        print(f"  SKIP: No file for {bioguide_id}")
        return False

    with open(filepath) as f:
        member = json.load(f)

    crp_id = extract_crp_id(member)
    if not crp_id:
        print(f"  SKIP: No CRP ID for {bioguide_id} ({member.get('name', '?')})")
        return False

    print(f"  Fetching data for {member['name']} (CRP: {crp_id})...")

    # 1. Get funding summary (1 API call)
    summary = fetch_summary(crp_id, cycle)
    total_raised = summary["total_raised"] if summary else 0

    # 2. Get top industries (1 API call)
    industries = fetch_top_industries(crp_id, cycle)

    # 3. Get top contributors (1 API call)
    contributors = fetch_top_contributors(crp_id, cycle)

    # Format industries with donor details
    top_industries = []
    for ind in industries:
        top_industries.append({
            "code": ind["code"],
            "name": ind["name"],
            "amount": ind["amount"],
            "donors": [],  # Will be filled from bulk data later
        })

    # Add top contributors as a virtual "Top Contributors" industry entry
    if contributors:
        top_donors = []
        for c in contributors:
            donor_type = "PAC" if c["pacs"] > c["indivs"] else "Organization"
            top_donors.append({
                "name": c["name"],
                "type": donor_type,
                "amount": c["total"],
            })

        # Attach top donors to each industry that matches by name (best effort)
        # For V1, we'll add all top contributors to the funding section
        # and let the UI display them
        for ind in top_industries:
            # Assign any contributor whose name loosely matches the industry
            ind["donors"] = []

        # Store all top contributors under a special entry
        if top_donors:
            top_industries.append({
                "code": "TOP",
                "name": "Top Overall Contributors",
                "amount": sum(d["amount"] for d in top_donors),
                "donors": top_donors,
            })

    # Update member data
    member["funding"] = {
        "cycle": cycle,
        "total_raised": total_raised,
        "top_industries": top_industries,
    }

    with open(filepath, "w") as f:
        json.dump(member, f, indent=2)

    print(f"  OK: {member['name']} — ${total_raised:,} raised, {len(industries)} industries, {len(contributors)} top contributors")
    return True


def main():
    parser = argparse.ArgumentParser(description="Fetch OpenSecrets funding data")
    parser.add_argument("--members", help="Comma-separated bioguide IDs (e.g. P000197,S001150)")
    parser.add_argument("--cycle", default=CYCLE, help="Election cycle (default: 2024)")
    parser.add_argument("--all", action="store_true", help="Process all members in data/members/")
    args = parser.parse_args()

    if not API_KEY:
        print("ERROR: Set OPENSECRETS_API_KEY environment variable", file=sys.stderr)
        print("Get a free key at: https://www.opensecrets.org/api/admin/index.php?function=signup")
        sys.exit(1)

    if args.all:
        member_ids = [f.stem for f in MEMBERS_DIR.glob("*.json")]
        print(f"Processing all {len(member_ids)} members (~{len(member_ids) * 3} API calls needed)")
        print(f"At 200 calls/day, this will take ~{(len(member_ids) * 3) // 200 + 1} days")
    elif args.members:
        member_ids = args.members.split(",")
    else:
        print("Specify --members or --all")
        sys.exit(1)

    print(f"Cycle: {args.cycle}")
    print(f"Members to process: {len(member_ids)}")
    print(f"Estimated API calls: {len(member_ids) * 3}")
    print()

    success = 0
    for bid in member_ids:
        if update_member(bid.strip(), args.cycle):
            success += 1

    print(f"\nDone. Updated {success}/{len(member_ids)} members. API calls used: {CALLS_MADE}")


if __name__ == "__main__":
    main()
