#!/usr/bin/env python3
"""
Score electorate alignment: how often does each member vote in line
with their district's opinion on key issues?

Uses:
- District opinion data from public/data/districts/{STATE}-{DISTRICT}.json
  (MRP estimates from CES survey data)
- Member vote records from public/data/members/{bioguide_id}_votes.json
- Bill policy_area from Congress.gov API (cached by script 05)

Mirrors the frontend ElectorateSection.tsx logic so pre-computed and
live results agree.

Outputs: data/raw/electorate_alignment.json
"""

import csv
import json
import os
import re
import sys

RAW_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "raw")
PUBLIC_DIR = os.path.join(os.path.dirname(__file__), "..", "public", "data")
PUBLIC_MEMBERS_DIR = os.path.join(PUBLIC_DIR, "members")
DISTRICTS_DIR = os.path.join(PUBLIC_DIR, "districts")
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


# ── Issue → Vote keyword mapping ────────────────────────────────────
# Mirrors ElectorateSection.tsx ISSUE_VOTE_MAP exactly.
# Each entry maps a district opinion issue to keywords we search for in
# vote descriptions, plus whether "support" on the issue means Yea or Nay.
ISSUE_VOTE_MAP = [
    {
        "issue": "Universal background checks for gun purchases",
        "keywords": ["background check", "gun purchase"],
        "support_means_yea": True,
        "topic": "Gun Control",
        # No policy_area fallback — "Crime and Law Enforcement" is too broad
        # (includes reentry programs, drug bills, officer weapon purchases, etc.)
        "d_position": "Yea",  # Dems support gun control
    },
    {
        "issue": "Ban on assault-style weapons",
        "keywords": ["assault weapon", "assault-style"],
        "support_means_yea": True,
        "topic": "Gun Control",
        "d_position": "Yea",
    },
    {
        "issue": "Abortion should always be legal",
        "keywords": ["abortion", "reproductive right", "right to contraception"],
        "support_means_yea": True,
        "topic": "Abortion",
        "policy_areas": ["Civil Rights and Liberties, Minority Issues", "Health"],
        "pa_keywords": ["abortion", "reproductive", "contraception", "pregnancy", "unborn"],
        "d_position": "Yea",  # Dems are pro-choice
    },
    {
        "issue": "Prohibit all abortions after 20 weeks",
        "keywords": ["20-week", "20 week", "late-term abortion", "pain-capable"],
        "support_means_yea": True,
        "topic": "Abortion",
        "policy_areas": ["Health"],
        "pa_keywords": ["abortion", "reproductive", "unborn", "fetal"],
        "d_position": "Nay",  # Dems oppose abortion bans
        "skip_inversion": True,  # Keywords already target pro-life bills directly
    },
    {
        "issue": "Support the Affordable Care Act",
        "keywords": ["affordable care act", "obamacare"],
        "support_means_yea": True,
        "topic": "Healthcare",
        "policy_areas": ["Health"],
        "pa_keywords": ["health care", "healthcare", "health insurance", "coverage", "premium", "medicaid", "medicare", "affordable care"],
        "d_position": "Yea",
    },
    {
        "issue": "Regulate CO2 as a pollutant",
        "keywords": ["carbon", "co2", "greenhouse gas", "emissions regulation"],
        "support_means_yea": True,
        "topic": "Climate",
        "policy_areas": ["Environmental Protection", "Energy"],
        "pa_keywords": ["emission", "carbon", "climate", "pollution", "clean air", "greenhouse", "fossil"],
        "d_position": "Yea",
    },
    {
        "issue": "Require minimum renewable fuel production",
        "keywords": ["renewable fuel", "renewable energy standard", "clean energy"],
        "support_means_yea": True,
        "topic": "Climate",
        "policy_areas": ["Energy", "Environmental Protection"],
        "pa_keywords": ["renewable", "clean energy", "solar", "wind", "fuel standard", "energy credit", "green energy"],
        "d_position": "Yea",
    },
    {
        "issue": "Grant legal status to DACA recipients",
        "keywords": ["daca", "dreamer", "deferred action"],
        "support_means_yea": True,
        "topic": "Immigration",
        "policy_areas": ["Immigration"],
        "pa_keywords": ["daca", "dreamer", "deferred action", "legal status", "undocumented", "pathway to citizenship"],
        "d_position": "Yea",
    },
    {
        "issue": "Build a wall on the U.S.-Mexico border",
        "keywords": ["border wall", "border barrier"],
        "support_means_yea": True,
        "topic": "Immigration",
        "policy_areas": ["Immigration"],
        "pa_keywords": ["border wall", "border barrier", "border fence", "border security", "border protection"],
        "d_position": "Nay",  # Dems oppose the wall
    },
    {
        "issue": "Require permits to carry concealed guns",
        "keywords": ["concealed carry", "concealed weapon"],
        "support_means_yea": False,  # support = restrict carry = Nay on carry bills
        "topic": "Gun Control",
        "d_position": "Nay",  # Dems vote Nay on expanding carry rights
    },
]

