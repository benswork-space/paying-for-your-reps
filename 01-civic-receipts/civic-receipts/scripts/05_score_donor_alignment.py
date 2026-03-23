#!/usr/bin/env python3
"""
Score donor alignment: how often does each member vote in line
with their actual top PAC donors' interests?

Approach:
- Uses each member's ACTUAL top PAC donors (by amount)
- Maps PAC names to policy categories using a registry
- Matches votes to categories using keywords in vote descriptions
- Deduplicates by bill number (keeps the most substantive vote)
- Weights alignment score by donation amount
- Calls out specific donor names in examples

Outputs: data/raw/donor_alignment.json
"""

import json
import os
import re
import sys
import time
import urllib.request
import urllib.error

import csv

RAW_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "raw")
PUBLIC_MEMBERS_DIR = os.path.join(os.path.dirname(__file__), "..", "public", "data", "members")
CACHE_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "scripts", ".cache")
ENV_LOCAL = os.path.join(os.path.dirname(__file__), "..", ".env.local")


def load_dotenv(path=ENV_LOCAL):
    """Load key=value pairs from .env.local into os.environ (won't overwrite)."""
    if not os.path.exists(path):
        return
    with open(path) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, value = line.partition("=")
            os.environ.setdefault(key.strip(), value.strip())


# ── Policy area → PAC category mapping ──────────────────────────────
# Congress.gov bills have a policyArea.name field. We map those to our
# PAC_REGISTRY categories so votes that don't match any keyword can still
# be scored if the bill's subject aligns with a donor category.
POLICY_AREA_TO_CATEGORIES = {
    "Health": ["HEALTHCARE"],
    "Armed Forces and National Security": ["DEFENSE"],
    "Energy": ["ENERGY_FOSSIL", "ENERGY_CLEAN"],
    "Finance and Financial Sector": ["FINANCE"],
    "Science, Technology, Communications": ["TECH", "TELECOM"],
    "Housing and Community Development": ["REAL_ESTATE"],
    "Agriculture and Food": ["AGRICULTURE"],
    "Crime and Law Enforcement": ["GUN_CONTROL", "GUN_RIGHTS"],
    "Labor and Employment": ["LABOR"],
    "International Affairs": ["FOREIGN_POLICY_ISRAEL"],
    "Environmental Protection": ["ENERGY_CLEAN", "ENERGY_FOSSIL"],
    "Transportation and Public Works": ["DEFENSE"],
    "Education": ["LABOR"],
    "Economics and Public Finance": ["FINANCE"],
    "Taxation": ["FINANCE"],
    "Commerce": ["TECH"],
    "Civil Rights and Liberties, Minority Issues": ["REPRODUCTIVE_RIGHTS"],
}

# Default expected position for policy_area matches (by category).
# Used when a vote matches via policy_area but no keyword gave a specific position.
# These represent the industry's general "pro-industry" stance.
CATEGORY_DEFAULT_POSITION = {
    "HEALTHCARE": "Yea",
    "DEFENSE": "Yea",
    "FINANCE": "Yea",
    "TECH": "Yea",
    "TELECOM": "Yea",
    "REAL_ESTATE": "Yea",
    "AGRICULTURE": "Yea",
    "LABOR": "Yea",
    "ENERGY_FOSSIL": "Yea",
    "ENERGY_CLEAN": "Yea",
    "GUN_CONTROL": "Yea",
    "GUN_RIGHTS": "Yea",
    "REPRODUCTIVE_RIGHTS": "Yea",
    "AUTO": "Yea",
    "FOREIGN_POLICY_ISRAEL": "Yea",
}


def parse_voteview_bill(bill_str):
    """
    Parse a Voteview bill string like 'HR1234' into (bill_type, number).
    Returns (type_slug, number_str) for Congress.gov API, e.g. ('hr', '1234').
    Returns (None, None) if unparseable.
    """
    if not bill_str:
        return None, None
    bill_str = bill_str.strip()
    # Order matters: check longer prefixes first
    for prefix, slug in [
        ("HCONRES", "hconres"), ("SCONRES", "sconres"),
        ("HJRES", "hjres"), ("SJRES", "sjres"),
        ("HRES", "hres"), ("SRES", "sres"),
        ("HR", "hr"), ("S", "s"),
    ]:
        if bill_str.upper().startswith(prefix):
            num = bill_str[len(prefix):]
            if num.isdigit():
                return slug, num
            break
    return None, None


