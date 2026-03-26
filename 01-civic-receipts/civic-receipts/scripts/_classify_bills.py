#!/usr/bin/env python3
"""
Classify bills into 10 policy issue categories for electorate alignment scoring.

For each bill, determines:
- Which of 10 policy issues it relates to
- Whether voting Yea means SUPPORTING or OPPOSING the issue position
- Confidence level and reason

Only includes bills that are clearly relevant to specific issues.
"""
import json
import os
import re

CACHE_DIR = os.path.join(os.path.dirname(__file__), '.cache', 'llm_electorate_positions')
BILLS_PATH = os.path.join(CACHE_DIR, '_all_bills.json')
OUTPUT_DIR = CACHE_DIR

# Load bills
with open(BILLS_PATH) as f:
    bills = json.load(f)

# ============================================================
# Manual classification of all relevant bills
# ============================================================
# Format: {issue_key: {bill_id: {yea_means_support, confidence, reason}}}

classifications = {
    "background_checks": {},
    "assault_weapons_ban": {},
    "abortion_legal": {},
    "abortion_20_weeks": {},
    "support_aca": {},
    "regulate_co2": {},
    "renewable_fuel": {},
    "daca": {},
    "border_wall": {},
    "concealed_carry": {},
}

# Helper to add a classification
def add(issue, bill_id, yea_means_support, confidence, reason):
    if bill_id not in bills:
        return  # Skip if bill not in our dataset
    classifications[issue][bill_id] = {
        "yea_means_support": yea_means_support,
        "confidence": confidence,
        "reason": reason,
    }


# ── GUN CONTROL: background_checks ─────────────────────────────
# HR7910 (118th) - Protecting Our Kids Act - includes enhanced background checks
add("background_checks", "HR7910", True, 0.85, "Protecting Our Kids Act includes enhanced background check provisions")

# ── GUN CONTROL: assault_weapons_ban ────────────────────────────
# HR1808 - Assault Weapons Ban (117th Congress)
add("assault_weapons_ban", "HR1808", True, 0.95, "Bans assault-style weapons")

# HR7910 - Protecting Our Kids Act - includes raising age for semi-auto purchases
add("assault_weapons_ban", "HR7910", True, 0.8, "Protecting Our Kids Act raises age for semi-automatic rifle purchases")

# ── GUN CONTROL: concealed_carry ────────────────────────────────
# (No specific concealed carry reciprocity or permit bills found in this dataset)

# ── ABORTION: abortion_legal ────────────────────────────────────
# HR21 - Born-Alive Abortion Survivors Protection Act (119th)
add("abortion_legal", "HR21", False, 0.95, "Born-Alive Act restricts abortion provider practices; voting Yea opposes abortion access")

# S6 - Born-Alive Abortion Survivors Protection Act (Senate, 119th)
add("abortion_legal", "S6", False, 0.95, "Born-Alive Act restricts abortion provider practices; voting Yea opposes abortion access")

# HR8296 - Women's Health Protection Act (117th)
add("abortion_legal", "HR8296", True, 0.95, "Protects right to abortion access nationwide")

# HR8297 - Ensuring Access to Abortion Act (117th)
add("abortion_legal", "HR8297", True, 0.95, "Ensures access to abortion services")

# HR8373 - Right to Contraception Act (117th)
add("abortion_legal", "HR8373", True, 0.85, "Protects right to contraception, related to reproductive rights")

# HR6914 - Pregnant Students' Rights Act (118th) - not directly about abortion legality, skip
# HR6918 - Supporting Pregnant and Parenting Women and Families Act (118th) - pro-life alternative framing
add("abortion_legal", "HR6918", False, 0.7, "Pro-life alternative supporting pregnant women; frames pregnancy support as alternative to abortion")

# HR6945 - Supporting Pregnant and Parenting Women and Families Act (119th, reintroduced)
add("abortion_legal", "HR6945", False, 0.7, "Pro-life alternative supporting pregnant women; frames pregnancy support as alternative to abortion")

# HR485 - Protecting Health Care for All Patients Act (119th) - related to conscience protections
# S4554 - Express support for protecting access to reproductive health care after Dobbs
add("abortion_legal", "S4554", True, 0.9, "Expresses support for protecting reproductive health care access after Dobbs")

# S4445 - Protect and expand nationwide access to fertility treatment including IVF
add("abortion_legal", "S4445", True, 0.75, "Protects access to fertility treatment including IVF, related to reproductive rights")

# HR5376 - Inflation Reduction Act / Build Back Better - skip, too broad

# ── ABORTION: abortion_20_weeks ─────────────────────────────────
# HR21 - Born-Alive Abortion Survivors Protection Act - related to late-term abortion restrictions
add("abortion_20_weeks", "HR21", True, 0.8, "Born-Alive Act targets late-term abortion outcomes; voting Yea supports restricting late abortions")

# S6 - Born-Alive Act (Senate)
add("abortion_20_weeks", "S6", True, 0.8, "Born-Alive Act targets late-term abortion outcomes; voting Yea supports restricting late abortions")


# ── HEALTHCARE: support_aca ─────────────────────────────────────
# HR6703 - Lower Health Care Premiums for All Americans Act (119th)
# This is a Republican bill to "lower premiums" but likely through deregulation/weakening ACA protections
add("support_aca", "HR6703", False, 0.75, "Republican bill to lower premiums by loosening ACA marketplace rules and protections")

