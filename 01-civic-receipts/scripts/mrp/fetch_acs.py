#!/usr/bin/env python3
"""
Fetch ACS 5-year demographic data by congressional district from the Census API.
Creates a poststratification table for MRP with demographic cell populations.

Uses ACS tables:
  B01001 - Sex by Age
  B15003 - Educational Attainment (25+)
  B03002 - Hispanic/Latino Origin by Race

Output: acs_district_demographics.csv
  Columns: cd_clean, female, age_bin, educ_bin, race_bin, population
  One row per demographic cell per congressional district.
"""

import csv
import itertools
import json
import os
import sys
import urllib.request
import urllib.error

API_KEY = os.environ.get("CENSUS_API_KEY", "")
DATA_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_FILE = os.path.join(DATA_DIR, "acs_district_demographics.csv")

# ACS 2022 5-year estimates (covers 2018-2022, closest match to CES 2018-2021)
# Uses 118th Congress district boundaries
ACS_YEAR = 2022
BASE_URL = f"https://api.census.gov/data/{ACS_YEAR}/acs/acs5"

# FIPS state codes (all 50 states + DC)
STATES = [
    "01", "02", "04", "05", "06", "08", "09", "10", "11", "12",
    "13", "15", "16", "17", "18", "19", "20", "21", "22", "23",
    "24", "25", "26", "27", "28", "29", "30", "31", "32", "33",
    "34", "35", "36", "37", "38", "39", "40", "41", "42", "44",
    "45", "46", "47", "48", "49", "50", "51", "53", "54", "55", "56",
]

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

# At-large districts (single CD states)
AT_LARGE_STATES = {"AK", "DE", "MT", "ND", "SD", "VT", "WY", "DC"}


def fetch_api(variables, state_fips):
    """Fetch data from Census API for a single state's congressional districts."""
    var_str = ",".join(variables)
    url = (
        f"{BASE_URL}?get=NAME,{var_str}"
        f"&for=congressional+district:*"
        f"&in=state:{state_fips}"
        f"&key={API_KEY}"
    )
    req = urllib.request.Request(url, headers={"User-Agent": "CivicReceipts/1.0"})
    resp = urllib.request.urlopen(req, timeout=30)
    data = json.loads(resp.read().decode())
    header = data[0]
    rows = data[1:]
    return [dict(zip(header, row)) for row in rows]


def cd_label(state_fips, district_num):
    """Convert FIPS state + district number to 'ST-DD' format."""
    state = FIPS_TO_STATE.get(state_fips, state_fips)
    if state in AT_LARGE_STATES:
        return f"{state}-00"
    return f"{state}-{district_num.zfill(2)}"


def fetch_age_sex():
    """
    Fetch B01001 (Sex by Age) for all congressional districts.
    Returns dict: cd_label -> {(female, age_bin): population}
    """
    # B01001: Sex by Age
    # Male columns (003-025), Female columns (027-049)
    # We need 18+ only, mapped to our age bins
    #
    # Male 18-19: 007, 20: 008, 21: 009, 22-24: 010, 25-29: 011
    # Male 30-34: 012, 35-39: 013, 40-44: 014
    # Male 45-49: 015, 50-54: 016, 55-59: 017, 60-61: 018, 62-64: 019
    # Male 65-66: 020, 67-69: 021, 70-74: 022, 75-79: 023, 80-84: 024, 85+: 025
    #
    # Female: same pattern but offset by 24 (007->031, etc.)

    male_18_29 = ["B01001_007E", "B01001_008E", "B01001_009E", "B01001_010E", "B01001_011E"]
    male_30_44 = ["B01001_012E", "B01001_013E", "B01001_014E"]
    male_45_64 = ["B01001_015E", "B01001_016E", "B01001_017E", "B01001_018E", "B01001_019E"]
    male_65_plus = ["B01001_020E", "B01001_021E", "B01001_022E", "B01001_023E", "B01001_024E", "B01001_025E"]

    female_18_29 = ["B01001_031E", "B01001_032E", "B01001_033E", "B01001_034E", "B01001_035E"]
    female_30_44 = ["B01001_036E", "B01001_037E", "B01001_038E"]
    female_45_64 = ["B01001_039E", "B01001_040E", "B01001_041E", "B01001_042E", "B01001_043E"]
    female_65_plus = ["B01001_044E", "B01001_045E", "B01001_046E", "B01001_047E", "B01001_048E", "B01001_049E"]

    all_vars = (male_18_29 + male_30_44 + male_45_64 + male_65_plus +
                female_18_29 + female_30_44 + female_45_64 + female_65_plus)

    groups = [
        (0, "18-29", male_18_29),
        (0, "30-44", male_30_44),
        (0, "45-64", male_45_64),
        (0, "65+", male_65_plus),
        (1, "18-29", female_18_29),
        (1, "30-44", female_30_44),
        (1, "45-64", female_45_64),
        (1, "65+", female_65_plus),
    ]

    result = {}  # cd -> {(female, age_bin): pop}
    print("  Fetching age × sex data (B01001)...")

    for state_fips in STATES:
        try:
            rows = fetch_api(all_vars, state_fips)
        except Exception as e:
            print(f"    Error fetching {state_fips}: {e}")
            continue

        for row in rows:
            cd = cd_label(row["state"], row["congressional district"])
            if cd not in result:
                result[cd] = {}

            for female, age_bin, var_cols in groups:
                pop = sum(int(row.get(v, 0) or 0) for v in var_cols)
                result[cd][(female, age_bin)] = pop

    print(f"    Got {len(result)} districts")
    return result