def fetch_bill_subjects(congresses=None):
    """
    Fetch policy_area for all bills in our Voteview rollcall data.
    Uses the Congress.gov API with caching.
    Returns dict: "HR1234" -> "Health" (bill_str -> policy_area name).
    """
    load_dotenv()
    api_key = os.environ.get("CONGRESS_API_KEY", "")
    if not api_key:
        print("  No CONGRESS_API_KEY set — skipping policy_area fetching.")
        return {}

    if congresses is None:
        congresses = [114, 115, 116, 117, 118, 119]

    os.makedirs(CACHE_DIR, exist_ok=True)
    all_subjects = {}

    for congress in congresses:
        cache_path = os.path.join(CACHE_DIR, f"bill_subjects_{congress}.json")

        # Load cache if exists
        if os.path.exists(cache_path):
            with open(cache_path) as f:
                cached = json.load(f)
            all_subjects.update(cached)
            print(f"  Congress {congress}: loaded {len(cached)} cached bill subjects")
            continue

        # Collect unique bill numbers from rollcall CSVs for this congress
        bills_to_fetch = set()
        for prefix in ["H", "S"]:
            rc_path = os.path.join(CACHE_DIR, f"{prefix}{congress}_rollcalls.csv")
            if not os.path.exists(rc_path):
                continue
            with open(rc_path) as f:
                for row in csv.DictReader(f):
                    bn = (row.get("bill_number") or "").strip()
                    if bn:
                        bills_to_fetch.add(bn)

        if not bills_to_fetch:
            print(f"  Congress {congress}: no rollcall data found")
            continue

        print(f"  Congress {congress}: fetching policy_area for {len(bills_to_fetch)} bills...")
        congress_subjects = {}
        fetched = 0
        errors = 0

        for bill_str in sorted(bills_to_fetch):
            bill_type, bill_num = parse_voteview_bill(bill_str)
            if not bill_type:
                continue

            url = (
                f"https://api.congress.gov/v3/bill/{congress}/{bill_type}/{bill_num}"
                f"?api_key={api_key}&format=json"
            )
            try:
                req = urllib.request.Request(url, headers={"User-Agent": "CivicReceipts/1.0"})
                resp = urllib.request.urlopen(req, timeout=15)
                data = json.loads(resp.read().decode())
                pa = data.get("bill", {}).get("policyArea", {})
                if pa and pa.get("name"):
                    congress_subjects[bill_str] = pa["name"]
                fetched += 1
            except urllib.error.HTTPError as e:
                if e.code == 404:
                    pass  # Bill not found — skip
                elif e.code == 429:
                    print(f"    Rate limited — pausing 60s...")
                    time.sleep(60)
                    errors += 1
                else:
                    errors += 1
            except Exception:
                errors += 1

            # Rate limit: ~5 requests/second to stay well under 1000/hour
            if fetched % 5 == 0:
                time.sleep(1.1)

            if fetched % 100 == 0 and fetched > 0:
                print(f"    ...fetched {fetched}/{len(bills_to_fetch)}")

        # Save cache
        with open(cache_path, "w") as f:
            json.dump(congress_subjects, f, indent=2)

        all_subjects.update(congress_subjects)
        print(f"  Congress {congress}: got policy_area for {len(congress_subjects)}/{len(bills_to_fetch)} bills ({errors} errors)")

    return all_subjects

