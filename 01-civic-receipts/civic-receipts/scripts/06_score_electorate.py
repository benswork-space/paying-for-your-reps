#!/usr/bin/env python3
"""
Score electorate alignment using Yale Climate Opinion Maps (YCOM).

Downloads district-level climate opinion data and cross-references
with member voting records on climate/energy legislation.

Outputs: data/raw/electorate_alignment.json
"""

import csv
import io
import json
import os
import sys

import requests

RAW_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "raw")
DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")

# Yale YCOM data - district-level estimates
# The downloadable data is at this URL (CSV format)
YCOM_URL = "https://climatecommunication.yale.edu/visualizations-data/ycom-us/download/"

# Key YCOM questions we can match to votes:
# - regulate: "Do you think the government should regulate CO2 as a pollutant?"
# - fundrenewables: "Do you support funding research into renewable energy?"
# - drilloffshore: "Do you support offshore drilling?" (reversed)
# - drillANWR: "Do you support drilling in the Arctic?" (reversed)
# - carbonlimits: "Do you support setting strict limits on CO2 emissions from power plants?"
# - standards: "Do you support requiring utilities to produce 20% renewable energy?"
# - cleanair: "Do you support the Clean Air Act?"

# Climate/energy votes to match against YCOM opinions
# These are loaded from the industry_vote_map.json and filtered to climate issues
CLIMATE_VOTE_IDS = []  # Will be populated from vote data


def fetch_ycom_data():
    """
    Fetch Yale Climate Opinion Maps data.
    The data is available as a CSV download.
    We need the congressional district level data.
    """
    print("Attempting to fetch YCOM data...")

    # The YCOM data requires navigating a download form.
    # As a fallback, we'll use pre-downloaded data or the API.
    # Try the direct CSV endpoint first
    urls_to_try = [
        "https://climatecommunication.yale.edu/wp-content/uploads/2023/09/YCOM_2023_Data.csv",
        "https://raw.githubusercontent.com/YaleCCOMlab/ycom-data/main/YCOM_2023_congressional_districts.csv",
    ]

    for url in urls_to_try:
        try:
            resp = requests.get(url, timeout=30, allow_redirects=True)
            if resp.status_code == 200 and len(resp.text) > 1000:
                os.makedirs(RAW_DIR, exist_ok=True)
                path = os.path.join(RAW_DIR, "ycom_data.csv")
                with open(path, "w") as f:
                    f.write(resp.text)
                print(f"  Downloaded YCOM data ({len(resp.text)} bytes)")
                return resp.text
        except Exception as e:
            print(f"  Failed to fetch from {url}: {e}")
            continue

    print("  Could not auto-download YCOM data.")
    print("  Please download manually from:")
    print("    https://climatecommunication.yale.edu/visualizations-data/ycom-us/")
    print("  Save as: data/raw/ycom_data.csv")
    print("  Generating placeholder data for now...")

    return None


def parse_ycom_data(text):
    """
    Parse YCOM CSV into district-level opinion estimates.
    Returns: {district_code: {question: pct_support, ...}}

    District codes are like "CA-11", "TX-22", etc.
    """
    if not text:
        return {}

    reader = csv.DictReader(io.StringIO(text))
    district_opinions = {}

    for row in reader:
        # YCOM data has a GeoType column indicating level (state, county, district, etc.)
        geo_type = row.get("GeoType", "").strip()
        geo_name = row.get("GeoName", "").strip()

        # We want congressional district data
        if geo_type not in ("Congressional District", "CD"):
            # Try to detect district format from GeoName
            if not any(c.isdigit() for c in geo_name):
                continue

        # Extract district code
        # Format varies: "California's 11th congressional district" or "CA-11"
        district_code = extract_district_code(geo_name, row)
        if not district_code:
            continue

        # Extract opinion percentages for key questions
        opinions = {}
        question_columns = {
            "regulate": "regulate",
            "fundrenewables": "fundrenewables",
            "drilloffshore": "drilloffshore",
            "carbonlimits": "carbonlimits",
            "standards": "standards",
            "cleanair": "cleanair",
            "gwvoteimp": "gwvoteimp",  # Global warming is important to voting
            "reducetax": "reducetax",
        }

        for col, key in question_columns.items():
            val = row.get(col, "")
            if val:
                try:
                    opinions[key] = round(float(val), 1)
                except ValueError:
                    pass

        if opinions:
            district_opinions[district_code] = opinions

    return district_opinions


