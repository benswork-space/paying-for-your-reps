# Paying for your Reps — Frontend

Next.js frontend for the Paying for your Reps project. See the [root README](../README.md) for full project documentation.

## Development

```bash
npm install
npm run dev
```

## Data Pipeline

The frontend serves pre-computed static JSON from `public/data/`. To regenerate:

```bash
python3 scripts/01_fetch_members.py      # Fetch member data
python3 scripts/04_fetch_votes.py         # Fetch voting records
python3 scripts/05_score_donor_alignment.py   # Score donor alignment
python3 scripts/06_score_electorate.py        # Score district alignment
```

Bill classifications (used by scripts 05 and 06) are stored in `scripts/.cache/llm_donor_positions/` and `scripts/.cache/llm_electorate_positions/`. These are AI-generated but human-auditable JSON files.
