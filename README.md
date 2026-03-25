# Paying for your Reps

Enter your zip code. See who funds your representatives, how they vote, and whether they're representing you or their donors.

## What This Does

- **Zip code lookup** — find your House and Senate representatives
- **Campaign finance breakdown** — top PAC donors, individual contributors, and industry funding for each rep's campaign committee and leadership PACs
- **Donor alignment score** — how often a rep's votes appear favorable to their top donor industries
- **District alignment score** — how often a rep votes in line with their district's public opinion on key issues
- **Notable votes** — specific examples where a rep voted with or against their donors' apparent interests

## How It Works

### Data Pipeline

The project uses a series of Python scripts (`civic-receipts/scripts/01-07`) to fetch, process, and score data:

1. **`01_fetch_members.py`** — Fetches current members of Congress from unitedstates/congress-legislators
2. **`02_fetch_zip_districts.py`** — Maps ZIP codes to congressional districts using U.S. Census ZCTA relationship files
3. **`03_fetch_finance.py`** — Pulls campaign finance data from FEC bulk filings (via OpenSecrets)
4. **`04_fetch_votes.py`** — Fetches voting records from Voteview (UCLA/MIT) across Congresses 114-119
5. **`05_score_donor_alignment.py`** — Scores how often each rep's votes align with their top donors' industry interests
6. **`06_score_electorate.py`** — Scores how often each rep's votes align with their district's public opinion
7. **`07_generate_json.py`** — Generates the final static JSON files served by the Next.js frontend

### Bill Classification (AI-Assisted)

Both the donor and district alignment scores rely on understanding what each bill actually does — not just its title (congressional bill titles are often misleading, e.g., "Do No Harm in Medicaid Act" actually cuts Medicaid).

We use AI-assisted classification (Claude) to analyze each bill and determine:
- **For donor alignment**: Which industry categories a bill is relevant to, and whether industry donors would prefer a Yea or Nay vote
- **For district alignment**: Which of 10 policy issues a bill relates to, and whether voting Yea supports or opposes that issue

Classifications are cached in `scripts/.cache/llm_donor_positions/` and `scripts/.cache/llm_electorate_positions/` as auditable JSON files. Each classification includes a confidence score and a reason explaining what the bill actually does. Bills with vague or misleading titles that can't be confidently classified are excluded.

### Donor Alignment

PAC donors are categorized into 15 industry groups (defense, healthcare, fossil fuels, labor, tech, finance, etc.) by matching PAC names against known patterns. For each bill a rep voted on, we look up the pre-classified industry position and check whether the rep's vote was favorable or unfavorable to that industry. The overall score is a weighted average across industries, weighted by donation amount.

### District Alignment

District-level public opinion is estimated using **Multilevel Regression and Poststratification (MRP)** applied to the **Cooperative Election Study (CES)** — a large-scale academic survey (Harvard/MIT, 164,000+ respondents, 2018-2021). We cover 10 policy issues across gun control, abortion, healthcare, climate, and immigration. For each issue, we compare the district's estimated opinion to how the rep actually voted on related legislation.

## Data Sources

| Source | What it provides |
|--------|-----------------|
| **FEC bulk filings** (via OpenSecrets) | Campaign contributions, PAC donors, individual donors |
| **Voteview** (UCLA/MIT) | Roll call voting records, party-line vote splits |
| **Congress.gov API** | Bill policy areas and subjects |
| **unitedstates/congress-legislators** | Member biographical data, terms, party, state/district |
| **U.S. Census Bureau** | ZIP-to-congressional-district mapping (ZCTA files) |
| **Cooperative Election Study (CES)** | District-level public opinion estimates (processed with MRP) |
| **Claude** (Anthropic) | Bill classification — determining what bills actually do and their likely impact on industries and policy issues |

## Tech Stack

- **Frontend**: Next.js 16, React, Tailwind CSS, Mapbox GL
- **Data pipeline**: Python scripts with JSON caching
- **Data format**: Static JSON files (no database, no server-side API)
- **Bill classification**: AI-assisted via Claude, cached as auditable JSON

## Development

```bash
cd civic-receipts
npm install
npm run dev
```

To re-run the data pipeline:
```bash
cd civic-receipts
python3 scripts/01_fetch_members.py
python3 scripts/04_fetch_votes.py
python3 scripts/05_score_donor_alignment.py
python3 scripts/06_score_electorate.py
```

## Limitations

- **Correlation, not causation** — a high donor alignment score doesn't prove a rep is voting because of donations
- **Industry categories are broad** — "healthcare" includes hospitals, pharma, and insurers, who may have conflicting interests on specific bills
- **District opinion data is from 2018-2021** — public opinion may have shifted since then
- **Bill classification is approximate** — AI classification is more accurate than keyword matching but not perfect; all classifications are auditable in the cache files
- **Small-dollar donors ($200 or less) are not itemized** by the FEC and don't appear in contributor lists
