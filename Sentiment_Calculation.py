!pip install vaderSentiment
import pandas as pd
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from transformers import pipeline

# ====================================================
# 1. LOAD YOUR FILES
# ====================================================
# Update these file names and column names to match yours exactly
reddit_file = "sample_data/bynd_oct_2025_reddit.xlsx"  # File with your raw Reddit posts
price_file = "sample_data/BYND_daily_prices_oct_2025.xlsx" # File with Volume, Daily_Change, etc.
text_column = 'Content'                   # Name of the column containing the text
ticker = "BYND"

df_reddit = pd.read_excel(reddit_file)
df_price = pd.read_excel(price_file)

# Ensure text data is string format
df_reddit[text_column] = df_reddit[text_column].astype(str).fillna('')

# Format Date columns to the same date format so they match perfectly during merge
df_reddit['Date'] = pd.to_datetime(df_reddit['Date']).dt.date
df_price['Date'] = pd.to_datetime(df_price['Date']).dt.date

# ====================================================
# 2. CALCULATE SENTIMENT SCORES PER POST
# ====================================================
print("Calculating VADER scores...")
vader_analyzer = SentimentIntensityAnalyzer()
df_reddit['VADER_Compound'] = df_reddit[text_column].apply(
    lambda x: vader_analyzer.polarity_scores(x)['compound']
)

# ====================================================
# 3. CALCULATE BERT SENTIMENT (RE-ENGINEERED)
# ====================================================
print("Initializing FinBERT pipeline...")
# Initialize the pipeline cleanly
bert_classifier = pipeline("sentiment-analysis", model="ProsusAI/finbert")

def get_bert_sentiment(text):
    if not text.strip():
        return 0.0
    try:
        # FORCE truncation and max_length directly inside the call step
        result = bert_classifier(text, truncation=True, max_length=512)[0]

        print(f"RAW OUTPUT: {result}")

        label = result['label'].lower()  # .lower() protects against any case mismatches
        score = result['score']

        if label == 'positive':
            return score
        elif label == 'negative':
            return -score
        else:
            return 0.0  # Neutral posts get 0.0

    except Exception as e:
        # This will tell us if any underlying error is actually happening
        print(f"Row failed due to: {e}")
        return 0.0

print("Calculating BERT scores...")
df_reddit['BERT_Score'] = df_reddit[text_column].apply(get_bert_sentiment)

# Confirming it worked
print("\nFirst 5 rows of calculated BERT scores:")
print(df_reddit[[text_column, 'BERT_Score']].head())

# ====================================================
# 4. AGGREGATE TO DAILY AVERAGES
# ====================================================
print("Averaging sentiment scores by date...")
# Group by Date and calculate the mean for both sentiment types
daily_sentiment = df_reddit.groupby('Date')[['VADER_Compound', 'BERT_Score']].mean().reset_index()

# ====================================================
# 5. MERGE DATA INTO A COMMON MASTER FILE
# ====================================================
print("Merging sentiment metrics into your stock price data...")
# Left join ensures you keep all trading days from your price file
master_df = pd.merge(df_price, daily_sentiment, on='Date', how='left')

# Optional: Fill days that had 0 Reddit activity with 0 (Neutral) instead of blank cells
master_df['VADER_Compound'] = master_df['VADER_Compound'].fillna(0)
master_df['BERT_Score'] = master_df['BERT_Score'].fillna(0)

print("\n--- DAYS WITH NON-ZERO SENTIMENT ---")
# Filters out any rows where both VADER and BERT equal 0.0
non_neutral_rows = master_df[(master_df['VADER_Compound'] != 0)]

print(non_neutral_rows.to_string(index=False))
# ====================================================
# 6. SAVE THE FINAL FILE
# ====================================================
output_file = f"{ticker}_master_combined.xlsx"
master_df.to_excel(output_file, index=False)
print(f"Done! Your unified dataset is saved as: {output_file}")