# ── PAC Registry ──────────────────────────────────────────────────────
# Maps PAC name patterns to policy categories and their expected positions
# on specific issue keywords.
#
# "positions" maps issue keywords → expected vote direction.
# Use word boundary markers in keywords for precision.
PAC_REGISTRY = {
    "LABOR": {
        "patterns": [
            "LETTER CARRIERS", "CARPENTERS", "TEACHERS COPE",
            "MACHINISTS", "AFSCME", "AFL-CIO", "LABORER",
            "COMMUNICATIONS WORKERS", "TRANSPORT WORKERS",
            "FIRE FIGHTERS", "PILOTS ASSOCIATION", "TEAMSTERS",
            "SEIU", "IBEW", "AUTO WORKERS", "PLUMBERS",
            "IRONWORKERS", "STEELWORKERS", "ENGINEERS POLITICAL",
            "AMERICAN FEDERATION OF STATE",
            # Additional labor unions
            "AIR TRAFFIC CONTROLLERS", "TREASURY EMPLOYEES UNION",
            "NEA FUND FOR CHILDREN", "NATIONAL EDUCATION ASSOCIATION",
            "RETIRED FEDERAL EMP", "NARFE",
            "DIRECTORS GUILD", "DGA-PAC",
            "HEALTH JOBS JUSTICE",
            "POSTAL WORKERS", "USPS",
        ],
        "positions": {
            "minimum wage": "Yea",
            "pro act": "Yea",
            "paid leave": "Yea",
            "overtime": "Yea",
            "workplace safety": "Yea",
            "osha": "Yea",
            "workers' rights": "Yea",
            "right to work": "Nay",
        },
        "label": "Labor unions",
    },
    "HEALTHCARE": {
        "patterns": [
            "DENTAL ASSOCIATION", "HOSPITAL ASSOCIATION",
            "AMERICAN MEDICAL", "AFLAC", "DAVITA", "KAISER",
            "PHARMACEUTICAL", "PFIZER", "MERCK", "ABBOTT",
        ],
        "positions": {
            "affordable care": "Yea",
            "medicare": "Yea",
            "medicaid": "Yea",
            "prescription drug": "Yea",
            "insulin": "Yea",
            "health care": "Yea",
        },
        "label": "Healthcare industry",
    },
    "REAL_ESTATE": {
        "patterns": [
            "REALTORS", "MULTI HOUSING", "HOME DEPOT",
            "HOMEBUILDERS", "MORTGAGE BANKERS",
            # Additional real estate
            "MULTIFAMILY HOUSING COUNCIL",
        ],
        "positions": {
            "housing": "Yea",
            "mortgage": "Yea",
            "homeowner": "Yea",
            "real estate": "Yea",
            "rental": "Yea",
            "rent control": "Nay",
        },
        "label": "Real estate industry",
    },
    "DEFENSE": {
        "patterns": [
            "L3HARRIS", "LOCKHEED", "RAYTHEON", "NORTHROP",
            "BAE SYSTEMS", "BOEING", "GENERAL DYNAMICS",
            "BOOZ ALLEN", "LEIDOS",
            # Additional defense
            "TRANSDIGM",
        ],
        "positions": {
            "national defense authorization": "Yea",
            "ndaa": "Yea",
            "defense appropriation": "Yea",
            "military spending": "Yea",
            "pentagon": "Yea",
            "military construction": "Yea",
        },
        "label": "Defense contractors",
    },
    "TELECOM": {
        "patterns": [
            "COMCAST", "AT&T", "VERIZON", "CHARTER",
            "T-MOBILE", "NBCUNIVERSAL",
        ],
        "positions": {
            "broadband": "Yea",
            "net neutrality": "Nay",
            "section 230": "Nay",
        },
        "label": "Telecom companies",
    },
    "TECH": {
        "patterns": [
            "GOOGLE", "MICROSOFT", "CISCO", "DROPBOX",
            "ORACLE", "APPLE", "META", "AMAZON",
            # Additional tech
            "HEWLETT PACKARD", "SIEMENS",
        ],
        "positions": {
            "data privacy": "Nay",
            "section 230": "Nay",
            "broadband": "Yea",
            "cybersecurity": "Yea",
            "artificial intelligence": "Yea",
        },
        "label": "Tech companies",
    },
    "FINANCE": {
        "patterns": [
            "GOLDMAN", "JPMORGAN", "CITIGROUP", "BANK OF AMERICA",
            "CREDIT UNION", "VISA", "MASTERCARD", "BLACKSTONE",
            "MORGAN STANLEY", "WELLS FARGO",
            # Additional finance
            "AMALGAMATED BANK", "FIDELITY BROKERAGE",
            "FIDELITY INVESTMENTS", "CAPITAL GROUP",
        ],
        "positions": {
            "financial regulation": "Nay",
            "dodd-frank": "Nay",
            "consumer financial": "Nay",
            "banking": "Yea",
            "capital markets": "Yea",
        },
        "label": "Financial industry",
    },
    "ENERGY_FOSSIL": {
        "patterns": [
            "PETROLEUM", "CHEVRON", "EXXON", "KOCH",
            "PIPELINE", "NATURAL GAS", "COAL",
        ],
        "positions": {
            "clean energy": "Nay",
            "emissions": "Nay",
            "carbon tax": "Nay",
            "renewable energy": "Nay",
            "drilling": "Yea",
            "pipeline": "Yea",
            "lng export": "Yea",
        },
        "label": "Fossil fuel industry",
    },
    "ENERGY_CLEAN": {
        "patterns": [
            "SOLAR", "WIND ENERGY", "CLEAN ENERGY",
            "LEAGUE OF CONSERVATION", "SIERRA",
        ],
        "positions": {
            "clean energy": "Yea",
            "emissions": "Yea",
            "carbon": "Yea",
            "renewable energy": "Yea",
            "drilling": "Nay",
            "pipeline": "Nay",
        },
        "label": "Clean energy industry",
    },
    "AGRICULTURE": {
        "patterns": [
            "CRYSTAL SUGAR", "FARM BUREAU", "DAIRY",
            "FOOD SOLUTIONS", "CARGILL", "ADM",
            # Additional agriculture
            "RICE INDUSTRY", "BEER WHOLESALERS",
            "WINE INSTITUTE",
        ],
        "positions": {
            "farm bill": "Yea",
            "agriculture appropriation": "Yea",
            "snap": "Yea",
            "crop insurance": "Yea",
            "sugar": "Yea",
        },
        "label": "Agriculture industry",
    },
    "GUN_CONTROL": {
        "patterns": [
            "EVERYTOWN", "GIFFORDS", "BRADY", "MOMS DEMAND",
        ],
        "positions": {
            "background check": "Yea",
            "assault weapon": "Yea",
            "ghost gun": "Yea",
            "red flag": "Yea",
        },
        "label": "Gun control advocates",
    },
    "GUN_RIGHTS": {
        "patterns": [
            "NATIONAL RIFLE", "GUN OWNERS OF AMERICA",
            "NATIONAL SHOOTING",
        ],
        "positions": {
            "background check": "Nay",
            "assault weapon": "Nay",
            "concealed carry": "Yea",
            "second amendment": "Yea",
        },
        "label": "Gun rights advocates",
    },
    "REPRODUCTIVE_RIGHTS": {
        "patterns": [
            "PLANNED PARENTHOOD", "EMILY", "NARAL",
            "REPRODUCTIVE FREEDOM",
        ],
        "positions": {
            "abortion": "Yea",
            "reproductive": "Yea",
            "contraception": "Yea",
        },
        "label": "Reproductive rights groups",
    },
    "AUTO": {
        "patterns": [
            "AUTOMOBILE DEALERS", "NATIONAL AUTO",
        ],
        "positions": {
            "emission standards": "Nay",
            "electric vehicle mandate": "Nay",
            "auto": "Yea",
        },
        "label": "Auto industry",
    },
    "FOREIGN_POLICY_ISRAEL": {
        "patterns": [
            "AIPAC", "AMERICAN ISRAEL PUBLIC AFFAIRS",
            "JOINT ACTION COMMITTEE FOR POLITICAL",
        ],
        "positions": {
            "iron dome": "Yea",
            "israel supplemental appropriations": "Yea",
            "anti-semitism": "Yea",
        },
        "label": "Pro-Israel groups",
    },
}

