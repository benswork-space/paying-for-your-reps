#!/usr/bin/env python3
"""
Score district alignment for members of Congress.

V1 approach: Compare rep's votes on key issues against estimated district
public opinion from known polling data.

For congressional districts, we use:
- Statewide polling on key issues (scaled by district partisan lean)
- National polling on issues with strong bipartisan consensus

Sources for opinion estimates:
- Pew Research Center national polls
- PPIC (Public Policy Institute of California) for CA districts
- Gallup national polls
- Issue-specific polls from major pollsters

Usage:
    python3 score_district.py --members P000197,S001150,P000145
"""
from __future__ import annotations

import json
import sys
import argparse
from pathlib import Path

MEMBERS_DIR = Path(__file__).parent.parent / "civic-receipts" / "public" / "data" / "members"

# === District opinion estimates on key issues ===
# Format: { state-district: { issue: { support_pct, margin, source } } }
# For Senate races, use state-level data

# California statewide opinion estimates (from PPIC, Pew, etc.)
CA_OPINION = {
    "Gun control: universal background checks": {
        "support_pct": 89, "margin": 3,
        "source": "PPIC 2024",
        "pro_position": "Yea",
        "vote_keywords": ["background check", "gun", "firearm"],
    },
    "Climate: government action on climate change": {
        "support_pct": 78, "margin": 4,
        "source": "PPIC 2024",
        "pro_position": "Yea",
        "vote_keywords": ["climate", "emissions", "carbon", "clean energy", "renewable"],
    },
    "Immigration: path to citizenship for Dreamers": {
        "support_pct": 73, "margin": 4,
        "source": "PPIC 2024",
        "pro_position": "Yea",
        "vote_keywords": ["dreamer", "daca", "dream act", "path to citizenship"],
    },
    "Healthcare: protecting ACA pre-existing conditions": {
        "support_pct": 82, "margin": 3,
        "source": "KFF 2024",
        "pro_position": "Yea",
        "vote_keywords": ["affordable care", "pre-existing", "health coverage", "aca"],
    },
    "Abortion: protecting access to abortion": {
        "support_pct": 75, "margin": 4,
        "source": "PPIC 2024",
        "pro_position": "Yea",
        "vote_keywords": ["abortion", "reproductive", "roe"],
    },
    "Economy: raising minimum wage": {
        "support_pct": 67, "margin": 4,
        "source": "Pew 2024",
        "pro_position": "Yea",
        "vote_keywords": ["minimum wage", "raise the wage"],
    },
    "Democracy: preventing government shutdowns": {
        "support_pct": 85, "margin": 3,
        "source": "Gallup 2024",
        "pro_position": "Yea",
        "vote_keywords": ["government shutdown", "continuing resolution", "appropriations act", "consolidated appropriations"],
    },
    "Infrastructure: investing in infrastructure": {
        "support_pct": 79, "margin": 3,
        "source": "Pew 2024",
        "pro_position": "Yea",
        "vote_keywords": ["infrastructure", "roads", "bridges", "broadband"],
    },
    "Veterans: expanding veteran healthcare": {
        "support_pct": 88, "margin": 3,
        "source": "Gallup 2024",
        "pro_position": "Yea",
        "vote_keywords": ["veteran", "va hospital", "pact act"],
    },
    "Education: student loan relief": {
        "support_pct": 62, "margin": 5,
        "source": "Pew 2024",
        "pro_position": "Yea",
        "vote_keywords": ["student loan", "student debt", "college afford"],
    },
}

# San Francisco (CA-11) is more liberal than CA statewide — bump by ~10 points
CA_11_ADJUSTMENTS = {
    "Gun control: universal background checks": 5,
    "Climate: government action on climate change": 10,
    "Abortion: protecting access to abortion": 12,
    "Immigration: path to citizenship for Dreamers": 10,
    "Economy: raising minimum wage": 10,
    "Education: student loan relief": 10,
}


def get_district_opinion(state: str, district: str | None, chamber: str) -> dict:
    """Get opinion estimates for a district or state."""
    if state != "CA":
        # For non-CA districts, return empty (we only have CA data for now)
        return {}

    opinion = {}
    for issue, data in CA_OPINION.items():
        entry = dict(data)
        # Apply district-level adjustment for House members
        if chamber == "house" and district:
            adjustment = CA_11_ADJUSTMENTS.get(issue, 0) if district == "11" else 0
            entry["support_pct"] = min(99, entry["support_pct"] + adjustment)
        opinion[issue] = entry

    return opinion


