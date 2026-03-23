#!/usr/bin/env python3
"""
Fetch voting records from Voteview (UCLA/MIT) and update member JSON files.

Data source: https://voteview.com/data
No API key needed — public CSV downloads.

Usage:
    python3 fetch_votes.py --members P000197,S001150,P000145
    python3 fetch_votes.py --all
"""
from __future__ import annotations

import csv
import io
import json
import os
import sys
import argparse
import urllib.request
from pathlib import Path

MEMBERS_DIR = Path(__file__).parent.parent / "civic-receipts" / "public" / "data" / "members"
CACHE_DIR = Path(__file__).parent / ".cache"
CONGRESS = 119


def download_csv(url, cache_name):
    """Download a CSV file, caching locally."""
    CACHE_DIR.mkdir(exist_ok=True)
    cache_path = CACHE_DIR / cache_name

    if cache_path.exists():
        print(f"  Using cached {cache_name}")
        with open(cache_path) as f:
            return f.read()

    print(f"  Downloading {cache_name}...")
    req = urllib.request.Request(url, headers={"User-Agent": "CivicReceipts/1.0"})
    resp = urllib.request.urlopen(req, timeout=60)
    text = resp.read().decode()

    with open(cache_path, "w") as f:
        f.write(text)

    return text


def load_rollcalls(chamber):
    """Load rollcall descriptions (what each vote was about)."""
    prefix = "H" if chamber == "house" else "S"
    url = f"https://voteview.com/static/data/out/rollcalls/{prefix}{CONGRESS}_rollcalls.csv"
    text = download_csv(url, f"{prefix}{CONGRESS}_rollcalls.csv")

    rollcalls = {}
    for row in csv.DictReader(io.StringIO(text)):
        rn = int(row["rollnumber"])
        rollcalls[rn] = {
            "date": row.get("date", ""),
            "bill_number": row.get("bill_number", ""),
            "vote_question": row.get("vote_question", ""),
            "vote_desc": row.get("vote_desc", ""),
            "vote_result": row.get("vote_result", ""),
            "yea_count": int(row.get("yea_count", 0)),
            "nay_count": int(row.get("nay_count", 0)),
            "dtl_desc": row.get("dtl_desc", ""),
        }
    return rollcalls


def load_member_votes(chamber):
    """Load all individual votes for this chamber/congress."""
    prefix = "H" if chamber == "house" else "S"
    url = f"https://voteview.com/static/data/out/votes/{prefix}{CONGRESS}_votes.csv"
    text = download_csv(url, f"{prefix}{CONGRESS}_votes.csv")

    # Build dict: icpsr -> list of (rollnumber, cast_code)
    member_votes = {}
    for row in csv.DictReader(io.StringIO(text)):
        icpsr = int(row["icpsr"])
        rn = int(row["rollnumber"])
        cast = int(row["cast_code"])
        if icpsr not in member_votes:
            member_votes[icpsr] = []
        member_votes[icpsr].append((rn, cast))

    return member_votes


def load_members_lookup(chamber):
    """Load ICPSR-to-bioguide mapping."""
    prefix = "H" if chamber == "house" else "S"
    url = f"https://voteview.com/static/data/out/members/{prefix}{CONGRESS}_members.csv"
    text = download_csv(url, f"{prefix}{CONGRESS}_members.csv")

    lookup = {}  # bioguide_id -> icpsr
    for row in csv.DictReader(io.StringIO(text)):
        bid = row.get("bioguide_id", "").strip()
        icpsr = row.get("icpsr", "").strip()
        if bid and icpsr:
            lookup[bid] = {
                "icpsr": int(icpsr),
                "nominate_dim1": float(row.get("nominate_dim1", 0) or 0),
                "nominate_dim2": float(row.get("nominate_dim2", 0) or 0),
                "party_code": int(row.get("party_code", 0) or 0),
            }
    return lookup


def cast_code_to_position(cast_code):
    """Convert Voteview cast_code to human-readable position."""
    # 1=Yea, 2=Paired Yea, 3=Announced Yea
    # 4=Announced Nay, 5=Paired Nay, 6=Nay
    # 7=Present (not voting), 8=Absent, 9=Not a member
    if cast_code in (1, 2, 3):
        return "Yea"
    elif cast_code in (4, 5, 6):
        return "Nay"
    elif cast_code == 7:
        return "Present"
    elif cast_code == 8:
        return "Absent"
    return "N/A"