# Procedural question types to skip (same as ElectorateSection.tsx)
# Keywords indicating the bill inverts the expected position.
# e.g., "Born-Alive Abortion Survivors Protection Act" — voting Nay is
# the pro-choice position, so matching on "abortion" would be backwards.
INVERSION_KEYWORDS = [
    "repeal", "rescind", "disapprov", "terminat", "eliminat",
    "prohibit", "block", "defund", "restrict", "ban on",
    "strike the", "nullif", "born-alive", "survivors protection",
    "pain-capable", "unborn child",
]

PROCEDURAL_QUESTIONS = [
    "motion to table",
    "motion to recommit",
    "motion to commit",
    "motion to adjourn",
    "motion to discharge",
    "motion to reconsider",
    "motion to refer",
    "motion to instruct",
    "providing for consideration",
    "ordering the previous",
    "point of order",
    "cloture",
    "motion to proceed",
]


def is_procedural_question(question):
    """Check if the vote question is procedural (should be skipped)."""
    q = (question or "").lower()
    for pq in PROCEDURAL_QUESTIONS:
        if pq in q:
            # Exception: "motion to suspend the rules and pass" is substantive
            if "suspend the rules" in q:
                return False
            return True
    return False


def is_inverted(description):
    """Check if vote description suggests the bill inverts expected positions.

    Detects double-negatives (e.g., "repeal amendments that terminate clean
    energy credits") where two inversion keywords cancel each other out.
    """
    desc_lower = (description or "").lower()
    triggers = [kw for kw in INVERSION_KEYWORDS if kw in desc_lower]
    if not triggers:
        return False

    # Double-negative: two independent inversion signals cancel out.
    # e.g., "repeal" + "terminat" = repealing a termination = net positive
    # Only count pairs where both words are actual inversions of each other
    # (not compound concepts like "born-alive" + "survivors protection").
    REVERSAL_WORDS = {"repeal", "rescind", "strike the", "nullif"}
    NEGATIVE_WORDS = {"terminat", "eliminat", "restrict", "prohibit", "block", "defund", "ban on"}
    has_reversal = any(kw in desc_lower for kw in REVERSAL_WORDS)
    has_negative = any(kw in desc_lower for kw in NEGATIVE_WORDS)
    if has_reversal and has_negative:
        return False  # Double-negative cancels out

    return True


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

        party_by_icpsr = {}
        with open(members_path) as f:
            for row in csv.DictReader(f):
                try:
                    icpsr = int(float(row["icpsr"]))
                except (ValueError, TypeError):
                    continue
                party_by_icpsr[icpsr] = row.get("party_code", "")

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


