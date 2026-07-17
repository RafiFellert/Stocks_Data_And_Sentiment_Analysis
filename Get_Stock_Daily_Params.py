import yfinance as yf
import pandas as pd

# Parameters
ticker = "MXL"
start_date = "2016-01-15"
end_date = "2016-02-15"

# Download stock data
df = yf.download(ticker, start=start_date, end=end_date)

# Flatten columns if needed
if isinstance(df.columns, pd.MultiIndex):
    df.columns = df.columns.get_level_values(0)

# Keep only the required columns
df = df.reset_index()[["Date", "Open", "Close", "Volume"]]

# Rename columns
df.rename(columns={
    "Open": "Start Price",
    "Close": "End Price"
}, inplace=True)

# Format the date
df["Date"] = df["Date"].dt.strftime("%Y-%m-%d")

# Sort newest first (optional)
df = df.sort_values("Date", ascending=False)

# Save to Excel
filename = f"{ticker}_prices.xlsx"
df.to_excel(filename, index=False)

print(df)
print(f"\nSaved to {filename}")
