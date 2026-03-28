#!/usr/bin/env Rscript
#
# MRP (Multilevel Regression and Poststratification) pipeline
# Generates district-level opinion estimates from CES survey data.
#
# Usage:
#   Rscript run_mrp.R
#
# Output:
#   district_estimates.csv — one row per district × issue
#

library(lme4)
library(haven)
library(dplyr)
library(tidyr)
library(readr)

cat("=== MRP Pipeline ===\n\n")

# --- Configuration ---
DATA_DIR <- "/Users/benjaminwallace/Desktop/Projects/activism-ideas/01-civic-receipts/scripts/mrp"

YEARS <- 2018:2021  # Use 4 years for larger sample
OUTPUT_FILE <- file.path(DATA_DIR, "district_estimates.csv")

# --- Policy questions to estimate ---
# Format: column_name -> list(label, support_value, description)
QUESTIONS <- list(
  guns_bgchecks = list(
    label = "Universal background checks for gun purchases",
    support_val = 1,
    topic = "Gun Control"
  ),
  guns_assaultban = list(
    label = "Ban on assault-style weapons",
    support_val = 1,
    topic = "Gun Control"
  ),
  abortion_always = list(
    label = "Abortion should always be legal",
    support_val = 1,
    topic = "Abortion"
  ),
  abortion_20weeks = list(
    label = "Prohibit all abortions after 20 weeks",
    support_val = 1,
    topic = "Abortion"
  ),
  healthcare_aca = list(
    label = "Support the Affordable Care Act",
    support_val = 2,  # 1 = repeal ACA, 2 = keep/support ACA
    topic = "Healthcare"
  ),
  enviro_carbon = list(
    label = "Regulate CO2 as a pollutant",
    support_val = 1,
    topic = "Climate"
  ),
  enviro_renewable = list(
    label = "Require minimum renewable fuel production",
    support_val = 1,
    topic = "Climate"
  ),
  immig_legalize = list(
    label = "Grant legal status to DACA recipients",
    support_val = 1,
    topic = "Immigration"
  ),
  immig_wall = list(
    label = "Build a wall on the U.S.-Mexico border",
    support_val = 1,
    topic = "Immigration"
  ),
  guns_permits = list(
    label = "Require permits to carry concealed guns",
    support_val = 2,  # 1 = no permit needed, 2 = require permits
    topic = "Gun Control"
  )
)

# --- Load and prepare data ---
cat("Loading CES data...\n")
ces <- readRDS(file.path(DATA_DIR, "cumulative_2006-2024.rds"))
policy <- read_tsv(file.path(DATA_DIR, "cumulative_ces_policy_preferences.tab"),
                   show_col_types = FALSE)

cat("Joining datasets...\n")
df <- inner_join(ces, policy, by = c("year", "case_id"))

# Filter to recent years
df <- df %>% filter(year %in% YEARS)
cat(sprintf("Using %d respondents from %s\n", nrow(df), paste(YEARS, collapse="-")))

# Convert haven_labelled columns to plain numeric/character
df <- df %>% mutate(across(where(haven::is.labelled), ~ as.numeric(.)))

# --- Prepare demographic variables for MRP ---
df <- df %>%
  mutate(
    # Binary gender (simplification for MRP cells)
    female = as.integer(gender == 2 | sex == 2),
    # Age bins
    age_bin = case_when(
      age < 30 ~ "18-29",
      age < 45 ~ "30-44",
      age < 65 ~ "45-64",
      TRUE ~ "65+"
    ),
    # Education bins
    educ_bin = case_when(
      educ <= 2 ~ "no_college",  # HS or less
      educ <= 4 ~ "some_college",
      TRUE ~ "college_plus"
    ),
    # Race (simplified)
    race_bin = case_when(
      race == 1 ~ "white",
      race == 2 ~ "black",
      race == 3 ~ "hispanic",
      TRUE ~ "other"
    ),
    # State as factor
    state_f = as.factor(st),
    # Congressional district
    cd_clean = cd
  ) %>%
  filter(!is.na(cd_clean), cd_clean != "", !is.na(state_f))

cat(sprintf("After cleaning: %d respondents across %d districts\n",
            nrow(df), length(unique(df$cd_clean))))

# --- Load ACS poststratification table ---
# Uses actual Census population data (ACS 5-year estimates) instead of
# survey respondent demographics. This corrects for selection bias in
# the CES sample (over-representation of college-educated, urban, etc.).
# Run fetch_acs.py first to generate the CSV.
ACS_FILE <- file.path(DATA_DIR, "acs_district_demographics.csv")
if (!file.exists(ACS_FILE)) {
  stop("ACS demographics file not found. Run: python3 scripts/mrp/fetch_acs.py")
}

cat("Loading ACS poststratification table...\n")
ps_table <- read_csv(ACS_FILE, show_col_types = FALSE) %>%
  mutate(
    female = as.integer(female),
    age_bin = as.character(age_bin),
    educ_bin = as.character(educ_bin),
    race_bin = as.character(race_bin),
    # Extract state abbreviation for the state random effect
    state_f = as.factor(sub("-.*", "", cd_clean))
  ) %>%
  filter(population > 0) %>%
  group_by(cd_clean) %>%
  mutate(cell_weight = population / sum(population)) %>%
  ungroup()

