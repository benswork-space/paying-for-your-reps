#!/usr/bin/env python3
"""
Fetch roll-call vote data from the unitedstates/congress GitHub repo.

Uses the congress repo's compiled vote data (JSON format).
Focuses on the current Congress (119th) and recent prior Congress (118th).

Outputs: data/raw/votes.json (all votes) and data/raw/member_votes.json (per-member vote index)
"""

import json
import os
import sys
import time

import requests

RAW_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "raw")

# We'll pull vote data from the congress repo's compiled data
# Format: https://www.govinfo.gov/bulkdata/BILLSTATUS/{congress}/...
# But the easiest source is VoteView for structured CSV data

VOTEVIEW_MEMBERS_URL = "https://voteview.com/static/data/out/members/HSall_members.csv"
VOTEVIEW_VOTES_URL = "https://voteview.com/static/data/out/rollcalls/HSall_rollcalls.csv"

# Congress.gov API for recent votes
CONGRESS_API_BASE = "https://api.congress.gov/v3"

# We'll use a simpler approach: fetch recent roll-call votes from Congress.gov
# and the unitedstates/congress GitHub for structured vote data

CONGRESS_VOTE_BASE = "https://raw.githubusercontent.com/unitedstates/congress/main/data"


def fetch_voteview_data():
    """
    Fetch VoteView data for ideological scores and vote data.
    This gives us NOMINATE scores and vote-level data.

    For V1, we'll use a simpler approach: fetch individual vote JSON files
    from the congress repo for specific votes we care about.
    """
    print("Fetching VoteView member data (this may take a moment)...")

    # Fetch only current members from VoteView
    # The full file is large, so we'll use the filtered endpoint
    url = "https://voteview.com/static/data/out/members/S119_members.csv"
    try:
        resp = requests.get(url, timeout=30)
        resp.raise_for_status()
        senate_csv = resp.text
    except Exception as e:
        print(f"  Warning: Could not fetch Senate VoteView data: {e}")
        senate_csv = ""

    url = "https://voteview.com/static/data/out/members/H119_members.csv"
    try:
        resp = requests.get(url, timeout=30)
        resp.raise_for_status()
        house_csv = resp.text
    except Exception as e:
        print(f"  Warning: Could not fetch House VoteView data: {e}")
        house_csv = ""

    os.makedirs(RAW_DIR, exist_ok=True)

    if senate_csv:
        with open(os.path.join(RAW_DIR, "voteview_senate_119.csv"), "w") as f:
            f.write(senate_csv)
    if house_csv:
        with open(os.path.join(RAW_DIR, "voteview_house_119.csv"), "w") as f:
            f.write(house_csv)

    return senate_csv, house_csv


def fetch_congress_votes(congress=119, chamber="senate", session=1, max_votes=500):
    """
    Fetch roll-call votes from the Congress.gov API.
    Returns a list of vote records.
    """
    api_key = os.environ.get("CONGRESS_API_KEY", "")

    if not api_key:
        print("  Note: No CONGRESS_API_KEY set. Using unitedstates/congress repo instead.")
        return fetch_votes_from_repo(congress, chamber)

    print(f"Fetching {chamber} votes for Congress {congress}...")
    votes = []
    offset = 0
    limit = 250

    while offset < max_votes:
        url = f"{CONGRESS_API_BASE}/roll-call-vote/{congress}/{chamber}"
        params = {
            "api_key": api_key,
            "offset": offset,
            "limit": limit,
            "format": "json",
        }

        try:
            resp = requests.get(url, params=params, timeout=30)
            resp.raise_for_status()
            data = resp.json()
        except Exception as e:
            print(f"  Warning: API request failed at offset {offset}: {e}")
            break

        roll_calls = data.get("rollCallVotes", data.get("roll-call-votes", []))
        if not roll_calls:
            break

        votes.extend(roll_calls)
        offset += limit

        if len(roll_calls) < limit:
            break

        time.sleep(0.5)  # Rate limiting

    print(f"  Fetched {len(votes)} {chamber} votes")
    return votes