def fetch_education():
    """
    Fetch B15003 (Educational Attainment, 25+) for all congressional districts.
    Returns dict: cd_label -> {educ_bin: population}
    """
    # B15003: Educational Attainment for Population 25+
    # 001: Total
    # 002-016: No college (no schooling through 12th grade no diploma)
    # 017: Regular high school diploma
    # 018: GED
    # 019-021: Some college (some college no degree, associate's)
    # 022: Bachelor's
    # 023-025: Graduate (master's, professional, doctorate)

    no_college = [f"B15003_{str(i).zfill(3)}E" for i in range(2, 19)]  # 002-018
    some_college = ["B15003_019E", "B15003_020E", "B15003_021E"]  # some college + associate's
    college_plus = ["B15003_022E", "B15003_023E", "B15003_024E", "B15003_025E"]  # bachelor's+

    all_vars = no_college + some_college + college_plus

    # API has a 50-variable limit per request, split if needed
    result = {}
    print("  Fetching education data (B15003)...")

    for state_fips in STATES:
        try:
            rows = fetch_api(all_vars, state_fips)
        except Exception as e:
            print(f"    Error fetching {state_fips}: {e}")
            continue

        for row in rows:
            cd = cd_label(row["state"], row["congressional district"])
            nc = sum(int(row.get(v, 0) or 0) for v in no_college)
            sc = sum(int(row.get(v, 0) or 0) for v in some_college)
            cp = sum(int(row.get(v, 0) or 0) for v in college_plus)
            result[cd] = {
                "no_college": nc,
                "some_college": sc,
                "college_plus": cp,
            }

    print(f"    Got {len(result)} districts")
    return result


def fetch_race():
    """
    Fetch B03002 (Hispanic/Latino Origin by Race) for all congressional districts.
    Returns dict: cd_label -> {race_bin: population}
    """
    # B03002: Hispanic or Latino Origin by Race
    # 003: Not Hispanic, White alone
    # 004: Not Hispanic, Black alone
    # 012: Hispanic or Latino (any race)
    # Total (001) minus white+black+hispanic = other
    vars_needed = ["B03002_001E", "B03002_003E", "B03002_004E", "B03002_012E"]

    result = {}
    print("  Fetching race/ethnicity data (B03002)...")

    for state_fips in STATES:
        try:
            rows = fetch_api(vars_needed, state_fips)
        except Exception as e:
            print(f"    Error fetching {state_fips}: {e}")
            continue

        for row in rows:
            cd = cd_label(row["state"], row["congressional district"])
            total = int(row.get("B03002_001E", 0) or 0)
            white = int(row.get("B03002_003E", 0) or 0)
            black = int(row.get("B03002_004E", 0) or 0)
            hispanic = int(row.get("B03002_012E", 0) or 0)
            other = max(0, total - white - black - hispanic)
            result[cd] = {
                "white": white,
                "black": black,
                "hispanic": hispanic,
                "other": other,
            }

    print(f"    Got {len(result)} districts")
    return result