def find_member_position(issue_mapping, votes, bill_subjects=None, party_splits=None):
    """
    Search a member's vote records for a vote matching the issue.
    Returns ("Yea", vote_desc) or ("Nay", vote_desc) or (None, None).

    If the bill's description contains inversion keywords (e.g., "repeal",
    "prohibit"), the position is flipped so that scoring remains correct.
    For example, voting Nay on "Born-Alive Abortion Survivors Protection Act"
    is treated as a pro-choice Yea for the "Abortion should always be legal" issue.

    Tries keyword matching first, then policy_area matching with party-line
    context as fallback.
    """
    if not votes:
        return None, None

    keywords = issue_mapping["keywords"]
    policy_areas = issue_mapping.get("policy_areas", [])

    # Pass 1: keyword matching (high precision)
    for vote in votes:
        if is_procedural_question(vote.get("question", "")):
            continue
        position = vote.get("position")
        if position not in ("Yea", "Nay"):
            continue

        desc = (vote.get("description") or "").lower()
        bill = (vote.get("bill") or "").lower()
        combined = f"{desc} {bill}"

        if any(kw in combined for kw in keywords):
            # If the bill inverts the issue, flip the position
            if not issue_mapping.get("skip_inversion") and is_inverted(vote.get("description", "")):
                position = "Nay" if position == "Yea" else "Yea"
            return position, vote.get("description", "")

    # Pass 2: policy_area matching with party-line context
    # Policy areas are broad (e.g., "Health" could be pro- or anti-ACA), so we
    # use party-line splits to determine directionality. Only count votes with
    # a strong party-line split (>60% gap) where one party voted >80% Yea.
    if not bill_subjects or not party_splits or not policy_areas:
        return None, None

    d_position = issue_mapping.get("d_position")
    if not d_position:
        return None, None

    for vote in votes:
        if is_procedural_question(vote.get("question", "")):
            continue
        position = vote.get("position")
        if position not in ("Yea", "Nay"):
            continue

        bill_str = (vote.get("bill") or "").strip()
        policy_area = bill_subjects.get(bill_str)
        if not policy_area or policy_area not in policy_areas:
            continue

        # Require a topic-confirmation keyword in the description to avoid
        # false matches (e.g., a "Crime" bill about reentry, not guns).
        pa_keywords = issue_mapping.get("pa_keywords", [])
        if pa_keywords:
            desc_lower = (vote.get("description") or "").lower()
            if not any(pk in desc_lower for pk in pa_keywords):
                continue

        # Look up party-line split for this vote
        congress = vote.get("congress", 119)
        roll_number = vote.get("roll_number")
        if not roll_number:
            continue
        split = party_splits.get((congress, roll_number))
        if not split:
            continue

        d_yea = split.get("D_yea", 0)
        d_nay = split.get("D_nay", 0)
        r_yea = split.get("R_yea", 0)
        r_nay = split.get("R_nay", 0)
        d_total = d_yea + d_nay
        r_total = r_yea + r_nay

        if d_total < 10 or r_total < 10:
            continue

        d_yea_pct = d_yea / d_total
        r_yea_pct = r_yea / r_total

        # Require strong party-line split (>60% gap)
        if abs(d_yea_pct - r_yea_pct) <= 0.6:
            continue

        # Determine bill ownership
        bill_party = "R" if r_yea_pct > 0.8 else ("D" if d_yea_pct > 0.8 else None)
        if not bill_party:
            continue

        # Determine if voting Yea on this bill = supporting the issue.
        # If D-authored bill and D normally votes Yea on this issue → Yea = support
        # If R-authored bill and D normally votes Yea on this issue → Yea = oppose
        bill_aligns_with_issue = (
            (bill_party == "D" and d_position == "Yea") or
            (bill_party == "R" and d_position == "Nay")
        )

        effective_position = position
        if not bill_aligns_with_issue:
            # Bill opposes the issue direction, flip the position
            effective_position = "Nay" if position == "Yea" else "Yea"

        return effective_position, vote.get("description", "")

    return None, None


