# US Civic Tech Landscape Research (Early 2026)

---

## 1. Existing Civic Tech Tools & Platforms

### Active & Prominent Tools (Citizen-Facing)

| Tool | What It Does | Status |
|------|-------------|--------|
| **Resistbot** | Text-to-letter service for contacting elected officials (text "resist" to 50409). Has served 9+ million users, delivered 30+ million letters. | Active, well-maintained |
| **5 Calls** | Provides scripts and phone numbers for calling reps on active issues. "Spend 5 minutes, make 5 calls." | Active |
| **GovTrack.us** | Tracks federal legislation, voting records, legislator stats. In 2025 expanded to track White House/executive orders. | Active, small team |
| **OpenSecrets** | Premier money-in-politics tracker. Campaign finance, lobbying, personal financial disclosures. Merged with FollowTheMoney.org for state-level data. | Active, well-funded |
| **BallotReady** | Comprehensive ballot info for every level of government (Senate to school board). Voter registration, mail-in ballot tools, rep contact. Acquired PioneerGov AI tech. | Active, growing |
| **Vote Smart** | Nonpartisan candidate info: voting records, issue positions (Political Courage Test), campaign finances, interest group ratings. Now based at Drake University. | Active |
| **Common Cause** | Advocacy org (1.5M+ members). Voter protection, ethics complaints, anti-gerrymandering, AI transparency legislation. | Active, strong advocacy wins |
| **MAPLE** (MA Platform for Legislative Engagement) | Code for Boston project. Lets MA residents submit testimony on pending legislation and read others' testimony. Public archive of testimony. | Active, state-level |

### Government/Enterprise Engagement Platforms

| Platform | Description |
|----------|-------------|
| **Granicus** | Government Experience Cloud. Online meetings, automated accessibility, email/SMS messaging. Major government vendor. |
| **CivicPlus** | Unified citizen identity across city services. Emergency alerts, issue reporting, modular design. |
| **GoVocal** | Data-driven civic engagement. Idea collection, participatory budgeting, sentiment tracking. |
| **CitizenLab** | Co-creation platform. Participatory budgeting, map-based issue reporting, multilingual. |
| **Consul** | Open-source. Used by Madrid, Buenos Aires. Scalable participation with full data control. |
| **Balancing Act** | Interactive municipal budget simulation. Citizens explore trade-offs. |
| **Zencity** | AI-driven community insights for local government. |

### Failed, Pivoted, or Diminished

| Tool/Org | What Happened |
|----------|--------------|
| **Countable** | Originally a consumer app for tracking legislation and contacting reps. After merging with Causes (2020), pivoted entirely to enterprise B2B. Consumer civic engagement app is effectively gone. |
| **Code for America Brigades** | CfA ended its Brigade Program in Jan 2023, cutting fiscal sponsorship for ~60 local volunteer chapters. Many forced to rebrand (e.g., "Code for SF" became "SF Civic Tech," "Code for DC" became "Civic Tech DC"). Further disrupted when Open Collective Foundation shut down. |
| **Sunlight Foundation** | Shut down Sunlight Labs, downsized, and considered merging. A major loss for open government data. |
| **OpenGov Foundation** | Discontinued most work on America Decoded. |
| **18F** | Eliminated in 2025 as part of federal restructuring. |
| **USDS** | Merged into the Department of Government Efficiency (DOGE) under the Trump administration, sparking backlash from the civic tech community. |
| **ProPublica Congress API** | No longer available. Developers directed to Congress.gov API or Google Civic Information API. |
| **Google Civic Information API (Representatives endpoint)** | Representatives API turned down April 30, 2025. Election/voter info endpoints remain, but elected official lookup is gone. |

### Key Organizational Development

- **Alliance of Civic Technologists** launched as a new umbrella for former CfA brigades (Boston, Seattle, 14+ other cities participating).
- **Rock the Vote** continues voter registration tech and civic engagement programs.
- **Ballotpedia** and **Cicero** have become important data providers filling the gap left by Google's Representatives API shutdown.

---

## 2. Available Public Data Sources & APIs

### Federal Legislative Data