def update_member(bioguide_id, rollcalls, member_votes_map, members_lookup):
    """Build vote data for a member and save as sidecar file."""
    filepath = MEMBERS_DIR / f"{bioguide_id}.json"
    if not filepath.exists():
        print(f"  SKIP: No file for {bioguide_id}")
        return False

    with open(filepath) as f:
        member = json.load(f)

    chamber = member.get("chamber", "house")
    lookup = members_lookup.get(chamber, {})

    info = lookup.get(bioguide_id)
    if not info:
        print(f"  WARN: {member['name']} not found in Voteview {chamber} data")
        return False

    icpsr = info["icpsr"]
    all_votes_map = member_votes_map.get(chamber, {})
    votes_raw = all_votes_map.get(icpsr, [])

    if not votes_raw:
        print(f"  WARN: No votes found for {member['name']} (ICPSR {icpsr})")
        return False

    chamber_rollcalls = rollcalls.get(chamber, {})

    # Build structured vote records
    recent_votes = []
    total_yea = 0
    total_nay = 0
    total_absent = 0

    for rn, cast in sorted(votes_raw, key=lambda x: -x[0]):  # Most recent first
        rc = chamber_rollcalls.get(rn, {})
        position = cast_code_to_position(cast)

        if position == "Yea":
            total_yea += 1
        elif position == "Nay":
            total_nay += 1
        elif position in ("Absent", "Present"):
            total_absent += 1

        # Only keep the most notable votes for the sidecar (with descriptions)
        if len(recent_votes) < 100 and rc.get("vote_desc") or rc.get("bill_number"):
            recent_votes.append({
                "roll_number": rn,
                "date": rc.get("date", ""),
                "bill": rc.get("bill_number", ""),
                "description": rc.get("vote_desc", "") or rc.get("dtl_desc", ""),
                "question": rc.get("vote_question", ""),
                "position": position,
                "result": rc.get("vote_result", ""),
            })

    # Save vote sidecar
    votes_file = MEMBERS_DIR / f"{bioguide_id}_votes.json"
    with open(votes_file, "w") as f:
        json.dump({
            "bioguide_id": bioguide_id,
            "name": member["name"],
            "congress": CONGRESS,
            "chamber": chamber,
            "ideology": {
                "nominate_dim1": info["nominate_dim1"],
                "nominate_dim2": info["nominate_dim2"],
                "description": "DW-NOMINATE scores: dim1 = liberal (-1) to conservative (+1), dim2 = social issues"
            },
            "vote_stats": {
                "total_votes": total_yea + total_nay,
                "yea": total_yea,
                "nay": total_nay,
                "absent_or_present": total_absent,
            },
            "recent_votes": recent_votes,
        }, f, indent=2)

    print(f"  OK: {member['name']} — {total_yea + total_nay} votes, ideology={info['nominate_dim1']:.3f}")
    return True


def main():
    parser = argparse.ArgumentParser(description="Fetch voting records from Voteview")
    parser.add_argument("--members", help="Comma-separated bioguide IDs")
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--congress", type=int, default=CONGRESS)
    args = parser.parse_args()

    if args.all:
        member_ids = [f.stem for f in MEMBERS_DIR.glob("*.json") if "_" not in f.stem]
    elif args.members:
        member_ids = args.members.split(",")
    else:
        print("Specify --members or --all")
        sys.exit(1)

    # Determine which chambers we need
    chambers_needed = set()
    for bid in member_ids:
        fp = MEMBERS_DIR / f"{bid}.json"
        if fp.exists():
            with open(fp) as f:
                chambers_needed.add(json.load(f).get("chamber", "house"))

    print(f"Congress: {CONGRESS}")
    print(f"Chambers: {chambers_needed}")
    print(f"Processing {len(member_ids)} members...\n")

    # Load data for needed chambers
    rollcalls = {}
    member_votes_map = {}
    members_lookup = {}

    for chamber in chambers_needed:
        print(f"Loading {chamber} data...")
        rollcalls[chamber] = load_rollcalls(chamber)
        member_votes_map[chamber] = load_member_votes(chamber)
        members_lookup[chamber] = load_members_lookup(chamber)
        print(f"  {len(rollcalls[chamber])} rollcalls, {len(member_votes_map[chamber])} members\n")

    success = 0
    for bid in member_ids:
        if update_member(bid.strip(), rollcalls, member_votes_map, members_lookup):
            success += 1

    print(f"\nDone. Updated {success}/{len(member_ids)} members.")


if __name__ == "__main__":
    main()