def fetch_votes_from_repo(congress=119, chamber="senate"):
    """
    Fetch vote data from the unitedstates/congress repo.
    Each vote is a separate JSON file.
    We'll fetch the vote index first, then individual votes.
    """
    chamber_prefix = "s" if chamber == "senate" else "h"

    # Try to get the list of votes from the repo
    # The structure is: data/{congress}/votes/{session}/{chamber}{number}/data.json
    votes = []
    session = 1

    print(f"Fetching {chamber} votes for Congress {congress} from repo...")

    # Probe for votes by number
    vote_num = 1
    consecutive_misses = 0

    while consecutive_misses < 10 and vote_num <= 500:
        url = f"https://raw.githubusercontent.com/unitedstates/congress/main/data/{congress}/votes/2025/{chamber_prefix}{vote_num}/data.json"

        try:
            resp = requests.get(url, timeout=10)
            if resp.status_code == 200:
                vote_data = resp.json()
                votes.append(vote_data)
                consecutive_misses = 0
                if vote_num % 50 == 0:
                    print(f"  ... fetched {vote_num} votes so far")
            else:
                consecutive_misses += 1
        except Exception:
            consecutive_misses += 1

        vote_num += 1
        time.sleep(0.1)  # Be nice to GitHub

    print(f"  Fetched {len(votes)} {chamber} votes from repo")
    return votes


def parse_repo_votes(votes):
    """
    Parse vote data from the unitedstates/congress repo format into
    our internal format.

    Each vote has:
    - vote_id, chamber, congress, session, number
    - category (passage, nomination, etc.)
    - question, result, date
    - votes: {Yea: [...], Nay: [...], Not Voting: [...], Present: [...]}
    - bill (if applicable): {type, number, title}
    """
    parsed = []
    member_votes = {}  # bioguide_id -> [{vote_id, position}]

    for vote in votes:
        vote_id = f"{vote.get('chamber', '?')}{vote.get('congress', '?')}-{vote.get('number', '?')}"

        bill_info = vote.get("bill", {})
        bill_id = ""
        bill_title = ""
        if bill_info:
            bill_id = f"{bill_info.get('type', '')}{bill_info.get('number', '')}"
            bill_title = bill_info.get("title", "")

        amendment = vote.get("amendment", {})

        parsed_vote = {
            "vote_id": vote_id,
            "chamber": vote.get("chamber", ""),
            "congress": vote.get("congress", 0),
            "number": vote.get("number", 0),
            "date": vote.get("date", ""),
            "question": vote.get("question", ""),
            "result": vote.get("result", ""),
            "category": vote.get("category", ""),
            "bill_id": bill_id,
            "bill_title": bill_title,
            "requires": vote.get("requires", ""),
        }
        parsed.append(parsed_vote)

        # Extract individual member votes
        vote_positions = vote.get("votes", {})
        for position, voters in vote_positions.items():
            for voter in voters:
                bio_id = voter.get("id", "")
                if not bio_id:
                    continue

                if bio_id not in member_votes:
                    member_votes[bio_id] = []

                member_votes[bio_id].append({
                    "vote_id": vote_id,
                    "position": position,
                    "date": vote.get("date", ""),
                    "question": vote.get("question", ""),
                    "bill_id": bill_id,
                })

    return parsed, member_votes


def main():
    os.makedirs(RAW_DIR, exist_ok=True)

    # Fetch VoteView data (for ideology scores)
    senate_csv, house_csv = fetch_voteview_data()

    # Fetch actual vote data from congress repo
    senate_votes = fetch_votes_from_repo(119, "senate")
    house_votes = fetch_votes_from_repo(119, "house")

    # Also fetch 118th Congress votes (more complete data)
    senate_votes_118 = fetch_votes_from_repo(118, "senate")
    house_votes_118 = fetch_votes_from_repo(118, "house")

    all_votes = senate_votes + house_votes + senate_votes_118 + house_votes_118
    print(f"\nTotal votes fetched: {len(all_votes)}")

    # Parse into our format
    parsed_votes, member_votes = parse_repo_votes(all_votes)

    # Save
    votes_path = os.path.join(RAW_DIR, "votes.json")
    with open(votes_path, "w") as f:
        json.dump(parsed_votes, f, indent=2)
    print(f"Wrote {len(parsed_votes)} parsed votes to {votes_path}")

    member_votes_path = os.path.join(RAW_DIR, "member_votes.json")
    with open(member_votes_path, "w") as f:
        json.dump(member_votes, f)
    print(f"Wrote vote records for {len(member_votes)} members to {member_votes_path}")

    # Verification
    for test_id in ["P000197", "S001150", "P000145"]:  # Pelosi, Schiff, Padilla
        count = len(member_votes.get(test_id, []))
        print(f"  {test_id}: {count} votes on record")


if __name__ == "__main__":
    main()