def is_aligned(position, support_pct, support_means_yea):
    """
    Determine if the member's vote aligns with the district majority.
    """
    majority_supports = support_pct > 50
    voted_yea = position == "Yea"

    if support_means_yea:
        return majority_supports == voted_yea
    else:
        # Support means Nay (e.g., "require permits" — supporting = restricting)
        return majority_supports != voted_yea


def load_bill_subjects():
    """Load cached bill subjects from Congress.gov API (created by script 05)."""
    all_subjects = {}
    for congress in [114, 115, 116, 117, 118, 119]:
        cache_path = os.path.join(CACHE_DIR, f"bill_subjects_{congress}.json")
        if os.path.exists(cache_path):
            with open(cache_path) as f:
                all_subjects.update(json.load(f))
    return all_subjects


def score_member(member, district_data, votes_data, bill_subjects, party_splits=None):
    """Score electorate alignment for a single member."""
    votes = votes_data.get("recent_votes", [])
    issues = district_data.get("issues", [])

    highlights = []
    aligned_count = 0
    scored_count = 0

    for district_issue in issues:
        issue_label = district_issue["issue"]
        support_pct = district_issue["support_pct"]
        margin = district_issue.get("margin_of_error", 7)

        # Find the matching issue mapping
        mapping = None
        for m in ISSUE_VOTE_MAP:
            if m["issue"] == issue_label:
                mapping = m
                break

        if not mapping:
            continue

        position, vote_desc = find_member_position(mapping, votes, bill_subjects, party_splits)
        if not position:
            continue

        aligned = is_aligned(position, support_pct, mapping["support_means_yea"])
        scored_count += 1
        if aligned:
            aligned_count += 1

        highlights.append({
            "issue": issue_label,
            "district_support_pct": support_pct,
            "margin_of_error": margin,
            "member_position": f"Voted {position}",
            "aligned_with_electorate": aligned,
            "aligned_with_donors": False,
        })

    against_pct = round((scored_count - aligned_count) / scored_count * 100) if scored_count > 0 else 0

    return {
        "issues_scored": scored_count,
        "against_electorate_pct": against_pct,
        "highlights": highlights,
        "against_electorate_with_donors": [],
        "source": "mrp-ces",
    }


