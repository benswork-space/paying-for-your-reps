#!/usr/bin/env python3
"""
Score donor alignment for members of Congress.

Approach:
- Map PAC donors to policy interest categories
- Identify key votes in those categories from Voteview rollcall data
- Determine the expected PAC preference on each vote (yea/nay)
- Score how often the member voted with their donors' expected preferences

Usage:
    python3 score_alignment.py --members P000197,S001150,P000145
"""
from __future__ import annotations

import csv
import io
import json
import os
import sys
import argparse
from pathlib import Path

MEMBERS_DIR = Path(__file__).parent.parent / "civic-receipts" / "public" / "data" / "members"
CACHE_DIR = Path(__file__).parent / ".cache"

# === PAC-to-Interest Category Mapping ===
# Maps PAC name patterns to interest categories
PAC_CATEGORIES = {
    # Labor
    "LETTER CARRIERS": "Labor",
    "CARPENTERS": "Labor",
    "TEACHERS": "Labor",
    "MACHINISTS": "Labor",
    "ENGINEERS POLITICAL": "Labor",
    "AFSCME": "Labor",
    "AFL-CIO": "Labor",
    "LABORERS": "Labor",
    "LABORER": "Labor",
    "COMMUNICATIONS WORKERS": "Labor",
    "TRANSPORT WORKERS": "Labor",
    "FIRE FIGHTERS": "Labor",
    "PILOTS ASSOCIATION": "Labor",
    "TEAMSTERS": "Labor",
    "SEIU": "Labor",
    "IBEW": "Labor",
    "UNITED AUTO WORKERS": "Labor",
    "PLUMBERS": "Labor",
    "IRONWORKERS": "Labor",
    "STEELWORKERS": "Labor",

    # Real Estate / Housing
    "REALTORS": "Real Estate",
    "HOME DEPOT": "Real Estate",
    "NATIONAL MULTI HOUSING": "Real Estate",

    # Healthcare
    "DENTAL ASSOCIATION": "Healthcare",
    "HOSPITAL ASSOCIATION": "Healthcare",
    "AFLAC": "Healthcare",
    "DAVITA": "Healthcare",
    "PLANNED PARENTHOOD": "Healthcare",
    "AMERICAN MEDICAL": "Healthcare",
    "PHARMACEUTICAL": "Healthcare",
    "PFIZER": "Healthcare",
    "JOHNSON & JOHNSON": "Healthcare",

    # Tech
    "GOOGLE": "Tech",
    "MICROSOFT": "Tech",
    "CISCO": "Tech",
    "DROPBOX": "Tech",
    "ORACLE": "Tech",
    "APPLE": "Tech",
    "META": "Tech",
    "AMAZON": "Tech",

    # Defense
    "L3HARRIS": "Defense",
    "LOCKHEED": "Defense",
    "RAYTHEON": "Defense",
    "NORTHROP": "Defense",
    "BAE SYSTEMS": "Defense",
    "BOEING": "Defense",
    "GENERAL DYNAMICS": "Defense",
    "BOOZ ALLEN": "Defense",

    # Telecom / Media
    "COMCAST": "Telecom/Media",
    "AT&T": "Telecom/Media",
    "VERIZON": "Telecom/Media",
    "DISNEY": "Telecom/Media",

    # Finance
    "GOLDMAN": "Finance",
    "JPMORGAN": "Finance",
    "CITIGROUP": "Finance",
    "BANK OF AMERICA": "Finance",
    "CREDIT UNION": "Finance",
    "VISA": "Finance",
    "MASTERCARD": "Finance",
    "BLACKSTONE": "Finance",
    "AMALGAMATED BANK": "Finance",
    "FIDELITY": "Finance",

    # Energy
    "ENERGY": "Energy",
    "OIL": "Energy",
    "PETROLEUM": "Energy",
    "EDISON": "Energy",
    "SOLAR": "Energy",

    # Agriculture
    "CRYSTAL SUGAR": "Agriculture",
    "FARM BUREAU": "Agriculture",
    "DAIRY": "Agriculture",

    # Gun Rights
    "NRA": "Gun Rights",
    "GUN OWNERS": "Gun Rights",
    "FIREARMS": "Gun Rights",

    # Civil Rights / Reform
    "END CITIZENS UNITED": "Campaign Reform",
    "ACLU": "Civil Rights",
    "JSTREETPAC": "Foreign Policy",
    "AIPAC": "Foreign Policy",

    # Food
    "FOOD SOLUTIONS": "Food/Agriculture",
    "RESTAURANT": "Food/Agriculture",
}