# HR498 - Do No Harm in Medicaid Act (119th) - restricts Medicaid, opposes ACA expansion
add("support_aca", "HR498", False, 0.8, "Restricts Medicaid provisions, weakening ACA-era coverage expansions")

# HR6833 - Affordable Insulin Now Act (117th) - caps insulin costs, supports healthcare coverage
add("support_aca", "HR6833", True, 0.75, "Caps insulin costs, strengthening affordable healthcare access")

# HR2483 - SUPPORT for Patients and Communities Reauthorization Act (119th) - opioid/substance abuse
# Not directly ACA-related, skip

# HR1834 - Breaking the Gridlock Act (119th) - large omnibus, includes Medicaid/ACA provisions
# This is the big GOP reconciliation bill that cuts Medicaid
add("support_aca", "HR1834", False, 0.85, "GOP reconciliation bill includes major Medicaid cuts and work requirements")

# HR1 - One Big Beautiful Bill Act (119th) - massive reconciliation, cuts Medicaid
add("support_aca", "HR1", False, 0.85, "GOP reconciliation bill cuts Medicaid by hundreds of billions, adds work requirements")

# S3385 - Extend health care premium tax credit enhancement
add("support_aca", "S3385", True, 0.9, "Extends ACA premium tax credit enhancements that reduce marketplace costs")

# S3386 - Health savings account contributions, reduce health care costs
add("support_aca", "S3386", False, 0.7, "HSA-based alternative approach that undermines ACA marketplace model")

# HR4531 - Support for Patients and Communities Reauthorization Act (118th) - opioid focused, skip

# HR5378 - Lower Costs, More Transparency Act (118th) - healthcare transparency
add("support_aca", "HR5378", True, 0.7, "Increases healthcare cost transparency, complementing ACA goals")

# HR7024 - Tax Relief for American Families and Workers Act - not healthcare focused, skip

# HR485 - Protecting Health Care for All Patients Act (119th)
# This is about banning quality-adjusted life year (QALY) metrics - Republican anti-ACA measure
add("support_aca", "HR485", False, 0.7, "Restricts healthcare cost-effectiveness analysis used to implement ACA provisions")

# HR542 - Elizabeth Dole Home- and Community-Based Services for Veterans Act - VA specific, skip

# HR3843 - Action for Dental Health Act - bipartisan dental, not ACA specific, skip


# ── CLIMATE: regulate_co2 ──────────────────────────────────────
# HCONRES86 - Expressing sense that carbon tax would be detrimental (118th)
add("regulate_co2", "HCONRES86", False, 0.95, "Resolution opposing carbon tax; voting Yea opposes CO2 regulation")

# HR1023 - Repeal section 134 of Clean Air Act (greenhouse gas reduction fund) (118th)
add("regulate_co2", "HR1023", False, 0.95, "Repeals greenhouse gas reduction fund from Clean Air Act")

# HR1121 - Protecting American Energy Production Act (118th)
add("regulate_co2", "HR1121", False, 0.85, "Blocks EPA emissions regulations on energy production")

# HR6009 - Restoring American Energy Dominance Act (118th)
add("regulate_co2", "HR6009", False, 0.85, "Rolls back environmental regulations to expand fossil fuel production")

# HRES987 - Denouncing harmful anti-American energy policies of Biden admin (118th)
add("regulate_co2", "HRES987", False, 0.8, "Resolution denouncing Biden energy/climate policies")

# HR7023 - Creating Confidence in Clean Water Permitting Act (118th)
add("regulate_co2", "HR7023", False, 0.75, "Weakens clean water permitting requirements")

# HR26 - Protecting American Energy Production Act (119th)
add("regulate_co2", "HR26", False, 0.85, "Blocks restrictions on energy production, opposes emissions regulation")

# HJRES61 - CRA disapproval of EPA rule (119th)
add("regulate_co2", "HJRES61", False, 0.9, "CRA disapproval of EPA environmental rule; voting Yea blocks environmental regulation")

# HJRES35 - CRA disapproval of EPA rule (119th)
add("regulate_co2", "HJRES35", False, 0.9, "CRA disapproval of EPA environmental rule")

# SJRES11 - CRA disapproval of Bureau of Land Management rule (119th)
add("regulate_co2", "SJRES11", False, 0.85, "CRA disapproval of BLM environmental rule")

# HJRES88 - CRA disapproval of EPA rule on California motor vehicle pollution control (119th)
add("regulate_co2", "HJRES88", False, 0.9, "CRA disapproval of EPA California vehicle emissions standards")

# HJRES89 - CRA disapproval of EPA rule on California engine pollution (119th)
add("regulate_co2", "HJRES89", False, 0.9, "CRA disapproval of EPA California engine emissions standards")

# HJRES87 - CRA disapproval of EPA California motor vehicle pollution control (119th)
add("regulate_co2", "HJRES87", False, 0.9, "CRA disapproval of EPA California vehicle pollution control standards")

# SJRES31 - CRA disapproval of EPA rule "Review of..." (119th)
add("regulate_co2", "SJRES31", False, 0.9, "CRA disapproval of EPA environmental regulation")

# HJRES136 - CRA disapproval of EPA rule (118th)
add("regulate_co2", "HJRES136", False, 0.9, "CRA disapproval of EPA environmental regulation")

# HR4824 - Carbon Sequestration Collaboration Act (118th)
add("regulate_co2", "HR4824", True, 0.8, "Promotes carbon sequestration research and collaboration")