def main():
    load_dotenv()
    print("Scoring electorate alignment...")

    # Load members
    members_path = os.path.join(RAW_DIR, "members.json")
    if not os.path.exists(members_path):
        print("ERROR: No members.json. Run 01_fetch_members.py first.")
        sys.exit(1)
    with open(members_path) as f:
        members = json.load(f)

    # Load cached bill subjects
    bill_subjects = load_bill_subjects()
    print(f"  Loaded {len(bill_subjects)} bill subjects from cache")

    # Load party-line splits for directionality on policy_area matches
    congresses = [114, 115, 116, 117, 118, 119]
    print(f"  Loading party-line vote data for congresses {congresses}...")
    house_splits = load_party_splits("house", congresses)
    senate_splits = load_party_splits("senate", congresses)
    print(f"  House: {len(house_splits)} votes, Senate: {len(senate_splits)} votes")

    # Pre-compute state-level averages for senators by averaging all
    # district files in the state (districts are roughly equal population).
    state_opinion_cache = {}

    def get_state_opinion(state):
        if state in state_opinion_cache:
            return state_opinion_cache[state]

        import glob
        pattern = os.path.join(DISTRICTS_DIR, f"{state}-*.json")
        files = sorted(glob.glob(pattern))
        if not files:
            state_opinion_cache[state] = None
            return None

        # Collect all issues across districts, average support_pct
        issue_totals = {}  # issue_label -> {sum, count, topic, margin}
        for fp in files:
            with open(fp) as f:
                dd = json.load(f)
            for issue in dd.get("issues", []):
                label = issue["issue"]
                if label not in issue_totals:
                    issue_totals[label] = {
                        "sum": 0, "count": 0,
                        "topic": issue.get("topic", ""),
                        "margin": issue.get("margin_of_error", 7),
                    }
                issue_totals[label]["sum"] += issue["support_pct"]
                issue_totals[label]["count"] += 1

        issues = []
        for label, data in issue_totals.items():
            issues.append({
                "issue": label,
                "topic": data["topic"],
                "support_pct": round(data["sum"] / data["count"], 1),
                "margin_of_error": data["margin"],
            })

        result = {"district": state, "issues": issues}
        state_opinion_cache[state] = result
        return result

    results = {}
    scored_count = 0
    total_issues = 0

    for member in members:
        bio_id = member["bioguide_id"]
        state = member["state"]
        district = member.get("district")
        chamber = member["chamber"]

        empty_result = {
            "issues_scored": 0, "against_electorate_pct": 0,
            "highlights": [], "against_electorate_with_donors": [],
            "source": "mrp-ces",
        }

        # Load district opinion data
        district_data = None
        if chamber == "house" and district:
            district_code = f"{state}-{district.zfill(2)}"
            district_path = os.path.join(DISTRICTS_DIR, f"{district_code}.json")
            if os.path.exists(district_path):
                with open(district_path) as f:
                    district_data = json.load(f)
        elif chamber == "senate":
            # Average all districts in the state
            district_data = get_state_opinion(state)

        if not district_data:
            results[bio_id] = empty_result
            continue

        # Load member votes
        votes_path = os.path.join(PUBLIC_MEMBERS_DIR, f"{bio_id}_votes.json")
        if not os.path.exists(votes_path):
            results[bio_id] = {
                "issues_scored": 0, "against_electorate_pct": 0,
                "highlights": [], "against_electorate_with_donors": [],
                "source": "mrp-ces",
            }
            continue

        with open(votes_path) as f:
            votes_data = json.load(f)

        splits = house_splits if chamber == "house" else senate_splits
        alignment = score_member(member, district_data, votes_data, bill_subjects, splits)
        results[bio_id] = alignment

        if alignment["issues_scored"] > 0:
            scored_count += 1
            total_issues += alignment["issues_scored"]

    # Save
    os.makedirs(RAW_DIR, exist_ok=True)
    out_path = os.path.join(RAW_DIR, "electorate_alignment.json")
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2)

    avg_issues = round(total_issues / scored_count, 1) if scored_count > 0 else 0
    print(f"  Scored {scored_count}/{len(results)} members with electorate data")
    print(f"  Average issues scored per member: {avg_issues}")

    # Also patch member JSONs directly
    patched = 0
    for bio_id, alignment in results.items():
        member_path = os.path.join(PUBLIC_MEMBERS_DIR, f"{bio_id}.json")
        if not os.path.exists(member_path):
            continue
        with open(member_path) as f:
            member_data = json.load(f)
        member_data["electorate_alignment"] = alignment
        with open(member_path, "w") as f:
            json.dump(member_data, f, indent=2)
        patched += 1

    print(f"  Patched {patched} member JSON files")

    # Show test results
    for test_id in ["P000197", "S001150", "P000145"]:
        a = results.get(test_id, {})
        name = "?"
        mp = os.path.join(PUBLIC_MEMBERS_DIR, f"{test_id}.json")
        if os.path.exists(mp):
            with open(mp) as f:
                name = json.load(f).get("name", "?")
        print(f"\n  {name} ({test_id}): {a.get('issues_scored', 0)} issues scored, "
              f"{a.get('against_electorate_pct', 0)}% against district")
        for h in a.get("highlights", []):
            tag = "ALIGNED" if h["aligned_with_electorate"] else "AGAINST"
            print(f"    [{tag}] {h['issue'][:50]} | District: {h['district_support_pct']}% | Rep: {h['member_position']}")


if __name__ == "__main__":
    main()
