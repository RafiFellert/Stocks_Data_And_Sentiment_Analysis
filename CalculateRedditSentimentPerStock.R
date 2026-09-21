# Auto-install missing packages
required_packages <- c("dplyr", "tidyr", "sentimentr", "lexicon", "writexl", "tidytext", "syuzhet", "textdata")
new_packages <- required_packages[!(required_packages %in% installed.packages()[,"Package"])]
if (length(new_packages) > 0) install.packages(new_packages)

library(dplyr)
library(tidyr)
library(sentimentr)
library(lexicon)
library(writexl)
library(tidytext)
library(syuzhet)
library(textdata)

# Load the dataset
setwd("C:/Users/felle/Documents/Rafi/seminar/MGRT")
csv_file <- list.files(pattern = "\\.csv$", full.names = TRUE)[1]
reddit_data <- read.csv(csv_file, stringsAsFactors = FALSE, fileEncoding = "UTF-8")

# Parse date, handle missing values, and assign a unique element_id per row
reddit_data <- reddit_data %>%
  mutate(
    date_posted_parsed = as.POSIXct(date_posted, format = "%Y-%m-%dT%H:%M:%OSZ", tz = "UTC"),
    post_date          = as.Date(date_posted_parsed),
    title              = replace_na(title, ""),
    description        = replace_na(description, ""),
    num_upvotes        = replace_na(as.numeric(num_upvotes), 0),
    Full_Text          = trimws(paste(title, description, sep = " "))
  ) %>%
  arrange(date_posted_parsed) %>%
  mutate(element_id = row_number()) # Unique row identifier

# ----------------------------------------------------
# 1. Calculate Sentiment using element_id Grouping
# ----------------------------------------------------
baseline_sentiment <- sentiment_by(reddit_data$Full_Text, by = reddit_data$element_id)

lm_hash <- lexicon::hash_sentiment_loughran_mcdonald
financial_sentiment <- sentiment_by(reddit_data$Full_Text, by = reddit_data$element_id, polarity_dt = lm_hash)

# Safe Min-Max Scaling [-1, 1]
rescale_sentiment <- function(x, new_min = -1, new_max = 1) {
  rng <- range(x, na.rm = TRUE)
  if (is.na(rng[1]) || rng[1] == rng[2]) return(rep(0, length(x)))
  (x - rng[1]) / (rng[2] - rng[1]) * (new_max - new_min) + new_min
}

# ----------------------------------------------------
# 2. Key-based Join Back to Dataset
# ----------------------------------------------------
reddit_data <- reddit_data %>%
  left_join(
    baseline_sentiment %>% select(element_id, word_count, baseline_raw = ave_sentiment),
    by = "element_id"
  ) %>%
  left_join(
    financial_sentiment %>% select(element_id, financial_raw = ave_sentiment),
    by = "element_id"
  ) %>%
  mutate(
    financial_score = rescale_sentiment(financial_raw)
  )

# ----------------------------------------------------
# 3. Post Weights & Upvote-Weighted Financial Sentiment
# ----------------------------------------------------
reddit_data <- reddit_data %>%
  group_by(post_date) %>%
  mutate(
    daily_total_upvotes = sum(num_upvotes, na.rm = TRUE),
    upvote_weight = if_else(
      daily_total_upvotes > 0, 
      num_upvotes / daily_total_upvotes, 
      1 / n()
    ),
    weighted_financial_raw   = financial_raw * upvote_weight,
    weighted_financial_score = financial_score * upvote_weight,
    daily_aggregate_score    = sum(weighted_financial_score, na.rm = TRUE)  # Added daily aggregate score to post-level data
  ) %>%
  ungroup()

# ----------------------------------------------------
# 4. Daily Aggregation
# ----------------------------------------------------
daily_sentiment_summary <- reddit_data %>%
  group_by(post_date) %>%
  summarise(
    total_posts           = n(),
    total_upvotes         = sum(num_upvotes, na.rm = TRUE),
    daily_financial_raw   = sum(weighted_financial_raw, na.rm = TRUE),
    daily_financial_score = sum(weighted_financial_score, na.rm = TRUE),
    daily_aggregate_financial_score = sum(weighted_financial_score, na.rm = TRUE),  # Explicitly named in daily summary
    .groups = "drop"
  )

# ----------------------------------------------------
# 5. Export Results
# ----------------------------------------------------
write_xlsx(
  list(
    "Post_Level_Scores"            = reddit_data,
    "Daily_financial_Aggregated"   = daily_sentiment_summary
  ),
  path = "MGRT_oct_2025_reddit_scored.xlsx"
)
