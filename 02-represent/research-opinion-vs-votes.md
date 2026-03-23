# Research: Public Opinion Data vs. Congressional Voting Records

## Purpose
Data sources and tools for building a civic tech feature that shows users when their representatives vote against the majority opinion of their constituents. This research covers district-level and state-level public opinion datasets, existing "representation gap" work, specific issue datasets, API/data availability, and methodological concerns.

---

## 1. District-Level and State-Level Public Opinion Datasets

### 1A. Cooperative Election Study (CES / formerly CCES)

**The single most important dataset for this project.**

- **What it is:** The largest academic survey focused on American elections. 50,000+ respondents per year since 2006. Cumulative dataset has 641,955 respondents (2006-2023). Asks about policy preferences on issues Congress has voted on, plus demographics, geography, vote choice, ideology.
- **Congressional district data:** Each respondent record includes a `cd` variable (e.g., "MI-04", "TX-18") identifying their congressional district. However, the survey is **not designed to be directly representative at the district level** — it is a national stratified sample. District-level estimates require weighting or MRP.
- **Data formats:** `.dta` (Stata), `.Rds` (R), `.feather` (Arrow). No native CSV — must convert.
- **Download:** Harvard Dataverse at https://dataverse.harvard.edu/dataverse/cces and https://cces.gov.harvard.edu/data
- **Cumulative dataset:** https://dataverse.harvard.edu/dataset.xhtml?persistentId=doi:10.7910/DVN/II2DB6
- **Cumulative policy preferences:** https://dataverse.harvard.edu/dataset.xhtml?persistentId=doi:10.7910/DVN/OSXDQO
- **Explore questions interactively:** https://cooperativeelectionstudy.shinyapps.io/ccsearch/
- **Key variables:** year, case_id, weight, state, st, cd, zipcode, county_fips, gender, age, race, plus policy preference questions
- **R packages for working with CES data:**
  - `ccesMRPprep` — cleans and prepares CES data for MRP (https://github.com/kuriwaki/ccesMRPprep)
  - `ccesMRPrun` — runs MRP models on prepared CES data (https://www.shirokuriwaki.com/ccesMRPrun/)
  - Related paper: Kuriwaki et al., "The Geography of Racially Polarized Voting: Calibrating Surveys at the District Level," *American Political Science Review* (2023)

### 1B. Democracy Fund + UCLA Nationscape

- **What it is:** One of the largest public opinion surveys ever conducted. ~6,250 interviews per week from July 2019 to January 2021. Over 500,000 total interviews. Covers 40+ policy areas.
- **District-level coverage:** Designed to include at least 1,000 interviews in every congressional district by completion. Not directly representative at district level without modeling, but the sheer volume enables reasonable district-level estimation.
- **Download:** https://www.voterstudygroup.org/data/nationscape and Harvard Dataverse at https://dataverse.harvard.edu/dataset.xhtml?persistentId=doi:10.7910/DVN/CQFP3Z
- **Principal investigators:** Chris Tausanovitch and Lynn Vavreck (UCLA)
- **Limitation:** Covers the 2019-2021 period; not an ongoing survey.

### 1C. Tausanovitch & Warshaw — American Ideology Project

- **What it is:** Jointly scaled policy preferences of 275,000 Americans, producing ideology estimates for every state, congressional district, state legislative district, and large city. The definitive academic dataset for district-level ideological preferences.
- **Key paper:** Tausanovitch & Warshaw (2013), "Measuring Constituent Policy Preferences in Congress, State Legislatures, and Cities," *Journal of Politics* 75(2): 330-342.
- **Download:** http://www.chriswarshaw.com/data.php (last updated Fall 2022)
- **What it provides:** Cross-sectional estimates of political liberalism/conservatism (ideology) at congressional district level, plus presidential vote by geography.
- **Related:** Dynamic Democracy project (state policy ideology 1936-2024) at http://www.dynamicdemocracy.us/

### 1D. MRP (Multilevel Regression and Poststratification) — The Key Method

MRP is the standard method for estimating district-level opinion from national surveys. **You will almost certainly need to use MRP** to produce the district-level opinion estimates your tool requires, unless you find pre-computed estimates for the specific issues you care about.

**How it works:**
1. Fit a multilevel model predicting opinion from demographics + geography using national survey data
2. Use Census/ACS data to construct the demographic composition of each district
3. "Post-stratify" — apply the model predictions to each demographic cell in each district, weighted by cell population

**Key reference:** Warshaw & Rodden (2012), "How Should We Measure District-Level Public Opinion on Individual Issues?" *Journal of Politics* 74(1): 203-219. Available at https://web.stanford.edu/~jrodden/wp/DistrictMRP_06_17_2011.pdf

**Toolchain for running MRP yourself:**
- Start with CES microdata via `ccesMRPprep` R package
- Use American Community Survey (ACS) data for poststratification tables
- Fit models via `brms` (Bayesian regression) or `rstanarm`
- Post-stratify with `ccesMRPrun`
- The `autoMrP` R package automates some of this process

### 1E. Other Major Polling Sources (National/State, Not District)

- **Pew Research Center:** Extensive issue polling. Breaks down by demographics and sometimes state-level, but **not** by congressional district. National-level data useful as MRP input. https://www.pewresearch.org/
- **Gallup:** Historical trends on many issues. State-level breakdowns available via Gallup Analytics (paid). **Not** district-level. https://news.gallup.com/
- **ANES (American National Election Studies):** Smaller than CES but longer-running. State identifiers but not district-level representative. https://electionstudies.org/
- **Data for Progress:** Regular policy polling with crosstabs. National-level. https://www.dataforprogress.org/

---

## 2. Existing "Representation Gap" Tools and Research

### 2A. No Unified Tool Exists

**Nobody has built exactly what you are describing.** This is a significant finding — the civic tech space has tools for tracking votes and tools for tracking opinion, but no widely available interactive tool that overlays the two to show the gap. This represents a genuine gap in the ecosystem.

### 2B. Voting Record Trackers (One Half of the Equation)

| Tool | URL | Format | Notes |
|------|-----|--------|-------|
| **VoteView** | https://voteview.com/data | CSV bulk download | Roll-call votes + NOMINATE ideology scores. All of Congress back to 1789. Maintained by Lewis, Poole, Rosenthal et al. Best for ideology scores. |
| **GovTrack.us** | https://www.govtrack.us/about-our-data | JSON + XML via GitHub | Open data. Voting records, bill text, status. `unitedstates/congress` GitHub repo for bulk data. Public domain. |
| **Congress.gov API** | https://www.loc.gov/apis/additional-apis/congress-dot-gov-api/ | JSON API | Official Library of Congress API. Bills, amendments, votes. |
| **ProPublica Congress API** | https://projects.propublica.org/api-docs/congress-api/ | JSON API | **No longer issuing new API keys.** May be effectively discontinued. Had vote positions for each member. |
| **unitedstates/congress** | https://github.com/unitedstates/congress | JSON + XML | Open-source scrapers. Public domain. Originally by GovTrack + Sunlight Foundation. Best bulk data source. |

### 2C. Landmark Academic Research on Representation Gaps

**Gilens & Page (2014)** — "Testing Theories of American Politics: Elites, Interest Groups, and Average Citizens," *Perspectives on Politics* 12(3): 564-81. The single most cited study on this topic. Found that after controlling for affluent Americans' and interest groups' preferences, the middle class's preferences bear virtually no relationship to policy outcomes. Used ~2,000 survey questions on proposed policy changes from 1981-2002.
- Paper: https://www.princeton.edu/~mgilens/idr.pdf

**Bartels (2002)** — Found U.S. senators are consistently and substantially more responsive to high-income constituents, with greater bias among Republican senators.

**Key finding across the literature:** Representatives often respond more to wealthy citizens, interest groups, and co-partisans than to the public at large. Congressional staff systematically mis-estimate constituent opinions, with those relying more on conservative/business interest groups having more skewed perceptions.

**Even at 100% public support, there is only ~65% chance of policy adoption within 4 years** (Gilens 2012). Responsiveness increases during presidential election years.

### 2D. MSU Partisan Advantage Tracker

Measures how congressional district maps favor one party over another — related but different from opinion-vs-vote analysis. https://ippsr.msu.edu/partisan-advantage-tracker

---

## 3. Specific Issue Datasets at District Level

### 3A. Climate Change — Yale Climate Opinion Maps (YCOM)

**This is the gold standard for what district-level opinion data looks like.**

- **Coverage:** All 50 states, 435 congressional districts, 3,000+ counties
- **Issues covered:** 25+ climate beliefs, risk perceptions, and policy support questions (e.g., "% who support regulating CO2 as a pollutant," "% who think global warming is happening")
- **Methodology:** MRP using 13,000+ survey responses (2008-2024), downscaled to state/district/county
- **Accuracy:** +/- 7 percentage points at state and congressional district levels
- **Data availability:** Free download + interactive maps + PDF factsheets for every district
- **URL:** https://climatecommunication.yale.edu/visualizations-data/ycom-us/
- **Factsheets:** https://climatecommunication.yale.edu/visualizations-data/factsheets/
- **Congressional districts:** Based on 118th Congress boundaries
- **No dedicated API** — data available via download and interactive tool, not a programmatic endpoint
- **Format:** The download appears to be structured data (likely CSV), though the primary access is through their interactive visualization

**This is the model to emulate. Yale took national survey data, applied MRP, and produced district-level estimates that are freely downloadable.**

### 3B. Gun Policy

- **No pre-computed district-level dataset found.** This is a gap.
- **National survey data available from:**
  - Johns Hopkins National Survey of Gun Policy (2013, 2015, 2017, 2019): https://publichealth.jhu.edu/center-for-gun-violence-solutions/data/national-survey-of-gun-policy
  - Pew Research Center gun policy polling: https://www.pewresearch.org/topic/politics-policy/political-issues/gun-policy/
- **Academic work:** Warshaw & Rodden (2012) demonstrated MRP works for gun-related issues at district level, but did not publish a standing dataset. A CUNY study on the "gun control paradox" used disaggregation at state level, finding sufficient state-level sample sizes in existing polls.
- **To get district-level gun opinion:** You would need to apply MRP to CES data (which includes gun policy questions) or to the JHU survey data.

### 3C. Healthcare / ACA

- **Enrollment data at district level exists** (useful as a proxy, but not the same as opinion):
  - KFF Interactive Maps: ACA Marketplace enrollment by congressional district. https://www.kff.org/interactive/interactive-maps-estimates-of-enrollment-in-aca-marketplaces-and-medicaid-expansion/
  - KFF Premium Impact Maps: https://www.kff.org/health-costs/congressional-district-interactive-map-how-much-will-aca-premium-payments-rise-if-enhanced-subsidies-expire/
  - Joint Economic Committee: District-level health insurance loss projections from Medicaid/ACA cuts. https://www.jec.senate.gov/public/index.cfm/democrats/2025/6/new-updated-state-by-state-congressional-district-data-on-health-insurance-losses-from-medicaid-aca-cuts
- **Opinion data:**
  - State-level ACA opinion via MRP exists in academic literature: see "The Affordable Care Act and Polarization in the United States," *RSF Journal of the Social Sciences* 6(2): 114. Used MRP to estimate state-level quarterly ACA support 2009-2016.
  - District-level ACA opinion: Not found as a pre-computed dataset. Would need MRP on CES data.
- **RWJF Congressional District Health Data:** 36 health measures by district, though focused on health outcomes rather than policy opinion. https://www.rwjf.org/en/insights/our-research/2023/01/congressional-districts-and-health--what-can-be-measured-.html

### 3D. Immigration

- **No pre-computed district-level dataset found.** This is a gap.
- **National/state-level sources:**
  - Gallup Historical Trends on immigration: https://news.gallup.com/poll/1660/immigration.aspx
  - Chicago Council on Global Affairs surveys: https://globalaffairs.org/research/public-opinion-survey/american-support-legal-immigration-reaches-new-heights
  - Data for Progress immigration polling: https://www.dataforprogress.org/immigration
  - Pew Research immigration attitudes: https://www.pewresearch.org/topic/immigration-migration/immigration-attitudes/
- **To get district-level:** Apply MRP to CES data, which includes immigration policy questions.

### 3E. Summary: Issue-Specific District-Level Data Availability

| Issue | Pre-computed District Data? | Source | Notes |
|-------|---------------------------|--------|-------|
| Climate change | **Yes** | Yale YCOM | Gold standard. Free download. |
| Gun policy | **No** | — | Must run MRP on CES or JHU data |
| Healthcare/ACA | **Partial** (enrollment, not opinion) | KFF, JEC | Opinion requires MRP on CES |
| Immigration | **No** | — | Must run MRP on CES data |
| General ideology | **Yes** | Tausanovitch & Warshaw | Updated through 2022 |

---

## 4. APIs and Machine-Readable Data Availability

### 4A. Voting Records (Good API/Data Availability)

| Source | Format | Access | Status |
|--------|--------|--------|--------|
| Congress.gov API | JSON | Free API key | Active, official |
| GovTrack / unitedstates/congress | JSON, XML | Free, public domain | Active |
| VoteView | CSV bulk download | Free | Active |
| ProPublica Congress API | JSON | API key required | **Not issuing new keys** |

### 4B. Public Opinion (Mixed Availability)

| Source | Format | Access | Programmatic? |
|--------|--------|--------|---------------|
| CES/CCES Cumulative | .dta, .Rds, .feather | Free via Dataverse | R packages available |
| Yale Climate Opinion Maps | Download (likely CSV) + interactive | Free | No API; download only |
| Nationscape | Dataverse download | Free | Download only |
| Tausanovitch-Warshaw Ideology | Download | Free | Download only |
| KFF district enrollment data | Interactive maps | Free | No API found |

### 4C. Recommended Technical Stack for Your Tool

1. **Voting records:** Use `unitedstates/congress` GitHub repo (public domain JSON/XML) or Congress.gov API for current vote data
2. **Opinion data:** Download CES cumulative dataset, run MRP in R to produce district-level estimates for issues of interest
3. **Climate specifically:** Download Yale YCOM data directly
4. **Ideology baseline:** Download Tausanovitch-Warshaw data
5. **Store pre-computed:** Cache MRP results in your own database; these don't need real-time computation

---

## 5. Methodological Concerns and Limitations

### 5A. How Reliable Is MRP for District-Level Estimation?

**Generally good, but with important caveats:**

- MRP produces estimates with **smaller errors than simple disaggregation** at all sample sizes. With a national sample of just 2,500, MRP outperforms disaggregation with much larger samples (Warshaw & Rodden 2012).
- In districts with fewer than 10 survey respondents, MRP yields ~50% smaller errors than disaggregation. As sample sizes per district grow above 100, MRP and disaggregation converge.
- Yale Climate Opinion Maps report accuracy of **+/- 7 percentage points** at the district level. This is a meaningful margin of error.
- YouGov used MRP to correctly predict 93% of UK constituencies in the 2017 general election.

### 5B. Key Limitations

1. **Variable constraints:** MRP can only use individual-level variables present in both the survey AND the Census/ACS. Religion, party ID, and media consumption are not in the Census — these cannot be directly included without synthetic expansion techniques (see `kuriwaki/synthjoint` package).

2. **Model specification sensitivity:** MRP requires careful setup. Andrew Gelman (one of MRP's creators) notes: "you can't just push a button, you have to be careful in setting up your problem or you can get bad results." Results can vary based on modeling choices.

3. **Margins of error:** +/- 7 points at district level means a "52% support" estimate could actually be 45% or 59%. **Presenting narrow margins as clear mandates would be misleading.** Your tool should communicate uncertainty.

4. **Temporal lag:** CES is conducted annually around November. MRP estimates reflect opinion at survey time, not necessarily at the time of a specific vote. Public opinion can shift rapidly on salient issues.

5. **Redistricting complications:** District boundaries change after each Census. Historical comparisons require mapping old survey responses to new district boundaries. The Yale maps note that some districts lack data due to redistricting litigation.

6. **Issue framing effects:** How a survey question is worded significantly affects responses. A question about "gun safety regulations" will poll differently than one about "gun control." Your tool would need to be transparent about exact question wording.

7. **Salience vs. preference:** A respondent saying they "support" a policy in a survey may not consider it a priority. There is a difference between diffuse support and intense opposition. A representative voting against 55% opinion on a low-salience issue is qualitatively different from voting against 80% opinion on a high-salience issue.

8. **ACS limitations for districts:** The American Community Survey does not provide microdata at the congressional district level. Only certain two- and three-way demographic cross-tabulations are available, which constrains the complexity of poststratification tables.

### 5C. Recommendations for Your Tool

- **Always show confidence intervals or margin of error**, not point estimates alone
- **Link to the exact survey question wording** so users can judge whether it maps to the vote in question
- **Be explicit about the date of the opinion data** versus the date of the vote
- **Use language like "estimated district opinion" rather than "what your district thinks"** — acknowledge these are statistical estimates
- **Focus on large gaps** (e.g., 70%+ support vs. a "no" vote) where the signal clearly exceeds the noise, rather than highlighting narrow cases
- **Consider showing a "confidence" rating** for each claim — high confidence when the gap is large and the question wording closely matches the bill, lower when margins are tight or the mapping is loose

---

## 6. Practical Path Forward

### Phase 1: Proof of Concept (Lowest Effort)
- Use Yale Climate Opinion Maps (pre-computed, free, district-level) + Congressional vote data on climate/energy bills
- This requires no MRP work — just cross-reference existing datasets
- Demonstrates the concept with real data

### Phase 2: Expand to More Issues
- Download CES cumulative dataset
- Run MRP using `ccesMRPprep` + `ccesMRPrun` in R to generate district-level opinion estimates for:
  - Gun policy questions from CES
  - Healthcare/ACA questions from CES
  - Immigration questions from CES
- Cross-reference with specific roll-call votes from `unitedstates/congress` or Congress.gov API

### Phase 3: Ongoing Updates
- Each year's new CES release updates opinion estimates
- Congress.gov API or GovTrack provides ongoing vote data
- Build pipeline to re-run MRP annually and update the database

### Key Technical Decisions
- **Match votes to questions carefully.** A CES question about "banning assault weapons" needs to be matched to the specific bill text, not just any gun vote. This editorial/curatorial step is critical and cannot be fully automated.
- **Choose your presentation threshold.** Only surface cases where the gap between estimated opinion and the vote is large enough to be meaningful given the margin of error.

---

## Sources

### Primary Data Sources
- [Cooperative Election Study (CES) — Main Site](https://cces.gov.harvard.edu/)
- [CES Dataverse](https://dataverse.harvard.edu/dataverse/cces)
- [CES Cumulative Dataset](https://dataverse.harvard.edu/dataset.xhtml?persistentId=doi:10.7910/DVN/II2DB6)
- [CES Cumulative Policy Preferences](https://dataverse.harvard.edu/dataset.xhtml?persistentId=doi:10.7910/DVN/OSXDQO)
- [Yale Climate Opinion Maps 2024](https://climatecommunication.yale.edu/visualizations-data/ycom-us/)
- [Yale Climate Factsheets](https://climatecommunication.yale.edu/visualizations-data/factsheets/)
- [Democracy Fund + UCLA Nationscape](https://www.voterstudygroup.org/data/nationscape)
- [Nationscape on Harvard Dataverse](https://dataverse.harvard.edu/dataset.xhtml?persistentId=doi:10.7910/DVN/CQFP3Z)
- [Tausanovitch & Warshaw — American Ideology Project](http://www.chriswarshaw.com/data.php)
- [Dynamic Democracy (State Policy Ideology 1936-2024)](http://www.dynamicdemocracy.us/)

### Voting Record Data
- [VoteView Data](https://voteview.com/data)
- [GovTrack.us — About Our Data](https://www.govtrack.us/about-our-data)
- [unitedstates/congress GitHub](https://github.com/unitedstates/congress)
- [Congress.gov API](https://www.loc.gov/apis/additional-apis/congress-dot-gov-api/)
- [ProPublica Congress API (may be sunsetting)](https://projects.propublica.org/api-docs/congress-api/)

### Issue-Specific Sources
- [KFF ACA Enrollment Interactive Maps](https://www.kff.org/interactive/interactive-maps-estimates-of-enrollment-in-aca-marketplaces-and-medicaid-expansion/)
- [KFF Premium Impact by Congressional District](https://www.kff.org/health-costs/congressional-district-interactive-map-how-much-will-aca-premium-payments-rise-if-enhanced-subsidies-expire/)
- [JHU National Survey of Gun Policy](https://publichealth.jhu.edu/center-for-gun-violence-solutions/data/national-survey-of-gun-policy)
- [RWJF Congressional District Health Data](https://www.rwjf.org/en/insights/our-research/2023/01/congressional-districts-and-health--what-can-be-measured-.html)
- [Gallup Immigration Trends](https://news.gallup.com/poll/1660/immigration.aspx)
- [Data for Progress — Immigration](https://www.dataforprogress.org/immigration)

### MRP Methodology
- [Warshaw & Rodden (2012) — District-Level MRP](https://web.stanford.edu/~jrodden/wp/DistrictMRP_06_17_2011.pdf)
- [ccesMRPprep R Package](https://github.com/kuriwaki/ccesMRPprep)
- [ccesMRPrun R Package](https://www.shirokuriwaki.com/ccesMRPrun/)
- [MRP Case Studies (Bookdown)](https://bookdown.org/jl5522/MRP-case-studies/introduction-to-mrp.html)
- [Kastellec MRP Primer (Princeton)](https://jkastellec.scholar.princeton.edu/publications/mrp_primer)

### Academic Research on Representation
- [Gilens — Inequality and Democratic Responsiveness](https://www.princeton.edu/~mgilens/idr.pdf)
- [Gilens & Page (2014) — Testing Theories of American Politics](https://www.cambridge.org/core/journals/perspectives-on-politics/article/testing-theories-of-american-politics-elites-interest-groups-and-average-citizens/62327F513959D0A304D4893B382B992B)
- [MSU Partisan Advantage Tracker](https://ippsr.msu.edu/partisan-advantage-tracker)