| Source | Description | Access |
|--------|-------------|--------|
| **Congress.gov API** | Official API from Library of Congress. Bills, amendments, members, committees, voting records, treaties, nominations. | Free, API key required. github.com/LibraryOfCongress/api.congress.gov |
| **GovInfo API** | Government Publishing Office publications. Full text of bills, reports, Federal Register. Launching MCP server for AI tools. | Free. api.govinfo.gov |
| **GovTrack.us** | Parsed congressional data, voting records, bill status, legislator statistics. | Free, open data |
| **LegiScan API** | Structured JSON for legislation in all 50 states + Congress. Bill details, status, sponsors, full text, roll calls. | Free tier: 30K queries/month |
| **BICAM Dataset** (2025) | Bulk Ingestion of Congressional Actions & Materials. All electronically available official records from 1789 to present: 11 data components. | Academic/research dataset |

### Campaign Finance & Money in Politics

| Source | Description | Access |
|--------|-------------|--------|
| **FEC API** | RESTful API for federal campaign finance. Individual contributions, candidate data, committee data, independent expenditures. Bulk downloads also available. | Free. api.open.fec.gov |
| **OpenSecrets Open Data** | 30+ years of processed campaign finance, lobbying, personal financial disclosure data. Summary and raw data. | Free for research; bulk data available |
| **FollowTheMoney.org** | State-level campaign finance (now part of OpenSecrets). | Free |
| **The Accountability Project** | FEC Schedule A data (2007-2020), nonprofits, lobbying, government spending, voter registration datasets. | Free. publicaccountability.org |

### Lobbying & Ethics

| Source | Description | Access |
|--------|-------------|--------|
| **U.S. Senate Lobbying Disclosure Database** | Downloadable quarterly lobbying filings. | Free. senate.gov |
| **LobbyView** | Academic resource linking lobbying filings to legislative bills. Network data on legislative politics. | Free for research. lobbyview.org |
| **LobbyingData.com** | 100% federal lobbying activity, 1999-present. Real-time and historical. | API available; commercial and public sector customers |

### Elections & Voter Information

| Source | Description | Access |
|--------|-------------|--------|
| **Google Civic Information API** | Polling places, early voting locations, election official contacts, ballot info. NOTE: Representatives endpoint shut down April 2025. | Free, 25K queries/day |
| **BallotReady API** | Comprehensive candidate/office data for every level of government. Replaced Google for some use cases. | Commercial API |
| **Ballotpedia** | Encyclopedic candidate and election data. | Data licensing available |
| **Cicero** | Elected official data by address. | Commercial API |
| **Vote Smart API** | Candidate bios, voting records, issue positions, ratings. | API available |

### Other Government Data

| Source | Description |
|--------|-------------|
| **Data.gov** | Federal open data portal. Thousands of datasets across agencies. |
| **Federal Register API** | Daily Journal of the US Government. Rules, proposed rules, notices, executive orders. |
| **USAspending.gov** | Federal spending data. Contracts, grants, loans. |
| **Census Bureau APIs** | Demographic, economic, geographic data. |
| **Open Civic Data Identifiers (OCD-IDs)** | Standardized IDs for political jurisdictions. Useful for linking datasets. |

### Notable 2025-2026 Developments

- **GPO launching MCP server** for AI tools to access official government publications (a significant development for AI-powered civic tools).
- **Congressional Data Task Force** continues with 2026 meetings scheduled and annual Congressional Hackathon.
- **ProPublica Congress API is gone** -- Congress.gov API is now the primary replacement.
- **Google Representatives API is gone** -- BallotReady, Ballotpedia, and Cicero are the alternatives.

---

## 3. What's Broken or Missing

### Structural/Institutional Problems

1. **Federal civic tech infrastructure gutted.** 18F eliminated. USDS absorbed into DOGE. Civic tech leaders worry DOGE is "tarnishing" the tools meant to improve government. The institutional knowledge and capacity for government digital modernization has been severely damaged.

2. **Brigade network fragmented.** Code for America dropped ~60 local chapters. Many survived by reorganizing (Alliance of Civic Technologists), but lost projects, leadership, and momentum during the transition.

3. **Funding crisis.** Major funders have shifted strategies. Frustration over projects not completing on time created "wariness in funding opportunities." Sunlight Foundation, OpenGov Foundation, and others have shut down or shrunk. The sustainability question remains unsolved for free civic tools.

### Technology & Data Gaps