def extract_district_code(geo_name, row):
    """Extract a district code like 'CA-11' from various YCOM formats."""
    # Check for a GEOID or FIPS column
    geoid = row.get("GEOID", row.get("GeoFIPS", "")).strip()

    if geoid and len(geoid) == 4:
        state_fips = geoid[:2]
        district = geoid[2:]
        state = FIPS_TO_STATE.get(state_fips)
        if state:
            district_num = district.lstrip("0") or "0"
            return f"{state}-{district_num}"

    # Try parsing the name directly
    # Format: "CA-11" or "California's 11th..."
    if "-" in geo_name and len(geo_name.split("-")[0]) == 2:
        parts = geo_name.split("-")
        state = parts[0].strip()
        try:
            district = str(int(parts[1].strip()))
            return f"{state}-{district}"
        except ValueError:
            pass

    return None


# FIPS to state (same as script 02)
FIPS_TO_STATE = {
    "01": "AL", "02": "AK", "04": "AZ", "05": "AR", "06": "CA",
    "08": "CO", "09": "CT", "10": "DE", "11": "DC", "12": "FL",
    "13": "GA", "15": "HI", "16": "ID", "17": "IL", "18": "IN",
    "19": "IA", "20": "KS", "21": "KY", "22": "LA", "23": "ME",
    "24": "MD", "25": "MA", "26": "MI", "27": "MN", "28": "MS",
    "29": "MO", "30": "MT", "31": "NE", "32": "NV", "33": "NH",
    "34": "NJ", "35": "NM", "36": "NY", "37": "NC", "38": "ND",
    "39": "OH", "40": "OK", "41": "OR", "42": "PA", "44": "RI",
    "45": "SC", "46": "SD", "47": "TN", "48": "TX", "49": "UT",
    "50": "VT", "51": "VA", "53": "WA", "54": "WV", "55": "WI",
    "56": "WY",
}


def generate_placeholder_electorate_data(members):
    """
    Generate placeholder electorate alignment data when YCOM data
    isn't available. This uses known climate opinion patterns by state.

    State-level climate opinion data from YCOM summaries (approximate):
    - CA, NY, MA, WA, OR, CT, HI: ~70-75% support climate regulation
    - TX, OK, WV, WY, ND: ~45-55% support
    - National average: ~65-70% support
    """
    # Rough state-level estimates for "regulate CO2"
    state_climate_support = {
        "CA": 75, "NY": 73, "MA": 74, "WA": 72, "OR": 72, "CT": 74,
        "HI": 76, "VT": 74, "MD": 71, "NJ": 70, "IL": 68, "CO": 68,
        "VA": 67, "MN": 67, "NM": 69, "ME": 70, "NH": 67, "RI": 73,
        "DE": 69, "MI": 65, "PA": 65, "WI": 64, "NV": 68, "AZ": 64,
        "GA": 63, "NC": 63, "FL": 65, "OH": 62, "IN": 60, "IA": 61,
        "MO": 59, "TX": 60, "LA": 58, "KS": 59, "NE": 58, "SC": 61,
        "MT": 58, "SD": 56, "ND": 55, "AK": 57, "ID": 55, "UT": 60,
        "AR": 57, "MS": 58, "AL": 58, "TN": 59, "KY": 57, "OK": 54,
        "WV": 52, "WY": 50, "DC": 80,
    }

    result = {}

    for member in members:
        bio_id = member["bioguide_id"]
        state = member["state"]
        district = member.get("district")
        chamber = member["chamber"]

        support = state_climate_support.get(state, 65)

        # For House members, add some district-level variance
        if chamber == "house" and district:
            # This is a rough approximation
            pass

        district_code = f"{state}-{district}" if district else state

        result[bio_id] = {
            "district": district_code,
            "opinions": {
                "regulate": support,
                "fundrenewables": min(support + 8, 95),
                "carbonlimits": max(support - 3, 40),
                "standards": min(support + 5, 92),
                "cleanair": min(support + 10, 95),
            },
            "source": "state-level-estimate",
            "margin_of_error": 7,
        }

    return result