# Vote questions that indicate the "final" most substantive vote on a bill
SUBSTANTIVE_QUESTIONS = [
    "On Passage",
    "On the Conference Report",
    "On the Joint Resolution",
    "On the Concurrent Resolution",
    "On the Resolution",
    "On Cloture",
    "On Overriding the Veto",
]

# Keywords indicating the bill inverts the expected position
# e.g., "Repealing the ACA" — a healthcare PAC would want Nay, not Yea
INVERSION_KEYWORDS = [
    "repeal", "rescind", "disapprov", "terminat", "eliminat",
    "prohibit", "block", "defund", "restrict", "ban on",
    "strike the", "nullif",
]


def load_party_splits(chamber, congresses=None):
    """
    Load party-line vote splits from Voteview data across multiple congresses.
    Returns dict: (congress, roll_number) -> {D_yea, D_nay, R_yea, R_nay}
    """
    if congresses is None:
        congresses = [114, 115, 116, 117, 118, 119]

    prefix = "H" if chamber == "house" else "S"
    splits = {}

    for congress in congresses:
        votes_path = os.path.join(CACHE_DIR, f"{prefix}{congress}_votes.csv")
        members_path = os.path.join(CACHE_DIR, f"{prefix}{congress}_members.csv")

        if not os.path.exists(votes_path) or not os.path.exists(members_path):
            continue

        # Load member party codes
        party_by_icpsr = {}
        with open(members_path) as f:
            for row in csv.DictReader(f):
                try:
                    icpsr = int(float(row["icpsr"]))
                except (ValueError, TypeError):
                    continue
                party_by_icpsr[icpsr] = row.get("party_code", "")

        # Compute splits
        with open(votes_path) as f:
            for row in csv.DictReader(f):
                try:
                    rn = int(float(row["rollnumber"]))
                    icpsr = int(float(row["icpsr"]))
                    cast = int(float(row["cast_code"]))
                except (ValueError, TypeError):
                    continue
                party = party_by_icpsr.get(icpsr, "")

                key = (congress, rn)
                if key not in splits:
                    splits[key] = {"D_yea": 0, "D_nay": 0, "R_yea": 0, "R_nay": 0}

                if party == "100":  # Democrat
                    if cast in (1, 2, 3):
                        splits[key]["D_yea"] += 1
                    elif cast in (4, 5, 6):
                        splits[key]["D_nay"] += 1
                elif party == "200":  # Republican
                    if cast in (1, 2, 3):
                        splits[key]["R_yea"] += 1
                    elif cast in (4, 5, 6):
                        splits[key]["R_nay"] += 1

    return splits


