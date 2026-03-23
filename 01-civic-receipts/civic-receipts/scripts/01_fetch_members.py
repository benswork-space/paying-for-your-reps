#!/usr/bin/env python3
"""
Fetch current member data from unitedstates/congress-legislators GitHub repo.
Outputs: data/raw/legislators-current.yaml and data/raw/members.json
"""

import json
import os
import sys
from datetime import date

import requests
import yaml

RAW_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "raw")
LEGISLATORS_URL = "https://raw.githubusercontent.com/unitedstates/congress-legislators/main/legislators-current.yaml"
PHOTO_BASE = "https://unitedstates.github.io/images/congress/450x550"


def fetch_legislators():
    print("Fetching legislators-current.yaml...")
    resp = requests.get(LEGISLATORS_URL)
    resp.raise_for_status()

    os.makedirs(RAW_DIR, exist_ok=True)
    yaml_path = os.path.join(RAW_DIR, "legislators-current.yaml")
    with open(yaml_path, "w") as f:
        f.write(resp.text)

    return yaml.safe_load(resp.text)


def parse_members(legislators):
    members = []
    today = date.today()

    for leg in legislators:
        bio = leg.get("id", {})
        bioguide_id = bio.get("bioguide", "")
        if not bioguide_id:
            continue

        name = leg.get("name", {})
        full_name = name.get("official_full", f"{name.get('first', '')} {name.get('last', '')}")

        # Get current term
        terms = leg.get("terms", [])
        if not terms:
            continue

        current_term = terms[-1]
        chamber = "senate" if current_term.get("type") == "sen" else "house"
        party_map = {"Democrat": "D", "Republican": "R", "Independent": "I"}
        party = party_map.get(current_term.get("party", ""), current_term.get("party", "?")[0])
        state = current_term.get("state", "")
        district = str(current_term.get("district", "")) if chamber == "house" else None

        # Calculate service start (earliest term)
        first_term_start = terms[0].get("start", "")
        serving_since = int(first_term_start[:4]) if first_term_start else None
        years = (today.year - serving_since) if serving_since else 0

        # OpenSecrets CID (for linking)
        opensecrets_id = bio.get("opensecrets", "")

        members.append({
            "bioguide_id": bioguide_id,
            "name": full_name,
            "party": party,
            "chamber": chamber,
            "state": state,
            "district": district,
            "photo_url": f"{PHOTO_BASE}/{bioguide_id}.jpg",
            "serving_since": serving_since,
            "years_in_office": years,
            "opensecrets_id": opensecrets_id,
            "official_website": current_term.get("url", ""),
        })

    return members


def main():
    legislators = fetch_legislators()
    members = parse_members(legislators)

    out_path = os.path.join(RAW_DIR, "members.json")
    with open(out_path, "w") as f:
        json.dump(members, f, indent=2)

    print(f"Wrote {len(members)} members to {out_path}")

    # Print summary
    house = sum(1 for m in members if m["chamber"] == "house")
    senate = sum(1 for m in members if m["chamber"] == "senate")
    print(f"  House: {house}, Senate: {senate}")


if __name__ == "__main__":
    main()