def score_member(bioguide_id: str) -> bool:
    """Compute district alignment scores for a member."""
    member_path = MEMBERS_DIR / f"{bioguide_id}.json"
    votes_path = MEMBERS_DIR / f"{bioguide_id}_votes.json"

    if not member_path.exists() or not votes_path.exists():
        print(f"  SKIP: Missing data for {bioguide_id}")
        return False

    with open(member_path) as f:
        member = json.load(f)
    with open(votes_path) as f:
        votes_data = json.load(f)

    state = member.get("state", "")
    district = member.get("district")
    chamber = member.get("chamber", "house")

    opinion = get_district_opinion(state, district, chamber)
    if not opinion:
        print(f"  SKIP: No opinion data for {state}-{district or 'statewide'}")
        return False

    # Build vote lookup
    vote_lookup = {}
    for v in votes_data.get("recent_votes", []):
        vote_lookup[v["roll_number"]] = v

    # Load rollcalls
    import csv
    cache_dir = Path(__file__).parent / ".cache"
    prefix = "H" if chamber == "house" else "S"
    congress = votes_data.get("congress", 119)
    rollcall_path = cache_dir / f"{prefix}{congress}_rollcalls.csv"

    if not rollcall_path.exists():
        print(f"  WARN: No rollcall cache")
        return False

    rollcalls = {}
    with open(rollcall_path) as f:
        for row in csv.DictReader(f):
            rn = int(row["rollnumber"])
            rollcalls[rn] = row

    # Score each issue
    highlights = []
    against_with_donors = []
    issues_scored = 0
    against_count = 0

    # Get donor categories for cross-referencing
    donor_cats = set()
    da = member.get("donor_alignment", {})
    for cat in da.get("categories", []):
        donor_cats.add(cat["name"])

    for issue, odata in opinion.items():
        keywords = odata["vote_keywords"]
        pro_position = odata["pro_position"]

        # Find matching votes
        matched_votes = []
        for rn, rc in rollcalls.items():
            desc = (rc.get("vote_desc", "") + " " + rc.get("bill_number", "")).lower()
            question = rc.get("vote_question", "").lower()

            # Skip procedural
            if desc.startswith("providing for consideration"):
                continue
            if "nomination" in question:
                continue

            for kw in keywords:
                if kw in desc:
                    vote = vote_lookup.get(rn)
                    if vote and vote["position"] in ("Yea", "Nay"):
                        # For CRAs (disapproval resolutions), the semantics flip:
                        # "Yea" on a disapproval = opposing the policy
                        is_disapproval = "disapproval" in desc or "disapproving" in desc
                        is_repeal = "repeal" in desc or "rescission" in desc or "terminate" in desc or "strike" in desc
                        # For amendments that ADD something positive, Yea = pro
                        is_pro_amendment = "to modify" in desc or "to extend" in desc or "to establish" in desc

                        effective_position = vote["position"]
                        if is_disapproval or is_repeal:
                            # Flip: Yea on disapproval = opposing the policy
                            effective_position = "Nay" if vote["position"] == "Yea" else "Yea"

                        matched_votes.append({
                            **vote,
                            "effective_position": effective_position,
                        })
                    break

        if not matched_votes:
            continue

        issues_scored += 1

        # Count how many votes aligned with district opinion
        aligned_count = sum(1 for v in matched_votes if v.get("effective_position", v["position"]) == pro_position)
        total = len(matched_votes)
        aligned = aligned_count > total / 2  # Majority of votes on this issue

        member_position = f"Voted {pro_position}" if aligned else f"Voted against"

        highlight = {
            "issue": issue.split(": ", 1)[-1] if ": " in issue else issue,
            "district_support_pct": odata["support_pct"],
            "margin_of_error": odata["margin"],
            "member_position": member_position,
            "aligned_with_electorate": aligned,
            "aligned_with_donors": False,  # Will check below
        }

        if not aligned:
            against_count += 1
            # Check if this aligns with donor interests
            issue_category = issue.split(":")[0].strip()
            donor_map = {
                "Gun control": "Gun Rights",
                "Climate": "Energy",
                "Healthcare": "Healthcare",
                "Economy": "Labor",
                "Infrastructure": "Real Estate",
            }
            mapped_cat = donor_map.get(issue_category)
            if mapped_cat and mapped_cat in donor_cats:
                highlight["aligned_with_donors"] = True
                against_with_donors.append({
                    "issue": highlight["issue"],
                    "district_support_pct": odata["support_pct"],
                    "member_position": member_position,
                    "top_donor_interest": mapped_cat,
                    "donor_preferred": f"Voted {'Nay' if pro_position == 'Yea' else 'Yea'}",
                })

        highlights.append(highlight)

    against_pct = round(against_count / issues_scored * 100) if issues_scored > 0 else 0

    member["electorate_alignment"] = {
        "issues_scored": issues_scored,
        "against_electorate_pct": against_pct,
        "highlights": highlights,
        "against_electorate_with_donors": against_with_donors,
    }

    with open(member_path, "w") as f:
        json.dump(member, f, indent=2)

    aligned_pct = 100 - against_pct
    print(f"  OK: {member['name']} — {aligned_pct}% aligned with district ({issues_scored} issues scored, {against_count} against)")
    return True


def main():
    parser = argparse.ArgumentParser(description="Score district alignment")
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