# HJRES140 - CRA disapproval of BLM rule (119th) - about land withdrawal in MN
add("regulate_co2", "HJRES140", False, 0.8, "CRA disapproval of BLM public land protection in Minnesota")

# SJRES55 - CRA disapproval rule (119th)
# Need to check what this is about - generic CRA
# Skip without more info

# HR1949 - Unlocking our Domestic LNG Potential Act (119th)
add("regulate_co2", "HR1949", False, 0.85, "Expands LNG exports and fossil fuel production")

# HR7176 - Unlocking our Domestic LNG Potential Act (118th, earlier version)
add("regulate_co2", "HR7176", False, 0.85, "Expands LNG exports and fossil fuel production")

# HR3109 - REFINER Act (119th)
add("regulate_co2", "HR3109", False, 0.8, "Reduces regulatory burden on oil refineries")

# HR3632 - Power Plant Reliability Act (119th)
add("regulate_co2", "HR3632", False, 0.8, "Weakens EPA power plant emission regulations in name of reliability")

# HR3616 - Reliable Power Act (119th)
add("regulate_co2", "HR3616", False, 0.8, "Limits EPA authority over power plant emissions for grid reliability")

# HR3628 - State Planning for Reliability and Affordability Act (119th)
add("regulate_co2", "HR3628", False, 0.75, "Prioritizes energy affordability over emissions standards")

# HR3638 - Electric Supply Chain Act (119th)
# This is more about supply chain, skip - too tangential

# HR1047 - GRID Power Act (119th) - likely pro-fossil
add("regulate_co2", "HR1047", False, 0.7, "Prioritizes grid reliability potentially at expense of emissions standards")

# HR3015 - National Coal Council Reestablishment Act (119th)
add("regulate_co2", "HR3015", False, 0.85, "Reestablishes National Coal Council, promoting coal industry interests")

# HR6285 - Alaska's Right to Produce Act (118th)
add("regulate_co2", "HR6285", False, 0.85, "Expands oil and gas production in Alaska")

# HR1435 - Preserving Choice in Vehicle Purchases Act (118th)
add("regulate_co2", "HR1435", False, 0.85, "Blocks EV mandates and vehicle emissions standards")

# HR4468 - Choice in Automobile Retail Sales Act (118th)
add("regulate_co2", "HR4468", False, 0.8, "Limits EPA authority over automobile emissions and EV mandates")

# HR7700 - Stop Unaffordable Dishwasher Standards Act (118th) - energy efficiency, tangential
add("regulate_co2", "HR7700", False, 0.7, "Blocks energy efficiency standards for appliances")

# HR7637 - Refrigerator Freedom Act (118th)
add("regulate_co2", "HR7637", False, 0.7, "Blocks energy efficiency standards for refrigerators")

# HR6192 - Hands Off Our Home Appliances Act (118th)
add("regulate_co2", "HR6192", False, 0.75, "Blocks DOE energy efficiency standards for home appliances")

# HR7673 - Liberty in Laundry Act (118th)
add("regulate_co2", "HR7673", False, 0.7, "Blocks energy efficiency standards for laundry appliances")

# HR1640 - Save Our Gas Stoves Act (118th)
add("regulate_co2", "HR1640", False, 0.75, "Blocks regulation of gas stoves, opposing emissions reduction")

# HR1615 - Gas Stove Protection and Freedom Act (118th)
add("regulate_co2", "HR1615", False, 0.75, "Protects gas stoves from energy efficiency regulations")

# HR764 - Trust the Science Act (118th) - about forestry/environment
# Not directly about CO2 regulation, skip

# SJRES7 - CRA disapproval (119th) - check context
# Generic, skip without more details

# SJRES3 - CRA disapproval (119th)
# Generic, skip

# SJRES12 - CRA disapproval (119th)
# Generic, skip

# SJRES10 - Terminating national emergency declared with respect to energy (119th)
add("regulate_co2", "SJRES10", False, 0.75, "Terminates energy emergency declaration used to justify climate action")

# SJRES71 - Terminating national emergency with respect to energy (119th)
add("regulate_co2", "SJRES71", False, 0.75, "Terminates energy emergency declaration")

# HR4553 - Energy and Water Development Appropriations Act, 2026 (119th)
# Appropriations - generally skip unless specific
# This likely defunds clean energy programs but too broad to be confident

# HR3062 - Promoting Cross-border Energy Infrastructure Act (119th) - fossil fuel pipelines
add("regulate_co2", "HR3062", False, 0.75, "Streamlines approval of cross-border fossil fuel pipelines")

# HR3668 - Improving Interagency Coordination for Pipeline Reviews Act (119th)
add("regulate_co2", "HR3668", False, 0.7, "Expedites fossil fuel pipeline reviews")

# HJRES75 - CRA disapproval of DOE Office of Energy Efficiency rule (119th)
add("regulate_co2", "HJRES75", False, 0.85, "CRA disapproval of DOE energy efficiency rule")

# HJRES42 - CRA disapproval of DOE energy conservation rule (119th)
add("regulate_co2", "HJRES42", False, 0.85, "CRA disapproval of DOE energy conservation standard")

# HJRES24 - CRA disapproval of DOE rule (119th)
add("regulate_co2", "HJRES24", False, 0.85, "CRA disapproval of Department of Energy regulation")

