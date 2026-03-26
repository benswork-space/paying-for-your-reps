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

import json
import os
import sys

RAW_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "raw")
PUBLIC_DIR = os.path.join(os.path.dirname(__file__), "..", "public", "data")
PUBLIC_MEMBERS_DIR = os.path.join(PUBLIC_DIR, "members")
DISTRICTS_DIR = os.path.join(PUBLIC_DIR, "districts")
CACHE_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "scripts", ".cache")
LLM_ELECTORATE_DIR = os.path.join(CACHE_DIR, "llm_electorate_positions")
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


# ── Issue → Vote mapping ──────────────────────────────────────────────
# Each entry maps a district opinion issue to its cache file key.
# Industry position preferences on specific bills are determined by
# pre-computed LLM classifications stored in LLM_ELECTORATE_DIR.
ISSUE_VOTE_MAP = [
    {
        "issue": "Universal background checks for gun purchases",
        "cache_key": "background_checks",
        "support_means_yea": True,
        "topic": "Gun Control",
    },
    {
        "issue": "Ban on assault-style weapons",
        "cache_key": "assault_weapons_ban",
        "support_means_yea": True,
        "topic": "Gun Control",
    },
    {
        "issue": "Abortion should always be legal",
        "cache_key": "abortion_legal",
        "support_means_yea": True,
        "topic": "Abortion",
    },
    {
        "issue": "Prohibit all abortions after 20 weeks",
        "cache_key": "abortion_20_weeks",
        "support_means_yea": True,
        "topic": "Abortion",
    },
    {
        "issue": "Support the Affordable Care Act",
        "cache_key": "support_aca",
        "support_means_yea": True,
        "topic": "Healthcare",
    },
    {
        "issue": "Regulate CO2 as a pollutant",
        "cache_key": "regulate_co2",
        "support_means_yea": True,
        "topic": "Climate",
    },
    {
        "issue": "Require minimum renewable fuel production",
        "cache_key": "renewable_fuel",
        "support_means_yea": True,
        "topic": "Climate",
    },
    {
        "issue": "Grant legal status to DACA recipients",
        "cache_key": "daca",
        "support_means_yea": True,
        "topic": "Immigration",
    },
    {
        "issue": "Build a wall on the U.S.-Mexico border",
        "cache_key": "border_wall",
        "support_means_yea": True,
        "topic": "Immigration",
    },
    {
        "issue": "Require permits to carry concealed guns",
        "cache_key": "concealed_carry",
        "support_means_yea": False,  # support = restrict carry = Nay on carry bills
        "topic": "Gun Control",
    },
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


def is_description_too_vague(description):
    """
    Check if a bill description is too vague to reliably classify.
    Short or generic titles like "Breaking the Gridlock Act" don't give
    enough information to confidently determine issue relevance.
    """
    desc = (description or "").strip()
    if len(desc) < 15:
        return True
    clean = desc.lower().strip()
    if clean in ("", "none", "n/a"):
        return True
    if len(desc.split()) <= 4 and "appropriation" not in clean:
        return True
    return False


def load_llm_electorate_positions():
    """
    Load pre-computed LLM classifications of bill positions per electorate issue.
    Returns dict: cache_key -> {bill_number: {yea_means_support, confidence, reason}}
    """
    positions = {}
    if not os.path.exists(LLM_ELECTORATE_DIR):
        print(f"  WARNING: LLM electorate positions directory not found: {LLM_ELECTORATE_DIR}")
        print("  Run the classification agent first to generate issue position data.")
        return positions

    for filename in os.listdir(LLM_ELECTORATE_DIR):
        if filename.startswith("_") or not filename.endswith(".json"):
            continue
        cache_key = filename.replace(".json", "")
        filepath = os.path.join(LLM_ELECTORATE_DIR, filename)
        with open(filepath) as f:
            positions[cache_key] = json.load(f)

    return positions


def find_member_position(issue_mapping, votes, llm_positions=None):
    """
    Search a member's vote records for a vote matching the issue using
    pre-computed LLM classifications.
    Returns ("Yea", vote_desc) or ("Nay", vote_desc) or (None, None).

    The LLM cache tells us which bills are relevant and whether Yea = support.
    We then translate the member's actual vote into an effective position
    relative to the issue (support = Yea, oppose = Nay).
    """
    if not votes or not llm_positions:
        return None, None

    cache_key = issue_mapping.get("cache_key")
    if not cache_key:
        return None, None

    issue_positions = llm_positions.get(cache_key, {})
    if not issue_positions:
        return None, None

    # Find the best matching vote: highest confidence, prefer "On Passage",
    # prefer most recent congress. Votes are already ordered by date (newest first).
    PASSAGE_QUESTIONS = {"On Passage", "On the Conference Report", "On the Joint Resolution",
                         "On the Concurrent Resolution", "On the Resolution"}

    best = None
    best_score = (-1, -1, 0)  # (is_passage, congress, confidence)

    for vote in votes:
        if is_procedural_question(vote.get("question", "")):
            continue
        position = vote.get("position")
        if position not in ("Yea", "Nay"):
            continue

        bill_str = (vote.get("bill") or "").strip()
        if not bill_str:
            continue

        # Skip bills with vague descriptions
        if is_description_too_vague(vote.get("description", "")):
            continue

        bill_info = issue_positions.get(bill_str)
        if not bill_info:
            continue

        confidence = bill_info.get("confidence", 0)
        if confidence < 0.6:
            continue

        question = vote.get("question", "")
        is_passage = 1 if question in PASSAGE_QUESTIONS else 0
        congress = vote.get("congress", 0)
        score = (is_passage, congress, confidence)

        if score > best_score:
            yea_means_support = bill_info.get("yea_means_support", True)

            # Translate actual vote to effective position relative to the issue
            if yea_means_support:
                effective_position = position
            else:
                effective_position = "Nay" if position == "Yea" else "Yea"

            best = (effective_position, vote.get("description", ""))
            best_score = score

    if best:
        return best
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


def score_member(member, district_data, votes_data, llm_positions=None):
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

        position, vote_desc = find_member_position(mapping, votes, llm_positions)
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

    # Load pre-computed LLM classifications
    print("  Loading LLM electorate issue classifications...")
    llm_positions = load_llm_electorate_positions()
    if not llm_positions:
        print("  ERROR: No LLM electorate position data found. Run classification agent first.")
        sys.exit(1)
    total_classified = sum(len(v) for v in llm_positions.values())
    print(f"  Loaded {len(llm_positions)} issues, {total_classified} total bill classifications")

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

        alignment = score_member(member, district_data, votes_data, llm_positions)
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