def categorize_pac(pac_name: str) -> str | None:
    """Map a PAC name to an interest category."""
    upper = pac_name.upper()
    for pattern, category in PAC_CATEGORIES.items():
        if pattern in upper:
            return category
    return None


def load_rollcalls(chamber: str, congress: int = 119) -> dict:
    """Load rollcall data from cache."""
    prefix = "H" if chamber == "house" else "S"
    cache_path = CACHE_DIR / f"{prefix}{congress}_rollcalls.csv"
    if not cache_path.exists():
        print(f"  WARN: No rollcall cache at {cache_path}")
        return {}

    rollcalls = {}
    with open(cache_path) as f:
        for row in csv.DictReader(f):
            rn = int(row["rollnumber"])
            rollcalls[rn] = {
                "date": row.get("date", ""),
                "bill_number": row.get("bill_number", ""),
                "vote_desc": row.get("vote_desc", ""),
                "vote_question": row.get("vote_question", ""),
                "vote_result": row.get("vote_result", ""),
            }
    return rollcalls


# === Key votes by interest category ===
# Maps categories to bill keywords and expected positions
# "yea" means the interest group would want a Yea vote
# This is a curated, transparent mapping
CATEGORY_KEY_VOTES = {
    "Labor": {
        "keywords": ["worker", "wage", "labor", "union", "nlrb", "overtime",
                     "paid leave", "family leave", "minimum wage", "pro act",
                     "employee", "workplace safety", "osha"],
        "expected": "Yea",  # Labor PACs generally want pro-labor votes
    },
    "Healthcare": {
        "keywords": ["health", "affordable care", "medicare", "medicaid",
                     "prescription drug", "insulin", "hospital", "medical"],
        "expected": "Yea",  # Healthcare PACs generally want healthcare expansion
    },
    "Defense": {
        "keywords": ["defense", "military", "armed forces", "ndaa",
                     "national defense", "pentagon", "veterans"],
        "expected": "Yea",  # Defense PACs want defense spending
    },
    "Real Estate": {
        "keywords": ["housing", "mortgage", "real estate", "rental",
                     "fair housing", "hud", "homeowner"],
        "expected": "Yea",
    },
    "Energy": {
        "keywords": ["energy", "climate", "emissions", "carbon", "fossil",
                     "renewable", "solar", "wind", "pipeline", "drilling"],
        "expected": "Yea",  # Varies - but energy PACs generally want energy bills
    },
    "Tech": {
        "keywords": ["technology", "data privacy", "artificial intelligence",
                     "cybersecurity", "broadband", "internet", "section 230"],
        "expected": "Yea",
    },
    "Finance": {
        "keywords": ["financial", "banking", "wall street", "dodd-frank",
                     "securities", "credit", "consumer financial"],
        "expected": "Yea",
    },
    "Gun Rights": {
        "keywords": ["firearm", "gun", "second amendment", "assault weapon",
                     "background check", "concealed carry"],
        "expected": "Nay",  # Gun rights PACs oppose gun control
    },
}


def find_relevant_votes(rollcalls: dict, category: str) -> list[dict]:
    """Find votes relevant to a category based on keywords."""
    config = CATEGORY_KEY_VOTES.get(category)
    if not config:
        return []

    keywords = config["keywords"]
    relevant = []

    # Skip nomination/confirmation votes — they don't reflect policy positions
    skip_patterns = ["to be secretary", "to be deputy", "to be administrator",
                     "to be director", "to be ambassador", "to be commissioner",
                     "nomination", "to be under secretary", "to be assistant secretary",
                     "cloture on the nomination", "confirmation"]

    for rn, rc in rollcalls.items():
        desc = (rc.get("vote_desc", "") + " " + rc.get("bill_number", "")).lower()
        question = rc.get("vote_question", "").lower()

        # Skip nominations
        if any(skip in desc for skip in skip_patterns):
            continue
        if "nomination" in question:
            continue

        # Skip procedural "providing for consideration" votes
        if desc.startswith("providing for consideration"):
            continue

        for kw in keywords:
            if kw in desc:
                relevant.append({
                    "roll_number": rn,
                    **rc,
                    "category": category,
                    "expected_position": config["expected"],
                })
                break

    return relevant