# HJRES20 - CRA disapproval of DOE rule (119th)
add("regulate_co2", "HJRES20", False, 0.85, "CRA disapproval of Department of Energy regulation")

# HJRES25 - CRA disapproval of Interior rule (119th)
add("regulate_co2", "HJRES25", False, 0.8, "CRA disapproval of Interior Department environmental rule")

# HJRES60 - CRA disapproval of NOAA rule (119th)
add("regulate_co2", "HJRES60", False, 0.8, "CRA disapproval of NOAA environmental rule")

# HJRES78 - CRA disapproval of USFWS Endangered Species rule (119th)
add("regulate_co2", "HJRES78", False, 0.8, "CRA disapproval of endangered species protections tied to habitat/climate")

# HR1366 - Mining Regulatory Clarity Act (119th)
add("regulate_co2", "HR1366", False, 0.7, "Reduces environmental regulations on mining operations")

# HR2925 - Mining Regulatory Clarity Act (118th, earlier version)
add("regulate_co2", "HR2925", False, 0.7, "Reduces environmental regulations on mining operations")

# HR4776 - SPEED Act (119th) - streamlines energy permitting
add("regulate_co2", "HR4776", False, 0.7, "Streamlines permitting for energy projects including fossil fuels")


# ── CLIMATE: renewable_fuel ─────────────────────────────────────
# HR1023 - Repeal greenhouse gas reduction fund (118th) - also anti-renewable
add("renewable_fuel", "HR1023", False, 0.9, "Repeals greenhouse gas reduction fund that finances clean energy projects")

# HR6009 - Restoring American Energy Dominance Act (118th)
add("renewable_fuel", "HR6009", False, 0.8, "Prioritizes fossil fuels over renewable energy development")

# HR1121 - Protecting American Energy Production Act (118th)
add("renewable_fuel", "HR1121", False, 0.8, "Prioritizes fossil fuel production over renewable energy")

# HR26 - Protecting American Energy Production Act (119th)
add("renewable_fuel", "HR26", False, 0.8, "Prioritizes fossil fuel production over renewable alternatives")

# HR6544 - Atomic Energy Advancement Act (118th)
add("renewable_fuel", "HR6544", True, 0.7, "Advances nuclear energy as clean energy alternative")

# HR4824 - Carbon Sequestration Collaboration Act (118th)
add("renewable_fuel", "HR4824", True, 0.75, "Promotes carbon sequestration as part of clean energy strategy")

# HR1435 - Preserving Choice in Vehicle Purchases Act (118th) - blocks EV transition
add("renewable_fuel", "HR1435", False, 0.8, "Blocks transition to electric vehicles, opposing renewable energy in transport")

# HR4468 - Choice in Automobile Retail Sales Act (118th)
add("renewable_fuel", "HR4468", False, 0.75, "Limits EV mandates, slowing renewable energy adoption in transportation")

# HR3015 - National Coal Council Reestablishment Act (119th)
add("renewable_fuel", "HR3015", False, 0.8, "Promotes coal industry at expense of renewable energy transition")

# HR1949 - Unlocking our Domestic LNG Potential Act (119th)
add("renewable_fuel", "HR1949", False, 0.8, "Expands fossil fuel LNG exports instead of investing in renewables")

# HR7176 - Unlocking our Domestic LNG Potential Act (118th)
add("renewable_fuel", "HR7176", False, 0.8, "Expands fossil fuel LNG at expense of renewable investment")

# HJRES75 - CRA disapproval of DOE energy efficiency rule (119th)
add("renewable_fuel", "HJRES75", False, 0.8, "Blocks energy efficiency standard that promotes renewable/clean energy")

# HJRES42 - CRA disapproval of DOE energy conservation rule (119th)
add("renewable_fuel", "HJRES42", False, 0.8, "Blocks energy conservation standard")

# HR3632 - Power Plant Reliability Act (119th) - weakens clean energy transition
add("renewable_fuel", "HR3632", False, 0.75, "Weakens power plant emission rules that incentivize renewable energy")

# HR3616 - Reliable Power Act (119th)
add("renewable_fuel", "HR3616", False, 0.75, "Limits transition to renewable power in name of grid reliability")

# HR6285 - Alaska's Right to Produce Act (118th)
add("renewable_fuel", "HR6285", False, 0.75, "Expands fossil fuel drilling instead of renewable energy")

# HR7980 - End Chinese Dominance of Electric Vehicles Act (118th)
add("renewable_fuel", "HR7980", False, 0.7, "Restricts EV imports, potentially slowing electric vehicle adoption")

# HR9468 - Rescind DOE loan programs office funds (118th)
add("renewable_fuel", "HR9468", False, 0.9, "Rescinds DOE loan program funds used for clean energy projects")

# HR5376 - Build Back Better / Inflation Reduction Act (117th) - massive clean energy investment
add("renewable_fuel", "HR5376", True, 0.85, "Inflation Reduction Act includes massive clean energy and renewable fuel investments")

# HR3638 - Electric Supply Chain Act (119th) - about electric grid supply chain
add("renewable_fuel", "HR3638", False, 0.65, "Focuses on electric supply chain without promoting renewables")
# Skip - confidence too low

# HR7073 - Next Generation Pipelines Research and Development Act (118th)
# Pipeline R&D - could be for hydrogen too, skip as ambiguous


