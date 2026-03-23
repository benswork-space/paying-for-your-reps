#!/usr/bin/env python3
"""
Generate per-member JSON files and the ZIP lookup file for the app.

Combines data from all previous pipeline steps into the final format
expected by the Next.js app.

Outputs:
  - public/data/members/{bioguide_id}.json (one per member)
  - public/data/zip_lookup.json
"""

import json
import os
import shutil
import sys

RAW_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "raw")
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "output")
PUBLIC_DIR = os.path.join(os.path.dirname(__file__), "..", "public", "data")


def load_json(path, label="data"):
    if not os.path.exists(path):
        print(f"  Note: {label} not found at {path}")
        return {}
    with open(path) as f:
        return json.load(f)


def slugify_name(name):
    """Convert name to URL-friendly slug for OpenSecrets link."""
    return name.lower().replace(" ", "-").replace(".", "").replace("'", "")


def build_funding_from_fec(fec_data):
    """Build the full funding structure from an FEC sidecar file."""
    totals = fec_data.get("totals", {})
    cycle = str(fec_data.get("cycle", "2024"))
    campaign_pac_contributors = fec_data.get("campaign_pac_contributors", [])
    campaign_top_employers = fec_data.get("campaign_top_employers", [])
    leadership_pacs = fec_data.get("leadership_pacs", [])

    # Use committee_ids (new format) or fall back to committee_id (old format)
    committee_ids = fec_data.get("fec_committee_ids", [])
    if not committee_ids:
        cid = fec_data.get("fec_committee_id")
        committee_ids = [cid] if cid else []

    # Campaign committee detail
    campaign = {
        "committee_id": committee_ids[0] if committee_ids else "",
        "total_raised": totals.get("total_raised", 0),
        "individual_contributions": totals.get("individual_contributions", 0),
        "individual_itemized": totals.get("individual_itemized", 0),
        "individual_unitemized": totals.get("individual_unitemized", 0),
        "pac_contributions": totals.get("pac_contributions", 0),
        "other_receipts": totals.get("other_receipts", 0),
        "top_employers": [
            {"name": e["name"], "type": "Organization", "amount": e["total"]}
            for e in campaign_top_employers
        ],
        "top_pac_donors": [
            {"name": c["name"], "type": "PAC", "amount": int(c["total"])}
            for c in campaign_pac_contributors
        ],
    }

    # Leadership PAC details
    leadership_pac_data = []
    for lp in leadership_pacs:
        leadership_pac_data.append({
            "committee_id": lp["committee_id"],
            "name": lp["name"],
            "total_raised": lp.get("receipts", 0),
            "top_employers": [
                {"name": e["name"], "type": "Organization", "amount": e["total"]}
                for e in lp.get("top_employers", [])
            ],
            "top_pac_donors": [
                {"name": c["name"], "type": "PAC", "amount": int(c["total"])}
                for c in lp.get("contributors", [])
            ],
        })

    leadership_total = sum(lp.get("receipts", 0) for lp in leadership_pacs)
    combined_total = totals.get("total_raised", 0) + leadership_total

    # Build top_industries
    all_employers = {}
    for e in campaign_top_employers:
        all_employers[e["name"]] = all_employers.get(e["name"], 0) + e["total"]
    for lp in leadership_pacs:
        for e in lp.get("top_employers", []):
            all_employers[e["name"]] = all_employers.get(e["name"], 0) + e["total"]
    sorted_employers = sorted(all_employers.items(), key=lambda x: -x[1])[:15]

    all_pac_donors = {}
    for c in campaign_pac_contributors:
        all_pac_donors[c["name"]] = all_pac_donors.get(c["name"], 0) + int(c["total"])
    for lp in leadership_pacs:
        for c in lp.get("contributors", []):
            all_pac_donors[c["name"]] = all_pac_donors.get(c["name"], 0) + int(c["total"])
    sorted_pac_donors = sorted(all_pac_donors.items(), key=lambda x: -x[1])[:15]

    top_industries = []
    individual_total = totals.get("individual_contributions", 0)
    pac_total = totals.get("pac_contributions", 0)

    if individual_total > 0:
        top_industries.append({
            "code": "IND",
            "name": "Individual Contributions",
            "amount": individual_total,
            "donors": [{"name": n, "type": "Organization", "amount": a} for n, a in sorted_employers],
        })

    if pac_total > 0 or leadership_total > 0:
        top_industries.append({
            "code": "PAC",
            "name": "PAC & Committee Contributions",
            "amount": pac_total,
            "donors": [{"name": n, "type": "PAC", "amount": a} for n, a in sorted_pac_donors],
        })

    if leadership_total > 0:
        top_industries.append({
            "code": "LPAC",
            "name": "Leadership PAC",
            "amount": leadership_total,
            "donors": [{"name": n, "type": "PAC", "amount": a} for n, a in sorted_pac_donors],
            "details": leadership_pac_data,
        })

    return {
        "cycle": cycle,
        "total_raised": combined_total,
        "campaign_raised": totals.get("total_raised", 0),
        "leadership_pac_raised": leadership_total,
        "top_industries": top_industries,
        "campaign": campaign,
        "leadership_pacs": leadership_pac_data,
    }


def build_funding_from_finance(fin):
    """Build a basic funding structure from the legacy finance.json data."""
    top_industries = fin.get("top_industries", [])
    top_contribs = fin.get("top_contributors", [])
    for industry in top_industries:
        if not industry.get("donors"):
            industry["donors"] = top_contribs[:5] if top_contribs else []

    return {
        "cycle": fin.get("cycle", "2024"),
        "total_raised": fin.get("total_raised", 0),
        "top_industries": [
            {
                "code": ind.get("code", ""),
                "name": ind.get("name", "Unknown"),
                "amount": ind.get("amount", 0),
                "donors": [
                    {
                        "name": d.get("name", ""),
                        "type": d.get("type", "PAC"),
                        "amount": d.get("amount", 0),
                    }
                    for d in ind.get("donors", [])[:8]
                ],
            }
            for ind in top_industries[:6]
        ],
    }