def get_donor_party_lean(member_data):
    """
    Determine whether this member's donors lean D or R.
    For now, use the member's own party as a proxy — PAC donors
    overwhelmingly donate to their party's candidates.
    """
    return member_data.get("party", "D")


def get_expected_position_with_party_context(
    base_expected, member_party, party_split, vote
):
    """
    Adjust expected position using party-line context.

    If a bill has a strong party-line split (e.g., 210-0 D Nay, 216-1 R Yea),
    and the member is a Democrat, then their donors (who mostly donate to Dems)
    likely wanted the Democrat position.

    This handles misleading bill names like "Do No Harm in Medicaid Act"
    where the name suggests Yea but Democrats overwhelmingly voted Nay.
    """
    if not party_split:
        return base_expected

    d_yea = party_split.get("D_yea", 0)
    d_nay = party_split.get("D_nay", 0)
    r_yea = party_split.get("R_yea", 0)
    r_nay = party_split.get("R_nay", 0)

    d_total = d_yea + d_nay
    r_total = r_yea + r_nay

    if d_total < 10 or r_total < 10:
        return base_expected

    d_yea_pct = d_yea / d_total
    r_yea_pct = r_yea / r_total

    # Only adjust on strong party-line votes (>60% gap between parties)
    is_party_line = abs(d_yea_pct - r_yea_pct) > 0.6
    if not is_party_line:
        return base_expected

    # Determine which party "owns" the bill (overwhelmingly voted Yea)
    bill_party = "R" if r_yea_pct > 0.8 else ("D" if d_yea_pct > 0.8 else None)
    if not bill_party:
        return base_expected

    # If the keyword says "Yea" but the bill was authored by the opposite party
    # from the member's donors, the bill likely undermines the keyword's intent.
    # e.g., "Do No Harm in Medicaid" (R bill) — keyword "medicaid" says Yea,
    # but for Dem-aligned healthcare PACs, the real expected position is Nay.
    if member_party != bill_party and base_expected == "Yea":
        return "Nay"
    elif member_party != bill_party and base_expected == "Nay":
        return "Yea"

    return base_expected


def classify_pac(pac_name):
    """Return the category key for a PAC name, or None."""
    name_upper = pac_name.upper()
    for category, info in PAC_REGISTRY.items():
        for pattern in info["patterns"]:
            if pattern in name_upper:
                return category
    return None


def get_top_pac_donors(member_data, top_n=50):
    """
    Extract the top N PAC donors by amount from a member's funding data.
    Returns list of {name, amount, category, category_label}.
    """
    all_pacs = []

    # Campaign committee PAC donors
    campaign = member_data.get("funding", {}).get("campaign", {})
    for donor in campaign.get("top_pac_donors", []):
        all_pacs.append(donor)

    # Leadership PAC donors
    for lp in member_data.get("funding", {}).get("leadership_pacs", []):
        for donor in lp.get("top_pac_donors", []):
            all_pacs.append(donor)

    # Also check top_industries for backward compat
    for ind in member_data.get("funding", {}).get("top_industries", []):
        if ind.get("code") in ("PAC", "LPAC"):
            for donor in ind.get("donors", []):
                all_pacs.append(donor)

    # Deduplicate by name, summing amounts
    merged = {}
    for p in all_pacs:
        name = p.get("name", "")
        if not name:
            continue
        if name not in merged:
            merged[name] = {"name": name, "amount": 0}
        merged[name]["amount"] += abs(p.get("amount", 0))

    # Sort by amount and take top N
    sorted_pacs = sorted(merged.values(), key=lambda x: -x["amount"])[:top_n]

    # Classify each
    for pac in sorted_pacs:
        category = classify_pac(pac["name"])
        if category:
            pac["category"] = category
            pac["category_label"] = PAC_REGISTRY[category]["label"]
        else:
            pac["category"] = None
            pac["category_label"] = None

    return sorted_pacs


def is_inverted(description, vote=None):
    """
    Check if vote description suggests the bill inverts expected positions.

    Also checks: if this was a party-line vote where one party overwhelmingly
    opposed it, the bill likely does the opposite of what its name suggests
    for that party's donors.
    """
    desc_lower = description.lower()
    if any(kw in desc_lower for kw in INVERSION_KEYWORDS):
        return True

    # Bills with misleadingly positive names that actually restrict/cut:
    # We check if there's a "Motion to Recommit" pattern — if the member voted
    # Yea on recommit but Nay on passage, the bill's intent is opposite to
    # what the name suggests (for that member's perspective).
    # This is handled at the scoring level instead.
    return False