4. **No reliable free API for elected official data.** Google's Representatives API shutdown (April 2025) left a major gap. The remaining options (BallotReady, Cicero, Ballotpedia) are commercial. There is no free, comprehensive, maintained API to look up "who represents me at every level of government." This is a critical infrastructure gap.

5. **Local government data is a desert.** Federal data is comparatively well-served. State data is spotty. City/county level data (council votes, local ordinances, zoning decisions, board meeting minutes, local campaign finance) is almost entirely unstructured, unstandardized, and inaccessible programmatically.

6. **No unified "civic stack."** Tools are siloed. Resistbot does letters. 5 Calls does phone calls. GovTrack does bill tracking. OpenSecrets does money tracking. BallotReady does ballot info. There is no integrated platform that ties these together into a coherent civic engagement experience.

7. **Transparency without actionability.** Harvard Ash Center research highlights that civic tech often produces dashboards and data displays but fails to connect information to collective action. "To the extent that civic technology has failed, it has not been because of insufficient data, but because it often ignores power and collective action."

### User Experience & Engagement Problems

8. **Engagement drops between elections.** Civic tech usage spikes around elections and crises, then drops off. No tool has solved the sustained engagement problem.

9. **Digital divide.** Low-income households, elderly, and rural populations are systematically underserved. Mobile-first design is still not universal. Multilingual support is inconsistent.

10. **The "large digital cemetery."** Too many civic tech projects start with technology instead of people. Result: abandoned dashboards, red-flag systems, report apps, and interactive maps that nobody uses.

11. **Ad hoc data analysis.** Most government agencies analyze engagement data on an ad hoc basis rather than systematically. Insights that could improve equity and resource allocation are lost.

### Specific Unmet Needs

12. **State and local legislative tracking.** LegiScan covers state bills, but there is no good equivalent for county/city level. Tracking local ordinances, zoning changes, school board decisions, etc. remains essentially manual.

13. **Lobbying transparency at the state/local level.** Federal lobbying is well-documented. State lobbying data varies wildly in quality and accessibility. Local lobbying is largely invisible.

14. **Cross-referencing money and votes.** While OpenSecrets tracks money and GovTrack tracks votes, connecting the two (who funded a legislator, and how did they vote on related issues) requires manual research. No consumer tool makes this easy.

15. **Collective action coordination.** Tools help individuals contact reps, but few help communities organize sustained pressure campaigns, coordinate testimony at public hearings, or track the progress of advocacy efforts.

---

## 4. Successful Models & Measurable Impact

### Proven Models

**Resistbot** -- Scale of individual advocacy
- 9+ million users, 30+ million letters delivered, 450+ million text messages handled.
- Success factor: extreme simplicity (text a keyword), low barrier to entry, meets people where they are (SMS/messaging apps).

**OpenSecrets** -- Transparency as public good
- 30+ years of data. Routinely cited by journalists, researchers, and policymakers.
- Success factor: authoritative data, sustained institutional commitment, earned trust as nonpartisan source.

**Participatory Budgeting (NYC, Paris, others)**
- Citizens directly propose and vote on municipal spending priorities.
- Success factor: real power (actual budget dollars at stake), tangible local impact, face-to-face + digital hybrid.

**Common Cause** -- Advocacy driving policy
- 2025: Secured voting rights protections in state law, 4 states rescinded Article V convention applications, passed CA AI Transparency Act update, filed 57 ethics complaints against Trump administration.
- Success factor: combination of grassroots mobilization, legal expertise, and policy sophistication.

**MAPLE (Massachusetts)**
- Democratized legislative testimony. Public archive of who said what on pending bills.
- Success factor: solves a specific, well-defined problem (testimony submission is confusing and opaque) with a simple tool.

**Pol.is (Taiwan)**
- Used for national policy dialogues (Uber regulation, e-commerce alcohol sales).
- Success factor: deliberative design that surfaces consensus rather than amplifying division. Government committed to acting on results.

**GovTrack.us**
- One of the longest-running civic tech projects (since 2004). Expanded to White House tracking in 2025.
- Success factor: sustained maintenance, clear focus, open data ethos.

**BallotReady**
- Comprehensive down-ballot information (the races most voters know least about).
- Success factor: filling a specific information gap (school board, judges, local offices) that media doesn't cover.