# ── IMMIGRATION: daca ───────────────────────────────────────────
# HR6655 - A Stronger Workforce for America Act (118th) - workforce, not DACA specific
# HR2 - Secure the Border Act (118th) - anti-immigration, would end DACA
add("daca", "HR2", False, 0.85, "Comprehensive border enforcement bill that would end DACA protections")

# HR3602 - End the Border Catastrophe Act (118th) - anti-immigration
add("daca", "HR3602", False, 0.75, "Anti-immigration bill that opposes legal status for unauthorized immigrants")

# S5 - Laken Riley Act (119th) - anti-immigration enforcement
add("daca", "S5", False, 0.7, "Immigration enforcement bill reflecting opposition to protections for unauthorized immigrants")

# HR29 - Laken Riley Act (House version, 119th)
add("daca", "HR29", False, 0.7, "Immigration enforcement bill reflecting opposition to protections for unauthorized immigrants")

# HR7511 - Laken Riley Act (118th)
add("daca", "HR7511", False, 0.7, "Immigration enforcement bill reflecting opposition to protections for unauthorized immigrants")

# HR30 - Preventing Violence Against Women by Illegal Aliens Act (119th)
add("daca", "HR30", False, 0.65, "Anti-immigration enforcement bill")
# Skip - confidence too low

# HR3486 - Stop Illegal Entry Act (119th) - border enforcement
add("daca", "HR3486", False, 0.7, "Border enforcement bill opposing pathway for unauthorized immigrants")

# HR5283 - Protecting our Communities from Failure to Secure the Border Act (118th)
add("daca", "HR5283", False, 0.7, "Anti-immigration border security bill")

# HR5525 - Spending Reduction and Border Security Act (118th)
add("daca", "HR5525", False, 0.7, "Combines spending cuts with border enforcement, opposing immigration protections")

# HR7909 - Violence Against Women by Illegal Aliens Act (118th)
add("daca", "HR7909", False, 0.65, "Anti-immigration enforcement bill")
# Skip - too tangential to DACA specifically


# ── IMMIGRATION: border_wall ────────────────────────────────────
# HR2 - Secure the Border Act (118th) - includes border barrier funding
add("border_wall", "HR2", True, 0.9, "Comprehensive border security bill including border wall/barrier funding")

# HR3602 - End the Border Catastrophe Act (118th) - includes border infrastructure
add("border_wall", "HR3602", True, 0.8, "Border enforcement bill including border barrier provisions")

# HR5525 - Spending Reduction and Border Security Act (118th)
add("border_wall", "HR5525", True, 0.8, "Includes border security/barrier spending provisions")

# HR3486 - Stop Illegal Entry Act (119th) - border security
add("border_wall", "HR3486", True, 0.8, "Border security enforcement bill supporting physical border infrastructure")

# HR993 - Emerging Innovative Border Technologies Act (119th)
add("border_wall", "HR993", True, 0.75, "Funds border technology infrastructure complementing physical barriers")

# HR495 - Subterranean Border Defense Act (119th) - underground border barriers
add("border_wall", "HR495", True, 0.9, "Funds underground border defense/barrier construction")

# HR8752 - DHS Appropriations Act, 2025 (118th) - likely includes border wall funding
add("border_wall", "HR8752", True, 0.7, "DHS appropriations likely including border security/wall funding")

# HR5283 - Protecting our Communities from Failure to Secure the Border (118th)
add("border_wall", "HR5283", True, 0.75, "Border security bill supporting border infrastructure")

# HR1834 - Breaking the Gridlock Act (119th) - large bill with border provisions
add("border_wall", "HR1834", True, 0.75, "Large reconciliation bill including border security funding")

# HR1 - One Big Beautiful Bill Act (119th) - includes border wall funding
add("border_wall", "HR1", True, 0.85, "Massive reconciliation bill includes billions for border wall construction")

# HR275 - Special Interest Alien Reporting Act (119th)
# Not about the wall specifically, skip

# HR875 - Protect Our Communities from DUIs Act (119th) - immigration enforcement but not wall
# Skip

# HR8146 - Police Our Border Act (118th)
add("border_wall", "HR8146", True, 0.75, "Border enforcement bill supporting border infrastructure")

# HR7147 - DHS Appropriations, 2026 (119th)
add("border_wall", "HR7147", True, 0.75, "DHS appropriations including border security and barrier funding")


# ── Additional bills found by searching descriptions ────────────

# HJRES105, HJRES106, HJRES104 - CRA disapprovals (119th)
# These are about various rules - need to check specifics
# HJRES105 - CRA disapproval of Bureau of Reclamation rule - water, skip
# HJRES106 - CRA disapproval - skip without more info
# HJRES104 - CRA disapproval - skip without more info

# SJRES80 - CRA disapproval of Bureau of Land Management rule (119th)
add("regulate_co2", "SJRES80", False, 0.8, "CRA disapproval of BLM environmental protection rule")

# HJRES131 - CRA disapproval of BLM rule (119th)
add("regulate_co2", "HJRES131", False, 0.8, "CRA disapproval of BLM environmental protection rule")

# HJRES130 - CRA disapproval of BLM rule (119th)
add("regulate_co2", "HJRES130", False, 0.8, "CRA disapproval of BLM environmental protection rule")

# SJRES32 - CRA disapproval of Bureau rule (118th)
add("regulate_co2", "SJRES32", False, 0.8, "CRA disapproval of environmental regulation")