def is_cra_vote(vote):
    """Check if this is a Congressional Review Act disapproval resolution."""
    desc = (vote.get("description", "") or "").lower()
    return any(kw in desc for kw in [
        "congressional disapproval",
        "providing for congressional disapproval",
        "disapproving the rule submitted",
        "disappoving the rule submitted",  # typo in source data
    ])


def is_nomination_or_procedural(vote):
    """
    Check if a vote is a nomination/confirmation, purely procedural,
    or a CRA disapproval resolution. These should NOT be scored.
    """
    # Filter out CRA votes — they're formulaic party-line votes
    if is_cra_vote(vote):
        return True

    desc = (vote.get("description", "") or "").lower()
    question = (vote.get("question", "") or "").lower()

    # Nomination/confirmation votes
    nomination_patterns = [
        r"\bto be\b.*\b(administrator|secretary|director|commissioner|"
        r"ambassador|judge|justice|member of the|chair|under secretary|"
        r"inspector general|attorney general|surgeon general)\b",
        r"\bnominat",
        r"\bconfirmation\b",
    ]
    for pat in nomination_patterns:
        if re.search(pat, desc):
            return True

    # Nomination questions
    if "on the nomination" in question or "on the cloture motion" in question:
        return True

    # Procedural questions (not final passage)
    procedural_questions = [
        "on ordering the previous question",
        "on the motion to table",
        "on motion to suspend the rules",
        "on the motion to discharge",
        "on the point of order",
        "on motion to commit",
        "on motion to recommit",
        "on cloture on the motion to proceed",
        "on the motion to proceed",
        "election of the speaker",
        "providing for consideration",
        "on approving the journal",
        "on the motion to adjourn",
        "quorum call",
    ]
    for pq in procedural_questions:
        if pq in question.lower() or pq in desc:
            return True

    return False


def match_vote_to_categories(vote, categories_with_pacs, bill_subjects=None):
    """
    Check if a vote description matches any of the active PAC categories.
    Returns list of (category, keyword, expected_position, [donor_names]).
    Skips nomination and procedural votes.

    Uses two matching strategies:
    1. Keyword matching on vote description (high precision)
    2. Bill policy_area from Congress.gov API (broader coverage)
    """
    # Skip nominations and procedural votes
    if is_nomination_or_procedural(vote):
        return []

    desc = (vote.get("description", "") + " " + vote.get("bill", "")).lower()
    matches = []
    matched_categories = set()

    # Strategy 1: Keyword matching (same as before)
    for category, pacs in categories_with_pacs.items():
        positions = PAC_REGISTRY[category]["positions"]
        for keyword, expected_pos in positions.items():
            # Use word boundary matching to avoid substring false positives
            pattern = r'\b' + re.escape(keyword) + r'\b'
            if re.search(pattern, desc, re.IGNORECASE):
                # Check if vote inverts the expected position
                actual_expected = expected_pos
                if is_inverted(vote.get("description", "")):
                    actual_expected = "Nay" if expected_pos == "Yea" else "Yea"

                donor_names = [p["name"] for p in pacs]
                donor_amounts = sum(p["amount"] for p in pacs)
                matches.append({
                    "category": category,
                    "keyword": keyword,
                    "expected_position": actual_expected,
                    "donor_names": donor_names[:3],  # Top 3 by amount
                    "donor_total": donor_amounts,
                    "label": PAC_REGISTRY[category]["label"],
                })
                matched_categories.add(category)
                break  # One match per category per vote

    # Strategy 2: Policy area matching (for categories not already matched)
    if bill_subjects:
        bill_str = (vote.get("bill") or "").strip()
        policy_area = bill_subjects.get(bill_str)
        if policy_area:
            pa_categories = POLICY_AREA_TO_CATEGORIES.get(policy_area, [])
            for category in pa_categories:
                if category in matched_categories:
                    continue  # Already matched by keyword
                if category not in categories_with_pacs:
                    continue  # Member doesn't have donors in this category

                pacs = categories_with_pacs[category]
                default_pos = CATEGORY_DEFAULT_POSITION.get(category, "Yea")
                actual_expected = default_pos
                if is_inverted(vote.get("description", "")):
                    actual_expected = "Nay" if default_pos == "Yea" else "Yea"

                donor_names = [p["name"] for p in pacs]
                donor_amounts = sum(p["amount"] for p in pacs)
                matches.append({
                    "category": category,
                    "keyword": f"[policy_area: {policy_area}]",
                    "expected_position": actual_expected,
                    "donor_names": donor_names[:3],
                    "donor_total": donor_amounts,
                    "label": PAC_REGISTRY[category]["label"],
                })
                matched_categories.add(category)

    return matches


