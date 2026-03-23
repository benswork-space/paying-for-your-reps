# Civic Receipts — Follow the Money to Your Door

## Concept
Enter your zip code. See which corporations and PACs fund your specific representatives, how those reps voted on issues you care about, and the exposed correlation between money and votes. Think "Spotify Wrapped" for political money — shareable, visual, personal.

## Why This Matters
- Makes corruption legible at a personal, local level
- Gives citizens a concrete artifact ("receipt") they can reference and share
- Bridges the gap between raw campaign finance data and citizen understanding

## Key Features
- Zip code → representative lookup
- Per-representative donor breakdown (top industries, top PACs, top individual donors)
- Voting record on key issues, cross-referenced with donor interests
- Shareable visual cards for social media ("Your rep received $X from industry Y and voted Z on bill W")
- "N people in your district also looked this up" — social proof / connection

## Data Sources
- **FEC API** — campaign contributions, PAC spending, independent expenditures
- **Congress.gov API** — voting records, bill text, sponsor/cosponsor data
- **OpenSecrets bulk data** — pre-processed money-in-politics data, industry coding
- **LegiScan** — state-level legislation and votes (50 states)
- **Representative lookup** — will need to solve the "who represents me" problem (see project 05)

## Open Questions
- How to present correlations responsibly (correlation ≠ causation, but patterns matter)
- State-level data availability varies widely
- How to keep data fresh (FEC data has reporting lag)
- Nonpartisan framing to maximize reach

## Status
Priority #1 — Active development starting soon.