def score_member(bioguide_id: str) -> bool:
    """Compute donor alignment scores for a member."""
    member_path = MEMBERS_DIR / f"{bioguide_id}.json"
    votes_path = MEMBERS_DIR / f"{bioguide_id}_votes.json"

    if not member_path.exists() or not votes_path.exists():
        print(f"  SKIP: Missing data for {bioguide_id}")
        return False

    with open(member_path) as f:
        member = json.load(f)
    with open(votes_path) as f:
        votes_data = json.load(f)

    chamber = member.get("chamber", "house")
    congress = votes_data.get("congress", 119)

    # Build vote lookup: roll_number -> position
    vote_lookup = {}
    for v in votes_data.get("recent_votes", []):
        vote_lookup[v["roll_number"]] = v["position"]

    # Categorize PAC donors
    all_pacs = []
    if member["funding"].get("campaign"):
        all_pacs.extend(member["funding"]["campaign"].get("top_pac_donors", []))
    for lp in member["funding"].get("leadership_pacs", []):
        all_pacs.extend(lp.get("top_pac_donors", []))

    category_amounts: dict[str, int] = {}
    for pac in all_pacs:
        cat = categorize_pac(pac["name"])
        if cat and pac["amount"] > 0:
            category_amounts[cat] = category_amounts.get(cat, 0) + pac["amount"]

    if not category_amounts:
        print(f"  WARN: No categorizable PAC donors for {member['name']}")
        return False

    # Load rollcalls
    rollcalls = load_rollcalls(chamber, congress)
    if not rollcalls:
        return False

    # Score each category
    total_aligned = 0
    total_scored = 0
    examples = []

    for category, amount in sorted(category_amounts.items(), key=lambda x: -x[1]):
        relevant_votes = find_relevant_votes(rollcalls, category)

        cat_aligned = 0
        cat_total = 0

        for rv in relevant_votes:
            rn = rv["roll_number"]
            position = vote_lookup.get(rn)
            if not position or position in ("Absent", "Present", "N/A"):
                continue

            expected = rv["expected_position"]
            aligned = position == expected
            cat_aligned += 1 if aligned else 0
            cat_total += 1

            # Keep notable examples, avoiding duplicates
            desc = rv["vote_desc"] or rv["bill_number"] or "Vote"
            seen_descs = {e["vote_description"] for e in examples}
            if len(examples) < 12 and desc not in seen_descs:
                examples.append({
                    "vote_description": desc,
                    "industry": category,
                    "industry_preferred": expected,
                    "member_voted": position,
                    "aligned": aligned,
                    "date": rv["date"],
                    "bill_url": f"https://www.congress.gov/bill/{congress}th-congress/{rv['bill_number'].lower().replace(' ', '-')}" if rv.get("bill_number") else "",
                })

        total_aligned += cat_aligned
        total_scored += cat_total

    # Compute overall alignment
    overall_pct = round((total_aligned / total_scored * 100)) if total_scored > 0 else 0

    # Select a balanced set of examples
    aligned_examples = [e for e in examples if e["aligned"]]
    against_examples = [e for e in examples if not e["aligned"]]

    # Show proportional examples (matching the alignment %)
    n_examples = min(5, len(examples))
    n_aligned = max(1, round(n_examples * overall_pct / 100)) if n_examples > 0 else 0
    n_against = n_examples - n_aligned

    balanced = aligned_examples[:n_aligned] + against_examples[:n_against]

    # Update member data
    member["donor_alignment"] = {
        "overall_pct": overall_pct,
        "total_votes_scored": total_scored,
        "methodology_url": "/methodology#donor-alignment",
        "examples": balanced,
        "categories": [
            {"name": cat, "amount": amt, "votes_scored": 0}
            for cat, amt in sorted(category_amounts.items(), key=lambda x: -x[1])
        ],
    }

    with open(member_path, "w") as f:
        json.dump(member, f, indent=2)

    print(f"  OK: {member['name']} — {overall_pct}% aligned with donors ({total_scored} votes scored, {len(category_amounts)} categories)")
    return True


def main():
    parser = argparse.ArgumentParser(description="Score donor alignment")
    parser.add_argument("--members", help="Comma-separated bioguide IDs")
    parser.add_argument("--all", action="store_true")
    args = parser.parse_args()

    if args.all:
        member_ids = [f.stem for f in MEMBERS_DIR.glob("*.json") if "_" not in f.stem]
    elif args.members:
        member_ids = args.members.split(",")
    else:
        print("Specify --members or --all")
        sys.exit(1)

    print(f"Processing {len(member_ids)} members...\n")

    success = 0
    for bid in member_ids:
        if score_member(bid.strip()):
            success += 1

    print(f"\nDone. Scored {success}/{len(member_ids)} members.")


if __name__ == "__main__":
    main()
