#!/usr/bin/env python3
"""
Score donor alignment: how often does each member vote in line
with their top donor industries' interests?

Uses industry_vote_map.json to map industries to specific votes
and expected positions.

Outputs: data/raw/donor_alignment.json
"""

import json
import os
import sys

RAW_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "raw")
DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")


def load_json(path, label):
    if not os.path.exists(path):
        print(f"WARNING: {label} not found at {path}")
        return {}
    with open(path) as f:
        return json.load(f)


def score_member(member_id, member_finance, member_votes_list, industry_map):
    """
    Score a single member's donor alignment.

    For each of their top donor industries, check how they voted on
    mapped votes. Calculate alignment percentage.

    Returns:
    {
        "overall_pct": 68,
        "total_votes_scored": 12,
        "examples": [...],
        "per_industry": {industry_code: {"aligned": N, "total": N, "pct": N}}
    }
    """
    # Build vote lookup for this member
    vote_lookup = {}
    for v in member_votes_list:
        vote_lookup[v["vote_id"]] = v["position"]

    top_industries = member_finance.get("top_industries", [])
    if not top_industries:
        return {
            "overall_pct": 0,
            "total_votes_scored": 0,
            "methodology_url": "/methodology#donor-alignment",
            "examples": [],
        }

    total_aligned = 0
    total_scored = 0
    total_weighted_aligned = 0
    total_weight = 0
    all_examples = []
    per_industry = {}

    for industry in top_industries:
        code = industry.get("code", "")
        name = industry.get("name", "")
        amount = industry.get("amount", 0)

        industry_votes = industry_map.get(code, {}).get("votes", [])
        if not industry_votes:
            continue

        ind_aligned = 0
        ind_total = 0

        for iv in industry_votes:
            vote_id = iv.get("vote_id", "")
            preferred = iv.get("preferred_position", "")
            description = iv.get("description", "")
            bill_url = iv.get("bill_url", "")
            date = iv.get("date", "")

            member_pos = vote_lookup.get(vote_id)
            if not member_pos or member_pos == "Not Voting":
                continue

            aligned = member_pos == preferred
            ind_total += 1
            ind_aligned += 1 if aligned else 0

            # Track as a notable example
            all_examples.append({
                "vote_description": description,
                "industry": name,
                "industry_preferred": f"{preferred} on {description}",
                "member_voted": member_pos,
                "aligned": aligned,
                "date": date,
                "bill_url": bill_url,
                "weight": iv.get("weight", 1.0),
                "industry_amount": amount,
            })

        if ind_total > 0:
            per_industry[code] = {
                "name": name,
                "aligned": ind_aligned,
                "total": ind_total,
                "pct": round(ind_aligned / ind_total * 100),
            }

            # Weight by donation amount for overall score
            weight = amount
            total_weighted_aligned += (ind_aligned / ind_total) * weight
            total_weight += weight
            total_aligned += ind_aligned
            total_scored += ind_total

    # Calculate overall alignment
    if total_weight > 0:
        overall_pct = round(total_weighted_aligned / total_weight * 100)
    elif total_scored > 0:
        overall_pct = round(total_aligned / total_scored * 100)
    else:
        overall_pct = 0

    # Select best examples (most notable aligned + against)
    aligned_examples = [e for e in all_examples if e["aligned"]]
    against_examples = [e for e in all_examples if not e["aligned"]]

    # Sort by industry amount (higher stakes = more notable)
    aligned_examples.sort(key=lambda e: e["industry_amount"], reverse=True)
    against_examples.sort(key=lambda e: e["industry_amount"], reverse=True)

    selected_examples = []
    for ex in aligned_examples[:2]:
        selected_examples.append({
            "vote_description": ex["vote_description"],
            "industry": ex["industry"],
            "industry_preferred": ex["industry_preferred"],
            "member_voted": ex["member_voted"],
            "aligned": True,
            "date": ex["date"],
            "bill_url": ex["bill_url"],
        })
    for ex in against_examples[:1]:
        selected_examples.append({
            "vote_description": ex["vote_description"],
            "industry": ex["industry"],
            "industry_preferred": ex["industry_preferred"],
            "member_voted": ex["member_voted"],
            "aligned": False,
            "date": ex["date"],
            "bill_url": ex["bill_url"],
        })

    return {
        "overall_pct": overall_pct,
        "total_votes_scored": total_scored,
        "methodology_url": "/methodology#donor-alignment",
        "examples": selected_examples,
    }


def main():
    # Load data
    members = load_json(os.path.join(RAW_DIR, "members.json"), "members")
    finance = load_json(os.path.join(RAW_DIR, "finance.json"), "finance")
    member_votes = load_json(os.path.join(RAW_DIR, "member_votes.json"), "member_votes")

    # Load industry vote map
    vote_map_path = os.path.join(DATA_DIR, "industry_vote_map.json")
    industry_map = load_json(vote_map_path, "industry_vote_map")

    if not industry_map:
        print("WARNING: No industry_vote_map.json found. Creating empty donor alignment data.")
        print("  Create data/industry_vote_map.json to enable scoring.")

    # Score each member
    results = {}
    scored_count = 0

    for member in members:
        bio_id = member["bioguide_id"]
        member_finance = finance.get(bio_id, {})
        member_votes_list = member_votes.get(bio_id, [])

        alignment = score_member(bio_id, member_finance, member_votes_list, industry_map)
        results[bio_id] = alignment

        if alignment["total_votes_scored"] > 0:
            scored_count += 1

    # Save
    os.makedirs(RAW_DIR, exist_ok=True)
    out_path = os.path.join(RAW_DIR, "donor_alignment.json")
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2)

    print(f"Wrote donor alignment for {len(results)} members ({scored_count} with scored votes)")

    # Verify
    for test_id in ["P000197", "S001150", "P000145"]:
        a = results.get(test_id, {})
        print(f"  {test_id}: {a.get('overall_pct', 0)}% aligned, {a.get('total_votes_scored', 0)} votes scored")


if __name__ == "__main__":
    main()
