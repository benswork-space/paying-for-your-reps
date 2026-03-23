# Represent — The Missing Civic Data Layer

## Concept
An open-source, free API and database mapping every elected official at every level of government (federal → state → county → city → school board) to every address in the US. The Google Civic Information API died in April 2025. Nobody has replaced it. This becomes infrastructure that every other civic tech tool depends on.

## Why This Matters
- Every civic app needs "who represents me?" and there's no free answer anymore
- The death of Google's API left a hole in the entire civic tech ecosystem
- Commercial alternatives (Cicero, BallotReady) are expensive and proprietary
- The people most harmed are small civic tech projects and activists who can't afford $300+/yr — exactly the constituency least able to fund an alternative
- This is a public good that should exist as open infrastructure

## Key Features
- Address → all elected officials at every level
- District boundary data (federal, state, local)
- Official contact information, social media, office locations
- Open API with generous rate limits
- Crowdsourced data correction and verification
- Bulk data downloads for researchers and other tools

## Data Sources
- **Census TIGER/Line files** — congressional and state legislative district boundaries
- **State Secretaries of State** — state-level official data
- **Plural Open / Open States API (free)** — state legislator data for all 50 states + DC + PR
- **Municipal websites** — city/county official data (scraping + crowdsourcing)
- **Redistricting Data Hub** — district boundary shapefiles, local redistricting data
- **Google Divisions API (still alive)** — returns OCD-ID district identifiers by address, but NOT official names/contact info. Could be used as a bridge.
- **Geocod.io** — free tier for geocoding + federal/state district matching

## What Google's API Aggregated (and why it's hard to replicate)
Google combined data from:
- **Voting Information Project (VIP)** — run by Democracy Works, partnership between state election officials and foundations
- **Open Civic Data (OCD) identifiers** — normalized political divisions across the entire US hierarchy
- **Multiple third-party and official sources** — with a priority system serving the highest-quality source available
- **Google's own geocoding infrastructure** — address → lat/long → point-in-polygon against overlapping districts

The key: Google subsidized this as a free public good. The data collection, boundary matching, geocoding, and maintenance were expensive but absorbed by Google.

## Why Nobody Has Rebuilt This

### CTCL was the best hope — and chose not to
The Center for Tech and Civic Life had been building the **Governance Project**, a comprehensive database. They decided **not to stand up an API**. This is documented in [datamade/my-reps issue #35](https://github.com/datamade/my-reps/issues/35).

### The structural problems
1. **89,000+ local governments** with no standardized data. Boundaries may be shapefiles, PDFs, JPGs, or "in a local official's head."
2. **BallotReady needed 10,000+ unique shapefiles** not available from the Census Bureau for downballot positions.
3. **Precinct boundaries are frequently deleted** by local authorities after elections — they're snapshots, not permanent records.
4. **Ongoing maintenance is labor-intensive** — officials resign, are appointed, die, or are recalled between elections. Contact info changes constantly.
5. **The economics don't work for volunteers** — this requires paid staff, not weekend hackathons.
6. **Commercial providers fill the gap for funded orgs** — removing urgency for a free alternative.

## What Organizations Use Now
| Provider | Pricing | Coverage | Notes |
|----------|---------|----------|-------|
| **Cicero (Melissa Data)** | ~3-4¢/lookup, ~$298/yr for 10K credits | 10,000+ US officials, daily updates | Most common Google API replacement |
| **BallotReady (Civitech)** | Quote-based (expensive) | Most comprehensive local coverage | Has 10,000+ unique shapefiles |
| **Ballotpedia** | Quote-based (annual subscription) | Federal + statewide + growing local | Free end-user tool, paid API |
| **USgeocoder** | "A bit more expensive than Google" | Unknown | |
| **Plural Open (Open States)** | Free | State legislators only | Does NOT cover local |
| **Geocod.io** | Free tier available | Geocoding + federal/state districts | No official data |

**The common 2025-2026 pattern:** Two-step process — Geocod.io or Google Divisions API for district matching, then BallotReady/Cicero/Ballotpedia for official data. More expensive and complex than Google's single API call.

## Existing Open-Source Attempts
- **FindOurReps** ([github.com/KatahGii/FindOurReps](https://github.com/KatahGii/FindOurReps)) — open-source with its own dataset for federal/state reps. Appears early stage.
- **DataMade's My Reps** — popular frontend, stopped working when Google API died. Codebase available for reuse.
- **Alliance of Civic Technologists** — no representative lookup API produced.

## Strategic Questions
- **Sustainability model:** Grants? Nonprofit? Foundation support? Community-maintained?
- **Scope:** Start federal+state (achievable) then expand to local (hard)? Or go wide from day one?
- **Could we partner with or build on CTCL's Governance Project data?** They chose not to build an API — would they share data with someone who would?
- **Democracy Works partnership?** They still operate VIP and partner with Google on remaining APIs.

## Status
Priority #2 — Research phase complete. Also serves as enabling infrastructure for project 01 (Civic Receipts).