def generate_member_json(member, finance, fec_data_map, donor_alignment, electorate_alignment):
    """Generate the full member JSON matching the app's MemberData type."""
    bio_id = member["bioguide_id"]
    opensecrets_id = member.get("opensecrets_id", "")

    # Prefer FEC sidecar data over legacy finance.json
    if bio_id in fec_data_map:
        funding = build_funding_from_fec(fec_data_map[bio_id])
    else:
        fin = finance.get(bio_id, {})
        funding = build_funding_from_finance(fin)

    # Donor alignment
    da = donor_alignment.get(bio_id, {})
    donor_align = {
        "overall_pct": da.get("overall_pct", 0),
        "total_votes_scored": da.get("total_votes_scored", 0),
        "methodology_url": "/methodology#donor-alignment",
        "examples": da.get("examples", []),
    }

    # Electorate alignment
    ea = electorate_alignment.get(bio_id, {})
    electorate_align = {
        "issues_scored": ea.get("issues_scored", 0),
        "against_electorate_pct": ea.get("against_electorate_pct", 0),
        "highlights": ea.get("highlights", []),
        "against_electorate_with_donors": ea.get("against_electorate_with_donors", []),
    }

    # Links
    name_slug = slugify_name(member["name"])
    voting_record_url = f"https://www.congress.gov/member/{name_slug}/{bio_id}"
    opensecrets_url = f"https://www.opensecrets.org/members-of-congress/summary?cid={opensecrets_id}" if opensecrets_id else ""
    official_url = member.get("official_website", "")

    return {
        "bioguide_id": bio_id,
        "name": member["name"],
        "party": member["party"],
        "chamber": member["chamber"],
        "state": member["state"],
        "district": member.get("district"),
        "gender": member.get("gender"),
        "photo_url": member["photo_url"],
        "serving_since": member.get("serving_since"),
        "years_in_office": member.get("years_in_office", 0),
        "funding": funding,
        "donor_alignment": donor_align,
        "electorate_alignment": electorate_align,
        "links": {
            "voting_record": voting_record_url,
            "opensecrets": opensecrets_url,
            "official_website": official_url,
        },
    }


def main():
    print("Loading pipeline data...")

    members = load_json(os.path.join(RAW_DIR, "members.json"), "members")
    if not members:
        print("ERROR: No members data. Run 01_fetch_members.py first.")
        sys.exit(1)

    finance = load_json(os.path.join(RAW_DIR, "finance.json"), "finance")
    donor_alignment = load_json(os.path.join(RAW_DIR, "donor_alignment.json"), "donor_alignment")
    electorate_alignment = load_json(os.path.join(RAW_DIR, "electorate_alignment.json"), "electorate_alignment")

    # Load FEC sidecar files (authoritative source when available)
    members_dir = os.path.join(PUBLIC_DIR, "members")
    os.makedirs(members_dir, exist_ok=True)

    fec_data_map = {}
    fec_dir = members_dir  # sidecars live alongside member JSONs
    for fname in os.listdir(fec_dir):
        if fname.endswith("_fec.json"):
            bio_id = fname.replace("_fec.json", "")
            fec_data_map[bio_id] = load_json(os.path.join(fec_dir, fname), f"FEC {bio_id}")
    print(f"  Loaded {len(fec_data_map)} FEC sidecar files")

    # Generate per-member JSON
    print(f"Generating JSON for {len(members)} members...")
    generated = 0

    for member in members:
        bio_id = member["bioguide_id"]
        member_json = generate_member_json(
            member, finance, fec_data_map, donor_alignment, electorate_alignment
        )

        path = os.path.join(members_dir, f"{bio_id}.json")
        with open(path, "w") as f:
            json.dump(member_json, f, indent=2)

        generated += 1

    print(f"  Wrote {generated} member JSON files to {members_dir}")

    # Copy ZIP lookup to public dir
    zip_src = os.path.join(OUTPUT_DIR, "zip_districts.json")
    zip_dst = os.path.join(PUBLIC_DIR, "zip_lookup.json")

    if os.path.exists(zip_src):
        shutil.copy2(zip_src, zip_dst)
        size_mb = os.path.getsize(zip_dst) / 1024 / 1024
        print(f"  Copied ZIP lookup to {zip_dst} ({size_mb:.1f} MB)")
    else:
        print("  WARNING: zip_districts.json not found. Run 02_fetch_zip_districts.py first.")

    # Verification
    print("\nVerification:")

    test_member_path = os.path.join(members_dir, "P000197.json")
    if os.path.exists(test_member_path):
        with open(test_member_path) as f:
            test = json.load(f)
        print(f"  P000197 ({test['name']}):")
        print(f"    Party: {test['party']}, Chamber: {test['chamber']}, State: {test['state']}-{test.get('district', 'N/A')}")
        print(f"    Total raised: ${test['funding']['total_raised']:,}")
        print(f"    Top industries: {len(test['funding']['top_industries'])}")
        print(f"    Donor alignment: {test['donor_alignment']['overall_pct']}%")
        print(f"    Electorate alignment: {100 - test['electorate_alignment']['against_electorate_pct']}% with district")
    else:
        print("  WARNING: P000197.json not generated")

    # Check total size
    total_size = 0
    for f in os.listdir(members_dir):
        total_size += os.path.getsize(os.path.join(members_dir, f))
    print(f"\n  Total member data size: {total_size / 1024 / 1024:.1f} MB")


if __name__ == "__main__":
    main()
