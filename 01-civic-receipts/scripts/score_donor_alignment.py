#!/usr/bin/env python3
"""
Score donor alignment for members of Congress.

Approach (V2):
- Use the top 50 donors (by amount) across campaign + leadership PAC
- Map specific PACs to their known policy positions using a curated registry
- For each key vote, identify which specific donors have a known stake
- Score alignment as: how often the member voted with each donor's position
- Show specific donor names on each example vote

Usage:
    python3 score_donor_alignment.py --members P000197,S001150,P000145
"""
from __future__ import annotations

import csv
import json
import sys
import argparse
from pathlib import Path

MEMBERS_DIR = Path(__file__).parent.parent / "civic-receipts" / "public" / "data" / "members"
CACHE_DIR = Path(__file__).parent / ".cache"

# === PAC Policy Position Registry ===
# Maps PAC name patterns to their known policy positions on specific issues.
# Each entry: pattern -> { "name": display name, "positions": { issue_keyword: "Yea"|"Nay" } }
#
# "Yea" means this PAC wants a Yea vote on bills advancing this issue.
# "Nay" means this PAC wants a Nay vote (i.e., opposes the policy).
#
# Sources: PAC websites, stated missions, public advocacy positions.

PAC_REGISTRY: list[dict] = [
    # === LABOR ===
    {
        "patterns": ["LETTER CARRIERS", "CARPENTERS", "TEACHERS COPE",
                      "MACHINISTS", "AFSCME", "AFL-CIO", "LABORER",
                      "COMMUNICATIONS WORKERS", "TRANSPORT WORKERS",
                      "FIRE FIGHTERS", "PILOTS ASSOCIATION", "TEAMSTERS",
                      "SEIU", "IBEW", "AUTO WORKERS", "PLUMBERS",
                      "IRONWORKERS", "STEELWORKERS", "ENGINEERS POLITICAL"],
        "name_suffix": "(Labor)",
        "positions": {
            "worker": "Yea", "wage": "Yea", "labor": "Yea",
            "union": "Yea", "paid leave": "Yea", "overtime": "Yea",
            "workplace safety": "Yea", "osha": "Yea",
        },
    },
    # === HEALTHCARE ===
    {
        "patterns": ["DENTAL ASSOCIATION", "HOSPITAL ASSOCIATION",
                      "AMERICAN MEDICAL", "PHARMACEUTICAL", "AFLAC",
                      "DAVITA", "KAISER"],
        "name_suffix": "(Healthcare)",
        "positions": {
            "health": "Yea", "medicare": "Yea", "medicaid": "Yea",
            "prescription drug": "Yea", "insulin": "Yea",
            "affordable care": "Yea",
        },
    },
    # === REPRODUCTIVE RIGHTS ===
    {
        "patterns": ["PLANNED PARENTHOOD", "EMILY", "NARAL",
                      "REPRODUCTIVE FREEDOM"],
        "name_suffix": "(Reproductive Rights)",
        "positions": {
            "abortion": "Yea", "reproductive": "Yea", "roe": "Yea",
            "contraception": "Yea",
        },
    },
    # === GUN CONTROL (pro-regulation) ===
    {
        "patterns": ["EVERYTOWN", "GIFFORDS", "BRADY", "MOMS DEMAND"],
        "name_suffix": "(Gun Safety)",
        "positions": {
            "background check": "Yea", "assault weapon": "Yea",
            "gun": "Yea", "firearm": "Yea",
        },
    },
    # === GUN RIGHTS (anti-regulation) ===
    {
        "patterns": ["NRA", "GUN OWNERS OF AMERICA", "NATIONAL SHOOTING"],
        "name_suffix": "(Gun Rights)",
        "positions": {
            "background check": "Nay", "assault weapon": "Nay",
            "gun": "Nay", "firearm": "Nay", "concealed carry": "Yea",
        },
    },
    # === REAL ESTATE ===
    {
        "patterns": ["REALTORS", "MULTI HOUSING", "HOME DEPOT",
                      "HOMEBUILDERS"],
        "name_suffix": "(Real Estate)",
        "positions": {
            "housing": "Yea", "mortgage": "Yea", "real estate": "Yea",
            "rental": "Yea", "homeowner": "Yea",
        },
    },
    # === TECH ===
    {
        "patterns": ["GOOGLE", "MICROSOFT", "CISCO", "DROPBOX",
                      "ORACLE", "APPLE", "META", "AMAZON"],
        "name_suffix": "(Tech)",
        "positions": {
            "data privacy": "Nay",  # Tech generally opposes strict privacy regulation
            "section 230": "Nay",   # Tech opposes section 230 reform
            "broadband": "Yea", "cybersecurity": "Yea",
        },
    },
    # === DEFENSE ===
    {
        "patterns": ["L3HARRIS", "LOCKHEED", "RAYTHEON", "NORTHROP",
                      "BAE SYSTEMS", "BOEING", "GENERAL DYNAMICS",
                      "BOOZ ALLEN"],
        "name_suffix": "(Defense)",
        "positions": {
            "defense": "Yea", "military": "Yea", "ndaa": "Yea",
            "armed forces": "Yea", "pentagon": "Yea",
        },
    },
    # === FINANCE ===
    {
        "patterns": ["GOLDMAN", "JPMORGAN", "CITIGROUP", "BANK OF AMERICA",
                      "CREDIT UNION", "VISA", "MASTERCARD", "BLACKSTONE",
                      "AMALGAMATED BANK", "FIDELITY"],
        "name_suffix": "(Finance)",
        "positions": {
            "financial": "Yea", "banking": "Yea",
            "consumer financial": "Nay",  # Finance opposes CFPB regulation
            "dodd-frank": "Nay",
        },
    },
    # === ENERGY (fossil) ===
    {
        "patterns": ["PETROLEUM", "OIL", "CHEVRON", "EXXON", "KOCH",
                      "PIPELINE", "NATURAL GAS"],
        "name_suffix": "(Oil & Gas)",
        "positions": {
            "climate": "Nay", "emissions": "Nay", "carbon": "Nay",
            "drilling": "Yea", "pipeline": "Yea",
            "renewable": "Nay", "clean energy": "Nay",
        },
    },
    # === CLEAN ENERGY ===
    {
        "patterns": ["SOLAR", "WIND ENERGY", "CLEAN ENERGY",
                      "LEAGUE OF CONSERVATION", "SIERRA"],
        "name_suffix": "(Clean Energy)",
        "positions": {
            "climate": "Yea", "emissions": "Yea", "carbon": "Yea",
            "renewable": "Yea", "clean energy": "Yea",
            "drilling": "Nay", "pipeline": "Nay",
        },
    },
    # === TELECOM ===
    {
        "patterns": ["COMCAST", "AT&T", "VERIZON", "CHARTER"],
        "name_suffix": "(Telecom)",
        "positions": {
            "broadband": "Yea", "net neutrality": "Nay",
        },
    },
    # === CAMPAIGN REFORM ===
    {
        "patterns": ["END CITIZENS UNITED"],
        "name_suffix": "(Campaign Reform)",
        "positions": {
            "campaign finance": "Yea", "citizens united": "Yea",
            "dark money": "Yea", "disclosure": "Yea",
        },
    },
    # === FOREIGN POLICY ===
    {
        "patterns": ["JSTREETPAC", "J STREET"],
        "name_suffix": "(Pro-Peace Israel)",
        "positions": {
            "israel": "Yea", "two-state": "Yea",
        },
    },
    {
        "patterns": ["AIPAC"],
        "name_suffix": "(Pro-Israel)",
        "positions": {
            "israel": "Yea", "iron dome": "Yea",
        },
    },
    # === AGRICULTURE ===
    {
        "patterns": ["CRYSTAL SUGAR", "FARM BUREAU", "DAIRY",
                      "FOOD SOLUTIONS"],
        "name_suffix": "(Agriculture)",
        "positions": {
            "farm bill": "Yea", "agriculture": "Yea",
            "food": "Yea", "snap": "Yea",
        },
    },
]