def deduplicate_votes(votes):
    """
    Deduplicate votes by bill number.
    Keeps the most substantive vote (On Passage > On Amendment).
    """
    bill_votes = {}
    for v in votes:
        bill = v.get("bill", "")
        if not bill:
            # No bill number — keep as unique
            bill = f"_roll_{v.get('roll_number', 0)}"

        question = v.get("question", "")

        if bill not in bill_votes:
            bill_votes[bill] = v
        else:
            # Replace if this is a more substantive question type
            existing_q = bill_votes[bill].get("question", "")
            for sq in SUBSTANTIVE_QUESTIONS:
                if sq in question and sq not in existing_q:
                    bill_votes[bill] = v
                    break

    return list(bill_votes.values())


def score_member(member_id, member_data, votes_data, party_splits, bill_subjects=None):
    """
    Score donor alignment for a single member.

    Returns alignment data with:
    - overall_pct (weighted by donation amount)
    - total_votes_scored
    - examples with specific donor callouts
    """
    top_pacs = get_top_pac_donors(member_data, top_n=50)
    member_party = member_data.get("party", "")

    # Group classified PACs by category
    categories_with_pacs = {}
    for pac in top_pacs:
        cat = pac.get("category")
        if cat:
            if cat not in categories_with_pacs:
                categories_with_pacs[cat] = []
            categories_with_pacs[cat].append(pac)

    if not categories_with_pacs:
        return {
            "overall_pct": 0,
            "total_votes_scored": 0,
            "methodology_url": "/methodology#donor-alignment",
            "examples": [],
        }

    # Get votes and deduplicate by bill
    votes = votes_data.get("recent_votes", [])
    deduped_votes = deduplicate_votes(votes)

    # Score each vote
    scored_votes = []
    for vote in deduped_votes:
        position = vote.get("position")
        if not position or position in ("Absent", "Present", "N/A"):
            continue

        matches = match_vote_to_categories(vote, categories_with_pacs, bill_subjects)
        if not matches:
            continue

        # Use the match with the highest donor total (most money at stake)
        best_match = max(matches, key=lambda m: m["donor_total"])

        # Adjust expected position using party-line context
        # This handles misleading bill names (e.g., "Do No Harm in Medicaid"
        # which actually cuts Medicaid — Dems vote Nay, Rs vote Yea)
        roll_number = vote.get("roll_number")
        congress = vote.get("congress", 119)
        party_split = party_splits.get((congress, roll_number)) if roll_number else None
        adjusted_expected = get_expected_position_with_party_context(
            best_match["expected_position"],
            member_party,
            party_split,
            vote,
        )

        aligned = position == adjusted_expected

        scored_votes.append({
            "vote_description": vote.get("description", ""),
            "bill": vote.get("bill", ""),
            "date": vote.get("date", ""),
            "member_voted": position,
            "donor_expected": adjusted_expected,
            "aligned": aligned,
            "donor_names": best_match["donor_names"],
            "donor_total": best_match["donor_total"],
            "category": best_match["category"],
            "category_label": best_match["label"],
            "keyword": best_match["keyword"],
        })

    if not scored_votes:
        return {
            "overall_pct": 0,
            "total_votes_scored": 0,
            "methodology_url": "/methodology#donor-alignment",
            "examples": [],
        }

    # Calculate weighted alignment score
    total_weight = 0
    weighted_aligned = 0
    simple_aligned = 0

    for sv in scored_votes:
        weight = sv["donor_total"]
        total_weight += weight
        if sv["aligned"]:
            weighted_aligned += weight
            simple_aligned += 1

    overall_pct = round(weighted_aligned / total_weight * 100) if total_weight > 0 else 0

    # Select diverse examples — avoid repeating the same category
    aligned_examples = [sv for sv in scored_votes if sv["aligned"]]
    against_examples = [sv for sv in scored_votes if not sv["aligned"]]

    # Sort by donor_total (higher stakes = more notable)
    aligned_examples.sort(key=lambda e: e["donor_total"], reverse=True)
    against_examples.sort(key=lambda e: e["donor_total"], reverse=True)

    def pick_diverse(examples, n):
        """Pick up to n examples, preferring different categories."""
        picked = []
        seen_categories = set()
        # First pass: one per category
        for ex in examples:
            if ex["category"] not in seen_categories and len(picked) < n:
                picked.append(ex)
                seen_categories.add(ex["category"])
        # Second pass: fill remaining slots
        for ex in examples:
            if ex not in picked and len(picked) < n:
                picked.append(ex)
        return picked

    # Pick examples proportional to alignment
    if overall_pct >= 80:
        n_aligned = min(4, len(aligned_examples))
        n_against = min(1, len(against_examples))
    elif overall_pct >= 50:
        n_aligned = min(3, len(aligned_examples))
        n_against = min(2, len(against_examples))
    else:
        n_aligned = min(1, len(aligned_examples))
        n_against = min(4, len(against_examples))

    selected = []
    for ex in pick_diverse(aligned_examples, n_aligned):
        selected.append({
            "vote_description": ex["vote_description"],
            "bill": ex["bill"],
            "date": ex["date"],
            "member_voted": ex["member_voted"],
            "aligned": True,
            "donor_name": ex["donor_names"][0] if ex["donor_names"] else "",
            "donor_category": ex["category_label"],
            "donor_expected": f"{ex['donor_expected']} on {ex['vote_description'][:60]}",
        })
    for ex in pick_diverse(against_examples, n_against):
        selected.append({
            "vote_description": ex["vote_description"],
            "bill": ex["bill"],
            "date": ex["date"],
            "member_voted": ex["member_voted"],
            "aligned": False,
            "donor_name": ex["donor_names"][0] if ex["donor_names"] else "",
            "donor_category": ex["category_label"],
            "donor_expected": f"{ex['donor_expected']} on {ex['vote_description'][:60]}",
        })

    return {
        "overall_pct": overall_pct,
        "total_votes_scored": len(scored_votes),
        "methodology_url": "/methodology#donor-alignment",
        "examples": selected,
    }