### What Makes Civic Tech Succeed (Patterns)

Based on the research, successful civic tech shares these characteristics:

1. **Solves a specific, felt problem** -- not "civic engagement" in the abstract, but "I need to call my senator about this bill" or "I don't know who's on my ballot."

2. **Extreme simplicity** -- Resistbot works via text message. 5 Calls gives you a phone number and a script. Low friction wins.

3. **Sustained institutional commitment** -- The projects that last have dedicated organizations behind them (OpenSecrets, GovTrack, Common Cause), not just volunteer energy.

4. **Real power or real information** -- Participatory budgeting gives citizens actual budget authority. OpenSecrets provides data journalists actually use. Tools that create an illusion of engagement without real influence get abandoned.

5. **Nonpartisan positioning** -- The most durable tools (GovTrack, OpenSecrets, Vote Smart, BallotReady) are deliberately nonpartisan, which broadens their user base and protects institutional credibility.

6. **Citizen-centered design, not technology-centered** -- Per Harvard Ash Center: "Effective civic technology is usually quite simple, condensing complexity to a level that is actionable and intuitive for citizens."

---

## Sources

- [Congress.gov API](https://api.congress.gov/)
- [FEC API](https://api.open.fec.gov/)
- [OpenSecrets](https://www.opensecrets.org/)
- [GovTrack.us](https://www.govtrack.us/)
- [Resistbot](https://resist.bot/guide)
- [5 Calls](https://5calls.org/)
- [BallotReady](https://www.ballotready.org/)
- [Vote Smart](https://www.votesmart.org/)
- [Common Cause](https://www.commoncause.org/)
- [LegiScan API](https://legiscan.com/legiscan)
- [MAPLE](https://www.mapletestimony.org/)
- [Google Civic Information API](https://developers.google.com/civic-information)
- [Google Representatives API Turndown Notice](https://groups.google.com/g/google-civicinfo-api/c/9fwFn-dhktA)
- [LobbyView](https://lobbyview.org/)
- [U.S. Senate Lobbying Database](https://www.senate.gov/legislative/Public_Disclosure/database_download.htm)
- [Alliance of Civic Technologists](https://www.civictechnologists.org/)
- [Congressional Data Task Force](https://congressionaldata.org/)
- [The Accountability Project](https://publicaccountability.org/datasets/home/)
- [Harvard Ash Center - Transparency is Insufficient](https://ash.harvard.edu/articles/transparency-is-insufficient-lessons-from-civic-technology-for-anticorruption/)
- [Federal News Network - Building Civic Tech That Works](https://federalnewsnetwork.com/technology-main/2025/08/building-civic-tech-that-actually-works-for-the-people-who-need-it-most/)
- [Nextgov - Civic Tech Leaders Worry DOGE is Tarnishing Its Tools](https://www.nextgov.com/digital-government/2025/06/civic-tech-leaders-worry-doge-tarnishing-its-tools-improve-government/405985/)
- [StateScoop - CfA Brigades Regroup](https://statescoop.com/code-for-america-former-brigades-regroup/)
- [ACM Interactions - What Does Failure Mean in Civic Tech](https://interactions.acm.org/archive/view/march-april-2024/what-does-failure-mean-in-civic-tech-we-need-continued-conversations-about-discontinuation)
- [Bill Hunt - The End of the Second Act of Civic Tech](https://krusynth.medium.com/the-end-of-the-second-act-of-civic-tech-2d8d9c766309)
- [Network Impact - Civic Tech: How to Measure Success](https://www.networkimpact.org/resources/civic-tech-how-to-measure-success)
- [OECD - Tackling Civic Participation Challenges (2025)](https://www.oecd.org/en/publications/2025/04/tackling-civic-participation-challenges-with-emerging-technologies_bbe2a7f5.html)
- [Granicus - Civic Engagement Benchmarks 2025](https://granicus.com/blog/civic-engagement-and-communication-benchmarks-for-success-in-2025/)
- [Ayerhs Magazine - Return of Civic Engagement 2026](https://ayerhsmagazine.com/2025/11/21/the-return-of-civic-engagement-in-2026/)
- [GoingVC - The VC Case for CivicTech](https://www.goingvc.com/post/the-vc-case-for-civictech-and-govtech)