def rake_cells(age_sex_marginals, educ_marginals, race_marginals, max_iter=50, tol=1e-4):
    """
    Iterative proportional fitting (raking) to create synthetic joint distribution
    from marginal distributions.

    Given:
      - age_sex: {(female, age_bin): pop}  (8 cells)
      - educ: {educ_bin: pop}  (3 cells)
      - race: {race_bin: pop}  (4 cells)

    Returns list of dicts with (female, age_bin, educ_bin, race_bin, population).
    """
    females = [0, 1]
    age_bins = ["18-29", "30-44", "45-64", "65+"]
    educ_bins = ["no_college", "some_college", "college_plus"]
    race_bins = ["white", "black", "hispanic", "other"]

    # Initialize with uniform distribution
    cells = {}
    for f, a, e, r in itertools.product(females, age_bins, educ_bins, race_bins):
        cells[(f, a, e, r)] = 1.0

    # Target marginals
    age_sex_total = sum(age_sex_marginals.values()) or 1
    educ_total = sum(educ_marginals.values()) or 1
    race_total = sum(race_marginals.values()) or 1

    for _ in range(max_iter):
        max_change = 0

        # Fit to age × sex marginals
        for f, a in itertools.product(females, age_bins):
            current = sum(cells[(f, a, e, r)] for e in educ_bins for r in race_bins)
            target = age_sex_marginals.get((f, a), 0)
            if current > 0 and target > 0:
                factor = target / current
                for e in educ_bins:
                    for r in race_bins:
                        old = cells[(f, a, e, r)]
                        cells[(f, a, e, r)] *= factor
                        max_change = max(max_change, abs(cells[(f, a, e, r)] - old))

        # Fit to education marginals (scaled to 18+ population)
        for e in educ_bins:
            current = sum(cells[(f, a, e, r)] for f in females for a in age_bins for r in race_bins)
            # Scale educ marginals (25+) to match the 18+ total from age_sex
            target = educ_marginals.get(e, 0) * (age_sex_total / educ_total) if educ_total > 0 else 0
            if current > 0 and target > 0:
                factor = target / current
                for f in females:
                    for a in age_bins:
                        for r in race_bins:
                            old = cells[(f, a, e, r)]
                            cells[(f, a, e, r)] *= factor
                            max_change = max(max_change, abs(cells[(f, a, e, r)] - old))

        # Fit to race marginals (scaled to 18+ population)
        for r in race_bins:
            current = sum(cells[(f, a, e, r)] for f in females for a in age_bins for e in educ_bins)
            target = race_marginals.get(r, 0) * (age_sex_total / race_total) if race_total > 0 else 0
            if current > 0 and target > 0:
                factor = target / current
                for f in females:
                    for a in age_bins:
                        for e in educ_bins:
                            old = cells[(f, a, e, r)]
                            cells[(f, a, e, r)] *= factor
                            max_change = max(max_change, abs(cells[(f, a, e, r)] - old))

        if max_change < tol:
            break

    return [
        {"female": f, "age_bin": a, "educ_bin": e, "race_bin": r, "population": round(cells[(f, a, e, r)])}
        for f, a, e, r in itertools.product(females, age_bins, educ_bins, race_bins)
        if cells[(f, a, e, r)] > 0.5  # Drop near-zero cells
    ]


def main():
    if not API_KEY:
        print("ERROR: Set CENSUS_API_KEY environment variable")
        print("Get a free key at: https://api.census.gov/data/key_signup.html")
        sys.exit(1)

    print(f"Fetching ACS {ACS_YEAR} 5-year data by congressional district...")

    age_sex = fetch_age_sex()
    educ = fetch_education()
    race = fetch_race()

    # Get all districts present in all three datasets
    all_cds = set(age_sex.keys()) & set(educ.keys()) & set(race.keys())
    print(f"\n  {len(all_cds)} districts with complete demographic data")

    # Rake marginals into joint distribution for each district
    print("  Raking marginals into joint distribution...")
    rows = []
    for cd in sorted(all_cds):
        cells = rake_cells(age_sex[cd], educ[cd], race[cd])
        for cell in cells:
            cell["cd_clean"] = cd
            rows.append(cell)

    # Write output
    fieldnames = ["cd_clean", "female", "age_bin", "educ_bin", "race_bin", "population"]
    with open(OUTPUT_FILE, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(f"\n  Wrote {len(rows)} cells to {OUTPUT_FILE}")

    # Sanity check: show KY-01 demographics
    ky01 = [r for r in rows if r["cd_clean"] == "KY-01"]
    total = sum(r["population"] for r in ky01)
    educ_dist = {}
    for r in ky01:
        educ_dist[r["educ_bin"]] = educ_dist.get(r["educ_bin"], 0) + r["population"]
    print(f"\n  KY-01 sanity check ({total:,} total 18+ pop):")
    for e in ["no_college", "some_college", "college_plus"]:
        pct = educ_dist.get(e, 0) / total * 100 if total > 0 else 0
        print(f"    {e}: {pct:.1f}%")


if __name__ == "__main__":
    main()
