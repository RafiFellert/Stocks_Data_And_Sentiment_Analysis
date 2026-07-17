from datetime import datetime, timedelta
import yfinance as yf

# Inputs
start_date = "2026-01-15"
ticker = "MXL"

# Calculate end date (start date + 2 days)
start_dt = datetime.strptime(start_date, "%Y-%m-%d")
end_dt = start_dt + timedelta(days=2)

# Download stock data
df = yf.download(
    ticker,
    start=start_dt.strftime("%Y-%m-%d"),
    end=(end_dt + timedelta(days=1)).strftime("%Y-%m-%d"),  # end date is exclusive
    auto_adjust=False
)

# Keep only the required columns
df = df[["Open", "Close", "Volume"]].reset_index()

# Rename columns
df.rename(columns={
    "Open": "StartPrice",
    "Close": "EndPrice"
}, inplace=True)

# Save to Excel
filename = f"{ticker}_{start_date}.xlsx"
df.to_excel(filename, index=False)

print(df)
print(f"\nData saved to: {filename}")