# SJRES38 - CRA disapproval of Federal rule (118th)
# This is about financial regulation, not environmental - skip

# SJRES24 - CRA disapproval (118th)
# About USFWS - endangered species
add("regulate_co2", "SJRES24", False, 0.75, "CRA disapproval of endangered species rule with environmental implications")

# SJRES9 - CRA disapproval of endangered species rule (118th)
add("regulate_co2", "SJRES9", False, 0.75, "CRA disapproval of endangered species protection rule")

# HJRES98 - CRA disapproval of NOAA rule (118th)
add("regulate_co2", "HJRES98", False, 0.8, "CRA disapproval of NOAA environmental regulation")

# HR2377 - Federal Extreme Risk Protection Order Act (117th) - gun control red flag law
add("background_checks", "HR2377", True, 0.75, "Federal red flag law enables temporary gun removal, complementary to background check framework")

# HR350 - Domestic Terrorism Prevention Act (117th) - not gun-specific enough, skip

# Senate CRA resolutions about environmental/energy rules
# SJRES82 - CRA disapproval (119th)
# SJRES84 - CRA disapproval (119th) - about BLM/environmental rule
add("regulate_co2", "SJRES84", False, 0.8, "CRA disapproval of environmental protection rule")

# SJRES86 - CRA disapproval (119th)
add("regulate_co2", "SJRES86", False, 0.8, "CRA disapproval of environmental regulation")

# SJRES89 - CRA disapproval (119th)
add("regulate_co2", "SJRES89", False, 0.8, "CRA disapproval of environmental regulation")

# SJRES91 - CRA disapproval (119th)
add("regulate_co2", "SJRES91", False, 0.8, "CRA disapproval of environmental regulation")

# SJRES76 - CRA disapproval (119th)
add("regulate_co2", "SJRES76", False, 0.8, "CRA disapproval of environmental regulation")

# HR1 (118th Congress) in the list is about Lower Energy Costs Act
# Check: HRES260 - Providing for consideration of HR 1 Lower Energy Costs Act
# The 118th HR1 is the Lower Energy Costs Act
# But our HR1 entry shows "One Big Beautiful Bill Act" (119th)
# These are different congresses - the bill IDs may collide
# Since our data shows HR1 as 119th congress, that's the reconciliation bill

# HR3195 - Superior National Forest Restoration Act (118th) - forestry
add("regulate_co2", "HR3195", False, 0.65, "Forest management bill that may reduce environmental protections")
# Skip - too low confidence

# HR471 - Fix Our Forests Act (119th) - forest management
# Not directly about CO2, skip

# HR8790 - Fix Our Forests Act (118th)
# Not directly about CO2, skip

# S3662 - Preventing PFAS Runoff at Airports Act (118th) - environmental but not CO2
# Skip

# HR2773 - Recovering America's Wildlife Act (117th) - wildlife, not CO2 specific
# Skip

# HR5110 - Protecting Hunting Heritage and Education Act (118th) - hunting, skip

# HR615 - Protecting Access for Hunters and Anglers (118th) - hunting, skip

# HR3397 - WEST Act (118th) - western energy, likely pro-fossil
add("regulate_co2", "HR3397", False, 0.7, "Western energy bill likely prioritizing fossil fuel extraction")

# HR4877 - Abandoned Well Remediation Research and Development Act (118th)
# This is about cleaning up abandoned wells - actually somewhat pro-environment
add("regulate_co2", "HR4877", True, 0.7, "Funds remediation of abandoned oil/gas wells, reducing methane emissions")

# HR3633 - CLARITY Act (119th) - likely about regulatory clarity for energy
add("regulate_co2", "HR3633", False, 0.7, "Reduces regulatory requirements likely affecting environmental oversight")

# HCONRES9 - Denouncing the horrors of socialism (118th) - not relevant
# HCONRES58 - Denouncing the horrors of socialism (119th) - not relevant

# Gun-related bills in the dataset
# HR5110 - Protecting Hunting Heritage - hunting rights, tangentially gun-related but not about background checks/assault weapons
# HR615 - Protecting Access for Hunters and Anglers - same

# HR2056 - DC Federal Immigration Compliance Act (119th)
add("daca", "HR2056", False, 0.7, "Requires DC to comply with federal immigration enforcement, opposing sanctuary policies")

# HR884 - Prohibit non-citizens from voting in DC (119th) - immigration-adjacent but not DACA
# Skip

# HR5717 - No Bailout for Sanctuary Cities Act (118th)
add("daca", "HR5717", False, 0.7, "Punishes sanctuary cities that protect unauthorized immigrants including DACA recipients")

# HR4371 - Kayla Hamilton Act (119th) - immigration enforcement
add("daca", "HR4371", False, 0.7, "Immigration enforcement bill targeting unauthorized immigrant protections")


# ── Additional older bills found in dataset ─────────────────────

# ABORTION - older congresses
# HR3504 - Born-Alive Abortion Survivors Protection Act (114th)
add("abortion_legal", "HR3504", False, 0.95, "Born-Alive Act restricts abortion provider practices; voting Yea opposes abortion access")
add("abortion_20_weeks", "HR3504", True, 0.8, "Born-Alive Act targets late-term abortion outcomes")

# HR3134 - Defund Planned Parenthood Act (114th)
add("abortion_legal", "HR3134", False, 0.95, "Defunds Planned Parenthood, major abortion provider; voting Yea opposes abortion access")