def match_pac_to_registry(pac_name: str) -> list[dict]:
    """Find all registry entries matching a PAC name."""
    upper = pac_name.upper()
    matches = []
    for entry in PAC_REGISTRY:
        for pattern in entry["patterns"]:
            if pattern in upper:
                matches.append(entry)
                break
    return matches


def load_rollcalls(chamber: str, congress: int = 119) -> dict:
    """Load rollcall data from cache."""
    prefix = "H" if chamber == "house" else "S"
    cache_path = CACHE_DIR / f"{prefix}{congress}_rollcalls.csv"
    if not cache_path.exists():
        return {}

    rollcalls = {}
    with open(cache_path) as f:
        for row in csv.DictReader(f):
            rn = int(row["rollnumber"])
            rollcalls[rn] = row
    return rollcalls


def is_inverted_vote(desc: str) -> bool:
    """Check if a vote has inverted semantics (disapproval, repeal, etc.)."""
    return any(kw in desc for kw in [
        "disapproval", "disapproving", "repeal", "rescission",
        "terminate", "strike the", "eliminating",
    ])


def score_member(bioguide_id: str) -> bool:
    """Compute donor alignment for a member using top 50 donors."""
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

    # Build vote lookup
    vote_lookup = {}
    for v in votes_data.get("recent_votes", []):
        vote_lookup[v["roll_number"]] = v

    # Collect all PAC donors across campaign + leadership PAC
    all_pacs = []
    if member["funding"].get("campaign"):
        for d in member["funding"]["campaign"].get("top_pac_donors", []):
            if d["amount"] > 0:
                all_pacs.append(d)
    for lp in member["funding"].get("leadership_pacs", []):
        for d in lp.get("top_pac_donors", []):
            if d["amount"] > 0:
                all_pacs.append(d)

    # Deduplicate by name, summing amounts
    pac_totals: dict[str, int] = {}
    for p in all_pacs:
        pac_totals[p["name"]] = pac_totals.get(p["name"], 0) + p["amount"]

    # Sort by amount, take top 50
    top_pacs = sorted(pac_totals.items(), key=lambda x: -x[1])[:50]

    # Match each PAC to registry
    pac_with_positions = []
    for pac_name, amount in top_pacs:
        entries = match_pac_to_registry(pac_name)
        if entries:
            pac_with_positions.append({
                "name": pac_name,
                "amount": amount,
                "positions": entries[0]["positions"],
                "category": entries[0]["name_suffix"],
            })

    if not pac_with_positions:
        print(f"  WARN: No matchable PAC donors for {member['name']}")
        # Still save empty alignment
        member["donor_alignment"] = {
            "overall_pct": 0,
            "total_votes_scored": 0,
            "methodology_url": "/methodology#donor-alignment",
            "examples": [],
        }
        with open(member_path, "w") as f:
            json.dump(member, f, indent=2)
        return True

    # Load rollcalls
    rollcalls = load_rollcalls(chamber, congress)
    if not rollcalls:
        return False

    # For each rollcall, check if any of our PACs have a position
    total_aligned = 0
    total_scored = 0
    examples = []
    seen_descs = set()

    # Skip procedural votes
    skip_prefixes = ["providing for consideration", "on ordering the previous"]

    for rn, rc in sorted(rollcalls.items(), key=lambda x: -x[0]):
        desc = rc.get("vote_desc", "") or ""
        bill = rc.get("bill_number", "") or ""
        full_desc = (desc + " " + bill).lower()
        question = rc.get("vote_question", "").lower()

        # Skip procedural and nominations
        if any(full_desc.startswith(p) for p in skip_prefixes):
            continue
        if "nomination" in question:
            continue
        # Skip confirmation votes by description
        if any(phrase in full_desc for phrase in [
            "to be secretary", "to be deputy", "to be an assistant",
            "to be administrator", "to be director", "to be ambassador",
            "to be commissioner", "to be under secretary",
            "to be a member of", "to be inspector general",
            "to be chief", "to be counsel", "to be general counsel",
        ]):
            continue

        # Check if inverted (disapproval/repeal = semantics flip)
        inverted = is_inverted_vote(full_desc)

        # Find PACs that have a position on this vote
        interested_pacs = []
        for pac in pac_with_positions:
            for keyword, position in pac["positions"].items():
                if keyword in full_desc:
                    # Adjust position for inverted votes
                    effective_position = position
                    if inverted:
                        effective_position = "Nay" if position == "Yea" else "Yea"
                    interested_pacs.append({
                        "name": pac["name"],
                        "amount": pac["amount"],
                        "category": pac["category"],
                        "expected": effective_position,
                        "keyword": keyword,
                    })
                    break  # One match per PAC per vote

        if not interested_pacs:
            continue

        # Check member's vote
        vote = vote_lookup.get(rn)
        if not vote or vote["position"] not in ("Yea", "Nay"):
            continue

        member_position = vote["position"]

        # Use majority position among interested PACs
        yea_pacs = [p for p in interested_pacs if p["expected"] == "Yea"]
        nay_pacs = [p for p in interested_pacs if p["expected"] == "Nay"]

        if len(yea_pacs) >= len(nay_pacs):
            donor_expected = "Yea"
            relevant_donors = yea_pacs
        else:
            donor_expected = "Nay"
            relevant_donors = nay_pacs

        aligned = member_position == donor_expected
        total_aligned += 1 if aligned else 0
        total_scored += 1

        # Build example (avoid duplicates)
        if desc not in seen_descs and len(examples) < 20:
            seen_descs.add(desc)
            # Name top 3 specific donors
            donor_names = [
                f"{p['name']} (${p['amount']:,})"
                for p in sorted(relevant_donors, key=lambda x: -x["amount"])[:3]
            ]

            examples.append({
                "vote_description": desc or bill,
                "industry": relevant_donors[0]["category"],
                "industry_preferred": donor_expected,
                "member_voted": member_position,
                "aligned": aligned,
                "date": vote.get("date", ""),
                "bill_url": "",
                "donors": donor_names,
            })

    # Compute overall alignment
    overall_pct = round((total_aligned / total_scored * 100)) if total_scored > 0 else 0

    # Select proportional examples
    aligned_ex = [e for e in examples if e["aligned"]]
    against_ex = [e for e in examples if not e["aligned"]]

    n_show = min(5, len(examples))
    if n_show > 0 and overall_pct > 0:
        n_aligned = max(1, round(n_show * overall_pct / 100))
        n_against = n_show - n_aligned
    else:
        n_aligned = 0
        n_against = n_show

    balanced = aligned_ex[:n_aligned] + against_ex[:n_against]

    # Update member data
    member["donor_alignment"] = {
        "overall_pct": overall_pct,
        "total_votes_scored": total_scored,
        "methodology_url": "/methodology#donor-alignment",
        "examples": balanced,
    }

    with open(member_path, "w") as f:
        json.dump(member, f, indent=2)

    n_matched = len(pac_with_positions)
    print(f"  OK: {member['name']} — {overall_pct}% aligned ({total_scored} votes, {n_matched}/{len(top_pacs)} PACs matched)")
    return True


def main():
    parser = argparse.ArgumentParser(description="Score donor alignment (V2)")
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