def main():
    load_dotenv()
    print("Scoring donor alignment...")

    # Load party-line splits for both chambers across all congresses
    congresses = [114, 115, 116, 117, 118, 119]
    print(f"  Loading party-line vote data for congresses {congresses}...")
    house_splits = load_party_splits("house", congresses)
    senate_splits = load_party_splits("senate", congresses)
    print(f"  House: {len(house_splits)} votes, Senate: {len(senate_splits)} votes")

    # Fetch bill subjects (policy_area) from Congress.gov API
    print("  Fetching bill subjects from Congress.gov API...")
    bill_subjects = fetch_bill_subjects(congresses)
    print(f"  Total bill subjects: {len(bill_subjects)}")

    # Load members
    members_path = os.path.join(RAW_DIR, "members.json")
    if not os.path.exists(members_path):
        print("ERROR: No members.json. Run 01_fetch_members.py first.")
        sys.exit(1)
    with open(members_path) as f:
        members = json.load(f)

    results = {}
    scored_count = 0

    for member in members:
        bio_id = member["bioguide_id"]

        # Load member's full data (with funding info)
        member_path = os.path.join(PUBLIC_MEMBERS_DIR, f"{bio_id}.json")
        if not os.path.exists(member_path):
            continue
        with open(member_path) as f:
            member_data = json.load(f)

        # Load member's votes
        votes_path = os.path.join(PUBLIC_MEMBERS_DIR, f"{bio_id}_votes.json")
        if not os.path.exists(votes_path):
            continue
        with open(votes_path) as f:
            votes_data = json.load(f)

        chamber = member_data.get("chamber", "house")
        splits = house_splits if chamber == "house" else senate_splits
        alignment = score_member(bio_id, member_data, votes_data, splits, bill_subjects)
        results[bio_id] = alignment

        if alignment["total_votes_scored"] > 0:
            scored_count += 1

    # Save
    os.makedirs(RAW_DIR, exist_ok=True)
    out_path = os.path.join(RAW_DIR, "donor_alignment.json")
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2)

    print(f"Scored {scored_count}/{len(results)} members with donor alignment data")

    # Also patch member JSONs directly
    patched = 0
    for bio_id, alignment in results.items():
        member_path = os.path.join(PUBLIC_MEMBERS_DIR, f"{bio_id}.json")
        if not os.path.exists(member_path):
            continue
        with open(member_path) as f:
            member_data = json.load(f)
        member_data["donor_alignment"] = alignment
        with open(member_path, "w") as f:
            json.dump(member_data, f, indent=2)
        patched += 1

    print(f"Patched {patched} member JSON files")

    # Show test results
    for test_id in ["P000197", "S001150", "P000145"]:
        a = results.get(test_id, {})
        name = "?"
        mp = os.path.join(PUBLIC_MEMBERS_DIR, f"{test_id}.json")
        if os.path.exists(mp):
            with open(mp) as f:
                name = json.load(f).get("name", "?")
        print(f"\n  {name} ({test_id}): {a.get('overall_pct', 0)}% aligned, {a.get('total_votes_scored', 0)} votes")
        for ex in a.get("examples", []):
            tag = "ALIGNED" if ex["aligned"] else "AGAINST"
            print(f"    [{tag}] {ex['vote_description'][:55]} | Donor: {ex.get('donor_name', '')[:30]}")


if __name__ == "__main__":
    main()