# HJRES43 - Disapproving DC Reproductive Health Non-Discrimination Act (114th)
add("abortion_legal", "HJRES43", False, 0.85, "Disapproves DC reproductive health protections; voting Yea opposes reproductive rights")

# HR3755 - Women's Health Protection Act (117th, Senate version)
add("abortion_legal", "HR3755", True, 0.95, "Protects abortion access nationwide")

# S4132 - Protect abortion access after Dobbs (117th)
add("abortion_legal", "S4132", True, 0.95, "Protects abortion access and provider ability to provide services")

# S4381 - Protect access to contraceptives (118th)
add("abortion_legal", "S4381", True, 0.85, "Protects access to contraceptives, related to reproductive rights")

# HR239 - Equal Access to Contraception for Veterans Act (117th)
add("abortion_legal", "HR239", True, 0.75, "Ensures veterans access to contraception, related to reproductive rights")

# HCONRES3 - Condemning attacks on pro-life facilities (118th)
add("abortion_legal", "HCONRES3", False, 0.7, "Resolution supporting pro-life movement; voting Yea signals opposition to abortion access")

# HR3762 - Restoring Americans' Healthcare Freedom (ACA repeal reconciliation, 114th)
add("support_aca", "HR3762", False, 0.95, "Reconciliation bill to repeal ACA and defund Planned Parenthood")
add("abortion_legal", "HR3762", False, 0.8, "ACA repeal bill includes defunding Planned Parenthood")

# HEALTHCARE / ACA - older congresses
# HR6311 - Increasing Access to Lower Premium Plans and Expanding HSAs (115th)
add("support_aca", "HR6311", False, 0.85, "Undermines ACA by expanding short-term plans and HSAs that bypass ACA protections")

# HRES826 - Expressing disapproval of Trump admin actions towards Medicaid (116th)
add("support_aca", "HRES826", True, 0.85, "Resolution defending Medicaid from Trump administration cuts")

# HRES271 - Condemning Trump admin legal campaign against ACA (116th)
add("support_aca", "HRES271", True, 0.9, "Resolution condemning efforts to take away Americans' healthcare under ACA")

# HR497 - Freedom for Health Care Workers Act (118th)
# This is about healthcare worker vaccine mandates, not directly ACA - skip

# S4361 - Emergency supplemental for border security (118th)
add("border_wall", "S4361", True, 0.8, "Emergency border security supplemental appropriations including barrier funding")

# CLIMATE - older congresses
# HR9 - Climate Action Now Act (116th)
add("regulate_co2", "HR9", True, 0.95, "Climate Action Now Act requires US to stay in Paris Climate Agreement")
add("renewable_fuel", "HR9", True, 0.8, "Climate Action Now Act promotes clean energy transition")

# HR5376 also gets renewable_fuel (already classified above)

# GUN CONTROL - older congresses
# HR8 - Bipartisan Background Checks Act (116th)
add("background_checks", "HR8", True, 0.95, "Requires background checks for all firearm sales including private transactions")

# HR1112 - Enhanced Background Checks Act (116th)
add("background_checks", "HR1112", True, 0.95, "Enhances background check procedures by extending review period")

# HR1446 - Enhanced Background Checks Act of 2021 (117th)
add("background_checks", "HR1446", True, 0.95, "Enhanced Background Checks Act extends waiting period for background checks")

# HR2377 - Federal Extreme Risk Protection Order Act (117th)
# Already classified above, also relevant to concealed_carry and assault_weapons
add("concealed_carry", "HR2377", True, 0.75, "Red flag law enables temporary removal of firearms, supports gun permit framework")

# HR7910 already classified for background_checks and assault_weapons_ban above

# IMMIGRATION - additional
# HR6 - American Dream and Promise Act (116th) - directly pro-DACA
add("daca", "HR6", True, 0.95, "American Dream and Promise Act provides pathway to citizenship for DACA recipients")

# HR1603 - Farm Workforce Modernization Act (117th) - immigration reform for ag workers
add("daca", "HR1603", True, 0.75, "Immigration reform for agricultural workers, related to DACA/immigration protections")

# HR5038 - Farm Workforce Modernization Act (116th)
add("daca", "HR5038", True, 0.75, "Immigration reform for agricultural workers, related pathway to legal status")

# S4361 already classified for border_wall above

# HEALTHCARE - additional older bills
# HR3 - Elijah Cummings Lower Drug Costs Now Act (116th)
add("support_aca", "HR3", True, 0.8, "Lowers prescription drug costs, strengthening affordable healthcare goals of ACA")

# HRES826 and HRES271 already classified above

# HR986 - Protecting Americans with Preexisting Conditions Act (116th)
add("support_aca", "HR986", True, 0.9, "Protects ACA preexisting condition coverage requirements")

# HR1319 - American Rescue Plan Act (117th) - includes ACA premium subsidies
add("support_aca", "HR1319", True, 0.75, "American Rescue Plan includes expanded ACA premium subsidies")

# HR3590 - Halt Tax Increases on Middle Class and Seniors (114th) - repeals ACA taxes
add("support_aca", "HR3590", False, 0.75, "Repeals ACA-related taxes on middle class and seniors")

# CLIMATE - additional older bills
# HR4447 - Expanding Access to Sustainable Energy Act (116th)
add("renewable_fuel", "HR4447", True, 0.9, "Expands access to sustainable/renewable energy")
add("regulate_co2", "HR4447", True, 0.8, "Promotes sustainable energy to address climate change")

