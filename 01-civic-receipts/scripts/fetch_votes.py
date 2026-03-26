#!/usr/bin/env python3
"""
Fetch voting records from Voteview (UCLA/MIT) and update member JSON files.

Supports multiple congresses for historical depth.

Data source: https://voteview.com/data
No API key needed — public CSV downloads.

Usage:
    python3 fetch_votes.py --members P000197,S001150,P000145
    python3 fetch_votes.py --all
    python3 fetch_votes.py --all --congresses 114,115,116,117,118,119
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

# Default: 114th-119th Congress (2015-2026, ~10 years)
DEFAULT_CONGRESSES = [114, 115, 116, 117, 118, 119]


def download_csv(url, cache_name):
    """Download a CSV file, caching locally."""
    CACHE_DIR.mkdir(exist_ok=True)
    cache_path = CACHE_DIR / cache_name

    if cache_path.exists():
        return open(cache_path).read()

    print(f"    Downloading {cache_name}...")
    req = urllib.request.Request(url, headers={"User-Agent": "CivicReceipts/1.0"})
    try:
        resp = urllib.request.urlopen(req, timeout=60)
        text = resp.read().decode()
    except Exception as e:
        print(f"    WARN: Failed to download {cache_name}: {e}")
        return ""

    with open(cache_path, "w") as f:
        f.write(text)

    return text


def load_rollcalls(chamber, congress):
    """Load rollcall descriptions for a specific congress."""
    prefix = "H" if chamber == "house" else "S"
    url = f"https://voteview.com/static/data/out/rollcalls/{prefix}{congress}_rollcalls.csv"
    text = download_csv(url, f"{prefix}{congress}_rollcalls.csv")
    if not text:
        return {}

    rollcalls = {}
    for row in csv.DictReader(io.StringIO(text)):
        try:
            rn = int(float(row["rollnumber"]))
        except (ValueError, TypeError):
            continue
        rollcalls[rn] = {
            "congress": congress,
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


def load_member_votes(chamber, congress):
    """Load all individual votes for this chamber/congress."""
    prefix = "H" if chamber == "house" else "S"
    url = f"https://voteview.com/static/data/out/votes/{prefix}{congress}_votes.csv"
    text = download_csv(url, f"{prefix}{congress}_votes.csv")
    if not text:
        return {}

    member_votes = {}
    for row in csv.DictReader(io.StringIO(text)):
        try:
            icpsr = int(float(row["icpsr"]))
            rn = int(float(row["rollnumber"]))
            cast = int(float(row["cast_code"]))
        except (ValueError, TypeError):
            continue
        if icpsr not in member_votes:
            member_votes[icpsr] = []
        member_votes[icpsr].append((rn, cast))

    return member_votes


def load_members_lookup(chamber, congress):
    """Load ICPSR-to-bioguide mapping for a specific congress."""
    prefix = "H" if chamber == "house" else "S"
    url = f"https://voteview.com/static/data/out/members/{prefix}{congress}_members.csv"
    text = download_csv(url, f"{prefix}{congress}_members.csv")
    if not text:
        return {}

    lookup = {}
    for row in csv.DictReader(io.StringIO(text)):
        bid = row.get("bioguide_id", "").strip()
        icpsr = row.get("icpsr", "").strip()
        if bid and icpsr:
            try:
                icpsr_int = int(float(icpsr))
            except (ValueError, TypeError):
                continue
            lookup[bid] = {
                "icpsr": icpsr_int,
                "nominate_dim1": float(row.get("nominate_dim1", 0) or 0),
                "nominate_dim2": float(row.get("nominate_dim2", 0) or 0),
                "party_code": int(row.get("party_code", 0) or 0),
            }
    return lookup


def cast_code_to_position(cast_code):
    """Convert Voteview cast_code to human-readable position."""
    if cast_code in (1, 2, 3):
        return "Yea"
    elif cast_code in (4, 5, 6):
        return "Nay"
    elif cast_code == 7:
        return "Present"
    elif cast_code == 8:
        return "Absent"
    return "N/A"


def update_member(bioguide_id, all_data, congresses):
    """
    Build vote data for a member across multiple congresses.

    all_data = {
        congress: {
            chamber: {
                "rollcalls": {...},
                "member_votes": {...},
                "members_lookup": {...},
            }
        }
    }
    """
    filepath = MEMBERS_DIR / f"{bioguide_id}.json"
    if not filepath.exists():
        return False

    with open(filepath) as f:
        member = json.load(f)

    current_chamber = member.get("chamber", "house")

    # Collect votes across all congresses
    # A member might have been in the House then moved to Senate
    all_votes = []
    total_yea = 0
    total_nay = 0
    total_absent = 0
    latest_ideology = None
    congresses_served = []

    for congress in sorted(congresses, reverse=True):  # Most recent first
        # Check both chambers (member may have switched)
        for chamber in [current_chamber, "senate" if current_chamber == "house" else "house"]:
            cdata = all_data.get(congress, {}).get(chamber)
            if not cdata:
                continue

            lookup = cdata["members_lookup"]
            info = lookup.get(bioguide_id)
            if not info:
                continue

            icpsr = info["icpsr"]
            votes_raw = cdata["member_votes"].get(icpsr, [])
            if not votes_raw:
                continue

            rollcalls = cdata["rollcalls"]
            if congress not in congresses_served:
                congresses_served.append(congress)

            # Use ideology from most recent congress
            if latest_ideology is None:
                latest_ideology = {
                    "nominate_dim1": info["nominate_dim1"],
                    "nominate_dim2": info["nominate_dim2"],
                }

            for rn, cast in sorted(votes_raw, key=lambda x: -x[0]):
                rc = rollcalls.get(rn, {})
                position = cast_code_to_position(cast)

                if position == "Yea":
                    total_yea += 1
                elif position == "Nay":
                    total_nay += 1
                elif position in ("Absent", "Present"):
                    total_absent += 1

                # Keep votes with descriptions (up to 2000 for historical depth)
                if len(all_votes) < 2000 and (rc.get("vote_desc") or rc.get("bill_number")):
                    all_votes.append({
                        "congress": congress,
                        "roll_number": rn,
                        "date": rc.get("date", ""),
                        "bill": rc.get("bill_number", ""),
                        "description": rc.get("vote_desc", "") or rc.get("dtl_desc", ""),
                        "question": rc.get("vote_question", ""),
                        "position": position,
                        "result": rc.get("vote_result", ""),
                    })

            break  # Found member in this chamber for this congress, don't check the other

    if not all_votes:
        return False

    # Sort all votes by date (most recent first)
    all_votes.sort(key=lambda v: v.get("date", ""), reverse=True)

    if latest_ideology is None:
        latest_ideology = {"nominate_dim1": 0, "nominate_dim2": 0}

    # Save vote sidecar
    votes_file = MEMBERS_DIR / f"{bioguide_id}_votes.json"
    with open(votes_file, "w") as f:
        json.dump({
            "bioguide_id": bioguide_id,
            "name": member["name"],
            "congresses": congresses_served,
            "chamber": current_chamber,
            "ideology": {
                "nominate_dim1": latest_ideology["nominate_dim1"],
                "nominate_dim2": latest_ideology["nominate_dim2"],
                "description": "DW-NOMINATE scores: dim1 = liberal (-1) to conservative (+1), dim2 = social issues"
            },
            "vote_stats": {
                "total_votes": total_yea + total_nay,
                "yea": total_yea,
                "nay": total_nay,
                "absent_or_present": total_absent,
                "congresses_covered": len(congresses_served),
            },
            "recent_votes": all_votes,
        }, f, indent=2)

    years = f"{min(congresses_served)}-{max(congresses_served)}" if len(congresses_served) > 1 else str(congresses_served[0])
    print(f"  OK: {member['name']} — {total_yea + total_nay} votes across {len(congresses_served)} congresses ({years})")
    return True


def main():
    parser = argparse.ArgumentParser(description="Fetch voting records from Voteview")
    parser.add_argument("--members", help="Comma-separated bioguide IDs")
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--congresses", help="Comma-separated congress numbers",
                        default=",".join(str(c) for c in DEFAULT_CONGRESSES))
    args = parser.parse_args()

    congresses = [int(c) for c in args.congresses.split(",")]

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
    # Always load both chambers since members may have switched
    chambers_needed = {"house", "senate"}

    print(f"Congresses: {congresses}")
    print(f"Chambers: {chambers_needed}")
    print(f"Processing {len(member_ids)} members...\n")

    # Load data for all congresses and chambers
    all_data = {}
    for congress in congresses:
        all_data[congress] = {}
        print(f"Loading Congress {congress}...")
        for chamber in chambers_needed:
            rollcalls = load_rollcalls(chamber, congress)
            member_votes = load_member_votes(chamber, congress)
            members_lookup = load_members_lookup(chamber, congress)
            all_data[congress][chamber] = {
                "rollcalls": rollcalls,
                "member_votes": member_votes,
                "members_lookup": members_lookup,
            }
            print(f"  {chamber}: {len(rollcalls)} rollcalls, {len(member_votes)} members")
        print()

    # Update each member
    success = 0
    for bid in member_ids:
        if update_member(bid.strip(), all_data, congresses):
            success += 1

    print(f"\nDone. Updated {success}/{len(member_ids)} members.")


if __name__ == "__main__":
    main()
