#!/usr/bin/env python3
"""
Build ZIP-to-congressional-district mapping.

Uses the Census Bureau ZCTA-to-CD relationship file.
Outputs: data/output/zip_districts.json
"""

import json
import os
import sys

import requests

RAW_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "raw")
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "output")

CENSUS_URL = "https://www2.census.gov/geo/docs/maps-data/data/rel2020/cd-sld/tab20_cd11820_zcta520_natl.txt"

# FIPS to state abbreviation
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
    "56": "WY", "60": "AS", "66": "GU", "69": "MP", "72": "PR",
    "78": "VI",
}


def fetch_crosswalk():
    print("Fetching Census ZCTA-to-CD relationship file...")
    resp = requests.get(CENSUS_URL)
    resp.raise_for_status()

    os.makedirs(RAW_DIR, exist_ok=True)
    raw_path = os.path.join(RAW_DIR, "zcta_cd_crosswalk.txt")
    with open(raw_path, "w", encoding="utf-8-sig") as f:
        f.write(resp.text)

    return resp.text


def parse_crosswalk(text):
    """
    Parse the Census CD-to-ZCTA relationship file.
    Format is pipe-delimited:
      OID_CD118_20|GEOID_CD118_20|NAMELSAD_CD118_20|...|GEOID_ZCTA5_20|...|AREALAND_PART|AREAWATER_PART

    GEOID_CD118_20 = 4-digit: SSDD (state FIPS + district)
    GEOID_ZCTA5_20 = 5-digit ZIP code
    AREALAND_PART = land area of the intersection (we use this as a ratio proxy)
    """
    lines = text.strip().split("\n")
    # Remove BOM if present
    if lines[0].startswith("\ufeff"):
        lines[0] = lines[0][1:]

    header = lines[0].split("|")
    # Find column indices
    col_map = {col.strip(): i for i, col in enumerate(header)}

    cd_geoid_idx = col_map.get("GEOID_CD118_20")
    zcta_geoid_idx = col_map.get("GEOID_ZCTA5_20")
    area_part_idx = col_map.get("AREALAND_PART")
    cd_area_idx = col_map.get("AREALAND_CD118_20")

    if cd_geoid_idx is None or zcta_geoid_idx is None:
        print(f"ERROR: Could not find required columns. Header: {header[:10]}")
        sys.exit(1)

    # Collect all entries: zcta -> [(state_fips, district, area_part)]
    zip_entries = {}
    skipped = 0

    for line in lines[1:]:
        if not line.strip():
            continue
        parts = line.split("|")

        cd_geoid = parts[cd_geoid_idx].strip()
        zcta = parts[zcta_geoid_idx].strip()

        # Skip rows with empty ZCTA (CD-level summary rows)
        if not zcta or len(zcta) < 5:
            skipped += 1
            continue

        if len(cd_geoid) < 4:
            skipped += 1
            continue

        state_fips = cd_geoid[:2]
        district = cd_geoid[2:]

        # Use area as proportion proxy
        area = 1.0
        if area_part_idx is not None and len(parts) > area_part_idx:
            try:
                area = float(parts[area_part_idx].strip())
            except ValueError:
                area = 1.0

        if zcta not in zip_entries:
            zip_entries[zcta] = []
        zip_entries[zcta].append((state_fips, district, area))

    print(f"  Parsed {len(zip_entries)} ZCTAs ({skipped} rows skipped)")

    # Convert area to ratio (proportion of ZIP's total area in each district)
    zip_map = {}
    for zcta, entries in zip_entries.items():
        total_area = sum(e[2] for e in entries)
        zip_map[zcta] = []
        for state_fips, district, area in entries:
            ratio = area / total_area if total_area > 0 else 1.0 / len(entries)
            zip_map[zcta].append({
                "state_fips": state_fips,
                "district": district,
                "ratio": round(ratio, 4),
            })

    return zip_map


def build_zip_lookup(zip_map, members):
    """Combine ZIP-to-district mapping with member data."""
    # Build lookups
    member_by_district = {}  # (state, district) -> member summary
    senators_by_state = {}   # state -> [senator summaries]

    for m in members:
        state = m["state"]
        summary = {
            "bioguide_id": m["bioguide_id"],
            "name": m["name"],
            "party": m["party"],
            "chamber": m["chamber"],
            "state": state,
            "photo_url": m["photo_url"],
        }
        if m["chamber"] == "senate":
            senators_by_state.setdefault(state, []).append(summary)
        else:
            district = m.get("district") or "0"
            summary["district"] = str(district)
            member_by_district[(state, str(district))] = summary

    result = {}

    for zcta, districts in zip_map.items():
        entries = []
        all_members = []
        seen_ids = set()

        for d in districts:
            state = FIPS_TO_STATE.get(d["state_fips"])
            if not state:
                continue

            district_num = d["district"].lstrip("0") or "0"
            if district_num in ("00", "98"):
                district_num = "0"

            entry = {
                "state": state,
                "district": district_num,
                "ratio": d["ratio"],
                "member_ids": [],
            }

            # House member
            house_member = member_by_district.get((state, district_num))
            if house_member and house_member["bioguide_id"] not in seen_ids:
                entry["member_ids"].append(house_member["bioguide_id"])
                all_members.append(house_member)
                seen_ids.add(house_member["bioguide_id"])

            # Senators
            for senator in senators_by_state.get(state, []):
                if senator["bioguide_id"] not in seen_ids:
                    entry["member_ids"].append(senator["bioguide_id"])
                    all_members.append(senator)
                    seen_ids.add(senator["bioguide_id"])

            entries.append(entry)

        if entries and all_members:
            result[zcta] = {
                "entries": entries,
                "members": all_members,
            }

    return result


def main():
    text = fetch_crosswalk()
    zip_map = parse_crosswalk(text)
    print(f"Parsed {len(zip_map)} ZIP codes from crosswalk")

    # Load members
    members_path = os.path.join(RAW_DIR, "members.json")
    if not os.path.exists(members_path):
        print("ERROR: Run 01_fetch_members.py first")
        sys.exit(1)

    with open(members_path) as f:
        members = json.load(f)

    # Build lookup
    zip_lookup = build_zip_lookup(zip_map, members)
    print(f"Built lookup for {len(zip_lookup)} ZIP codes with members")

    # Write output
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    out_path = os.path.join(OUTPUT_DIR, "zip_districts.json")
    with open(out_path, "w") as f:
        json.dump(zip_lookup, f, separators=(",", ":"))

    size_mb = os.path.getsize(out_path) / 1024 / 1024
    print(f"Wrote {out_path} ({size_mb:.1f} MB)")

    # Verify 94107
    if "94107" in zip_lookup:
        entry = zip_lookup["94107"]
        print(f"\n94107 verification:")
        for m in entry["members"]:
            label = f"{m['state']}"
            if m.get("district"):
                label += f"-{m['district']}"
            print(f"  {m['name']} ({m['party']}) - {m['chamber']} {label}")
    else:
        print("\nWARNING: 94107 not found!")


if __name__ == "__main__":
    main()