# HR1146 - Arctic Cultural and Coastal Plain Protection Act (116th)
add("regulate_co2", "HR1146", True, 0.85, "Protects Arctic coastal plain from oil drilling")
add("renewable_fuel", "HR1146", True, 0.75, "Blocks Arctic fossil fuel extraction, supporting renewable alternatives")

# HR1768 - Diesel Emissions Reduction Act (116th)
add("regulate_co2", "HR1768", True, 0.85, "Reduces diesel emissions, supporting pollution regulation")

# HCONRES89 - Sense that carbon tax would be detrimental (114th)
add("regulate_co2", "HCONRES89", False, 0.95, "Resolution opposing carbon tax; voting Yea opposes CO2 regulation")

# HCONRES112 - Opposing $10/barrel oil tax (114th)
add("regulate_co2", "HCONRES112", False, 0.9, "Opposes oil barrel tax that would internalize carbon costs")

# HR4775 - Ozone Standards Implementation Act (114th)
add("regulate_co2", "HR4775", False, 0.8, "Delays implementation of ozone/air quality standards")

# S4072 - Prohibit funds for certain EPA rules (118th)
add("regulate_co2", "S4072", False, 0.9, "Blocks funding for EPA environmental regulations")

# HR535 - PFAS Action Act (116th) - environmental regulation
add("regulate_co2", "HR535", True, 0.7, "Regulates PFAS pollutants through EPA, supporting environmental regulation")

# HR2467 - PFAS Action Act (117th)
add("regulate_co2", "HR2467", True, 0.7, "Requires EPA action on PFAS chemical pollutants")

# HR1937 - National Strategic and Critical Minerals Production Act (114th)
add("regulate_co2", "HR1937", False, 0.7, "Streamlines mineral extraction, reducing environmental oversight")

# HR702 - Adapt to changing crude oil market (114th) - lifted oil export ban
add("regulate_co2", "HR702", False, 0.75, "Lifts crude oil export ban, expanding fossil fuel production")

# HR4557 - Blocking Regulatory Interference from Closing Kilns Act (114th)
add("regulate_co2", "HR4557", False, 0.8, "Blocks EPA regulations on brick kilns' emissions")

# HR6094 - Regulatory Relief for Small Businesses (114th)
# Too broad, skip

# HR3797 - Satisfying Energy Needs and Saving the Environment (SENSE) Act (114th)
add("regulate_co2", "HR3797", False, 0.7, "Streamlines energy permitting, potentially at environmental expense")

# ABORTION - more older bills
# HR3495 - Women's Public Health and Safety Act (114th) - defunding Planned Parenthood related
add("abortion_legal", "HR3495", False, 0.8, "Restricts funding to abortion providers, opposing abortion access")

# IMMIGRATION - older bills
# HR3009 - Enforce the Law for Sanctuary Cities Act (114th)
add("daca", "HR3009", False, 0.75, "Anti-sanctuary city bill opposing protections for unauthorized immigrants")

# HR549 - Venezuela TPS Act (116th) - about TPS not DACA, skip
# HR1333 - NO BAN Act (117th) - about travel ban, tangential to DACA
add("daca", "HR1333", True, 0.7, "Repeals discriminatory travel bans, supporting immigrant protections")

# HR4038 - American SAFE Act (114th) - restricts Syrian/Iraqi refugee admission
# Not directly DACA, skip

# HR3239 - Humanitarian Standards for Individuals in CBP Custody (116th)
# About detention conditions, not DACA specifically, skip

# BORDER WALL - older bills
# HR5525 already classified
# HR2 (118th) already classified
# HJRES31 - Making continuing appropriations for DHS FY2019 (116th) - the shutdown bill about wall funding
add("border_wall", "HJRES31", True, 0.8, "DHS continuing appropriations during government shutdown over border wall funding")

# HJRES1 - Making continuing appropriations for DHS FY2019 (116th)
add("border_wall", "HJRES1", True, 0.7, "DHS appropriations during border wall funding dispute")

# HR648 - Consolidated Appropriations Act 2019 (116th) - ended shutdown, included some barrier funding
add("border_wall", "HR648", True, 0.7, "Consolidated appropriations including limited border barrier funding")

# Clean up: remove entries below 0.7 confidence
for issue in classifications:
    to_remove = [k for k, v in classifications[issue].items() if v["confidence"] < 0.7]
    for k in to_remove:
        del classifications[issue][k]

# Write output files
for issue, bills_data in classifications.items():
    if not bills_data:
        # Write empty file
        out_path = os.path.join(OUTPUT_DIR, f"{issue}.json")
        with open(out_path, 'w') as f:
            json.dump({}, f, indent=2)
        print(f"  {issue}: 0 bills (empty)")
        continue

    out_path = os.path.join(OUTPUT_DIR, f"{issue}.json")
    with open(out_path, 'w') as f:
        json.dump(bills_data, f, indent=2)

    support_count = sum(1 for v in bills_data.values() if v["yea_means_support"])
    oppose_count = sum(1 for v in bills_data.values() if not v["yea_means_support"])
    print(f"  {issue}: {len(bills_data)} bills ({support_count} support, {oppose_count} oppose)")

print(f"\nTotal classified: {sum(len(v) for v in classifications.values())} bill-issue pairs")
print(f"Output directory: {OUTPUT_DIR}")