def score_electorate_alignment(electorate_data, member_votes, vote_map):
    """
    Cross-reference district opinions with member votes on climate issues.

    vote_map: the climate-related entries from industry_vote_map.json
    """
    results = {}

    # Build a mapping of YCOM questions to votes
    climate_votes = vote_map.get("climate_votes", [])

    for bio_id, opinion_data in electorate_data.items():
        opinions = opinion_data.get("opinions", {})
        member_vote_list = member_votes.get(bio_id, [])
        member_vote_lookup = {v["vote_id"]: v["position"] for v in member_vote_list}

        highlights = []
        against_count = 0
        scored_count = 0

        for cv in climate_votes:
            ycom_key = cv.get("ycom_question")
            vote_id = cv.get("vote_id")
            pro_position = cv.get("pro_climate_position", "Yea")
            description = cv.get("description", "")

            if ycom_key not in opinions:
                continue
            if vote_id not in member_vote_lookup:
                continue

            district_pct = opinions[ycom_key]
            member_pos = member_vote_lookup[vote_id]

            # Determine if member's vote aligns with district majority
            district_supports = district_pct > 50
            member_supports = member_pos == pro_position

            aligned = district_supports == member_supports
            scored_count += 1

            if not aligned:
                against_count += 1

            highlights.append({
                "issue": description,
                "district_support_pct": district_pct,
                "margin_of_error": opinion_data.get("margin_of_error", 7),
                "member_position": "Supported" if member_supports else "Opposed",
                "aligned_with_electorate": aligned,
                "aligned_with_donors": False,  # Will be filled by script 05
            })

        results[bio_id] = {
            "issues_scored": scored_count,
            "against_electorate_pct": round(against_count / scored_count * 100) if scored_count > 0 else 0,
            "highlights": highlights,
            "against_electorate_with_donors": [],  # Filled by generate script
            "source": opinion_data.get("source", "ycom"),
        }

    return results


def main():
    os.makedirs(RAW_DIR, exist_ok=True)

    # Load members
    members_path = os.path.join(RAW_DIR, "members.json")
    if not os.path.exists(members_path):
        print("ERROR: Run 01_fetch_members.py first")
        sys.exit(1)
    with open(members_path) as f:
        members = json.load(f)

    # Try to fetch YCOM data
    ycom_text = fetch_ycom_data()
    district_opinions = parse_ycom_data(ycom_text) if ycom_text else {}

    if district_opinions:
        print(f"Parsed YCOM data for {len(district_opinions)} districts")
    else:
        print("Using state-level placeholder estimates for district opinion")
        placeholder_data = generate_placeholder_electorate_data(members)
        out_path = os.path.join(RAW_DIR, "electorate_data.json")
        with open(out_path, "w") as f:
            json.dump(placeholder_data, f, indent=2)
        print(f"Wrote placeholder electorate data for {len(placeholder_data)} members")

    # Load member votes if available
    member_votes_path = os.path.join(RAW_DIR, "member_votes.json")
    member_votes = {}
    if os.path.exists(member_votes_path):
        with open(member_votes_path) as f:
            member_votes = json.load(f)

    # Load climate vote mappings if available
    vote_map_path = os.path.join(DATA_DIR, "industry_vote_map.json")
    vote_map = {}
    if os.path.exists(vote_map_path):
        with open(vote_map_path) as f:
            vote_map = json.load(f)

    # Score alignment
    if district_opinions:
        electorate_data = {}
        for member in members:
            bio_id = member["bioguide_id"]
            state = member["state"]
            district = member.get("district")
            district_code = f"{state}-{district}" if district else state

            if district_code in district_opinions:
                electorate_data[bio_id] = {
                    "district": district_code,
                    "opinions": district_opinions[district_code],
                    "source": "ycom",
                    "margin_of_error": 7,
                }
    else:
        electorate_data = placeholder_data

    alignment = score_electorate_alignment(electorate_data, member_votes, vote_map)

    out_path = os.path.join(RAW_DIR, "electorate_alignment.json")
    with open(out_path, "w") as f:
        json.dump(alignment, f, indent=2)

    scored = sum(1 for v in alignment.values() if v["issues_scored"] > 0)
    print(f"Wrote electorate alignment for {len(alignment)} members ({scored} with scored votes)")


if __name__ == "__main__":
    main()
