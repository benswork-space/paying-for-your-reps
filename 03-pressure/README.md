# Pressure — Coordinated Action Campaigns

## Concept
Go beyond sending a letter into the void. Show users that 400 people in their district sent the same letter this week. Track whether the rep responded. Escalate collectively (letter → call campaign → showing up). Gamified collective pressure with a visible scoreboard.

## Why This Matters
- Individual action feels futile; visible collective action sustains momentum
- Congressional staff say volume matters, but constituents never see the volume
- Bridges the gap between individual frustration and collective power

## Key Features
- Campaign creation around specific issues/bills
- One-tap actions (pre-written letters, call scripts)
- Real-time counters: "N people in [district] contacted [rep] about [issue] this week"
- Rep response tracking (did they reply? how? what did they say?)
- Escalation mechanics (thresholds that trigger next-level actions)
- District-level leaderboards and progress bars

## Data Sources
- **Contact volume** — must be built from scratch (see Research Findings below)
- **Representative contact info** — from project 02 (Represent) or Cicero API (~3¢/lookup)
- **Bill/issue data** — Congress.gov API, LegiScan

## Research Findings: Contact Volume Data

### The bad news: No external data source exists
- **Resistbot** has no public API and explicitly does not share user data. ~50M letters sent since 2017, but no per-rep or per-district breakdown is published. Their GitHub repos are internal tooling only.
- **Quorum/Capitol Canary (Phone2Action)** has APIs but they're B2B SaaS — each client sees only their own campaign data, not cross-platform aggregates.
- **Fireside21** (dominant congressional office CRM) reports aggregate stats (~81M inbound messages in 2022) but no per-office breakdowns. Congress is exempt from FOIA, so this data can't be requested.
- **VoterVoice** publishes annual advocacy benchmark reports, but data is aggregated/anonymized.
- **5 Calls** asks users to self-report calls, but this is honor system.

### The interesting development: Case Compass
POPVOX Foundation + House Digital Services are building **Case Compass** — a dashboard for anonymized, aggregate constituent casework data across participating congressional offices. As of Sept 2025, they released a unified data schema. House-only, focused on casework (not advocacy campaigns), but it's the first cross-office data-sharing effort.

### What this means for Pressure
The counter data must come from our own users. This creates a chicken-and-egg problem but also a moat. Strategies to bootstrap:
1. **Partner with existing orgs** (Indivisible, MoveOn, local advocacy groups) who already coordinate campaigns
2. **Start with a single high-profile issue** to build initial critical mass
3. **Open-source the counter infrastructure** so other tools can contribute data
4. **Use Resistbot's `contact-officials` GitHub repo** (form definitions for electronic delivery) as a starting point for the contact mechanism

### Relevant open-source tools
- **CiviCRM / PowerBase** — open-source CRM for nonprofits/advocacy, could serve as backend
- **Resistbot's `contact-officials` repo** — form definitions for delivering messages to officials

## Open Questions
- Can we partner with Resistbot, Indivisible, or similar orgs for bootstrapping?
- Honor system vs. delivery confirmation for verifying contacts were made?
- How to prevent astroturfing / bot abuse of the counters?
- Could Case Compass eventually become a data source if it expands?

## Status
Priority #3 — Concept phase. Core insight: this must be a platform play, not a data aggregation play.
