from datetime import datetime, timedelta
import yfinance as yf
import pandas as pd

# Inputs
ticker = "MXL"
start_dates = [
    "2026-01-15",
    "2026-02-10",
    "2026-03-05"
]

all_data = []

for start_date in start_dates:

    start_dt = datetime.strptime(start_date, "%Y-%m-%d")
    end_dt = start_dt + timedelta(days=2)

    # Download 3-day period
    df = yf.download(
        ticker,
        start=start_dt.strftime("%Y-%m-%d"),
        end=(end_dt + timedelta(days=1)).strftime("%Y-%m-%d"),
        auto_adjust=False
    )

    if df.empty:
        print(f"No data found for {start_date}")
        continue

    # Flatten MultiIndex columns if necessary
    if isinstance(df.columns, pd.MultiIndex):
      df.columns = df.columns.get_level_values(0)

    # Keep only required columns
    df = df[["Open", "Close", "Volume"]].reset_index()

    # Rename columns
    df.rename(columns={
        "Open": "StartPrice",
        "Close": "EndPrice"
    }, inplace=True)

    # Remember which start date generated these rows
    df["RequestedStartDate"] = start_date

    all_data.append(df)

# Combine all periods
final_df = pd.concat(all_data, ignore_index=True)

# Save to Excel
filename = f"{ticker}_multiple_dates.xlsx"
final_df.to_excel(filename, index=False)

print(final_df)
print(f"\nData saved to: {filename}")