cat(sprintf("Poststratification table: %d cells across %d districts\n",
            nrow(ps_table), length(unique(ps_table$cd_clean))))

# --- Load district-level partisan covariate ---
# 2020 Republican two-party vote share by congressional district.
# Adding this as a fixed effect reduces over-smoothing by giving the model
# a strong partisan signal to differentiate districts (Warshaw & Rodden 2012).
PRES_FILE <- file.path(DATA_DIR, "district_pres_vote.csv")
if (!file.exists(PRES_FILE)) {
  stop("Presidential vote share file not found. Run: python3 scripts/mrp/fetch_presidential_votes.py")
}
pres_vote <- read_csv(PRES_FILE, show_col_types = FALSE) %>%
  select(cd_clean, rep_two_party_share)

cat(sprintf("Loaded partisan covariate for %d districts (R vote share: %.1f%% - %.1f%%)\n",
            nrow(pres_vote),
            min(pres_vote$rep_two_party_share) * 100,
            max(pres_vote$rep_two_party_share) * 100))

# Join to survey data and poststratification table
df <- df %>% left_join(pres_vote, by = "cd_clean")
ps_table <- ps_table %>% left_join(pres_vote, by = "cd_clean")

# Drop rows without partisan data (very rare — new/redistricted districts)
n_before <- nrow(df)
df <- df %>% filter(!is.na(rep_two_party_share))
cat(sprintf("  Dropped %d survey rows without partisan data\n", n_before - nrow(df)))

# --- Run MRP for each question ---
results <- tibble()

for (q_name in names(QUESTIONS)) {
  q_info <- QUESTIONS[[q_name]]
  cat(sprintf("\nEstimating: %s (%s)...\n", q_info$label, q_name))

  # Prepare response variable
  q_df <- df %>%
    filter(!is.na(.data[[q_name]])) %>%
    mutate(support = as.integer(.data[[q_name]] == q_info$support_val))

  n_resp <- nrow(q_df)
  if (n_resp < 1000) {
    cat(sprintf("  Skipping: only %d responses\n", n_resp))
    next
  }
  cat(sprintf("  %d respondents, %.1f%% support\n", n_resp, mean(q_df$support) * 100))

  # Fit multilevel logistic regression
  # Random effects for state and congressional district
  # Fixed effects for demographics
  tryCatch({
    model <- glmer(
      support ~ female + age_bin + educ_bin + race_bin + rep_two_party_share +
        (1 | state_f) + (1 | cd_clean) +
        (1 | educ_bin:state_f) + (1 | race_bin:state_f) + (1 | age_bin:state_f),
      data = q_df,
      family = binomial(link = "logit"),
      control = glmerControl(optimizer = "bobyqa", optCtrl = list(maxfun = 100000)),
      nAGQ = 1  # Laplace approximation (more accurate than nAGQ=0)
    )

    cat("  Model fitted successfully\n")

    # Predict for each poststratification cell (with standard errors)
    pred <- predict(model, newdata = ps_table, type = "link",
                    allow.new.levels = TRUE, se.fit = TRUE)
    # Convert from logit scale to probability
    ps_table$pred_prob <- plogis(pred$fit)
    ps_table$pred_se <- pred$se.fit * ps_table$pred_prob * (1 - ps_table$pred_prob)  # delta method

    # Aggregate to district level (weighted by cell size)
    district_est <- ps_table %>%
      filter(!is.na(pred_prob)) %>%
      group_by(cd_clean) %>%
      summarise(
        support_pct = round(weighted.mean(pred_prob, cell_weight, na.rm = TRUE) * 100, 1),
        # Margin of error: pooled SE across cells, scaled to percentage points (95% CI)
        margin_of_error = round(1.96 * sqrt(weighted.mean(pred_se^2, cell_weight, na.rm = TRUE)) * 100, 1),
        n_cells = n(),
        .groups = "drop"
      ) %>%
      mutate(
        # Floor at 3, cap at 12 for reasonable display
        margin_of_error = pmin(pmax(margin_of_error, 3), 12),
        question = q_name,
        label = q_info$label,
        topic = q_info$topic
      )

    results <- bind_rows(results, district_est)
    cat(sprintf("  Generated estimates for %d districts (mean: %.1f%%)\n",
                nrow(district_est), mean(district_est$support_pct)))

  }, error = function(e) {
    cat(sprintf("  ERROR: %s\n", e$message))
  })
}

# --- Save results ---
cat(sprintf("\n=== Writing %d estimates to %s ===\n", nrow(results), OUTPUT_FILE))
write_csv(results, OUTPUT_FILE)

# Show CA districts as a sanity check
cat("\nCA district estimates (sample):\n")
ca_sample <- results %>%
  filter(grepl("^CA-", cd_clean)) %>%
  arrange(question, cd_clean)

for (q in unique(ca_sample$question)) {
  cat(sprintf("\n  %s:\n", q))
  ca_q <- ca_sample %>% filter(question == q)
  for (i in 1:min(5, nrow(ca_q))) {
    cat(sprintf("    %s: %.1f%%\n", ca_q$cd_clean[i], ca_q$support_pct[i]))
  }
}

cat("\nDone!\n")
