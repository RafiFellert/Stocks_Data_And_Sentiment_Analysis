from datetime import datetime, timedelta
import yfinance as yf
import pandas as pd
import numpy as np

# 1. Defining range of dates for data collection
start_date = "<YYYY-MM-DD>"
end_date = "<YYYY-MM-DD>"

# 2. Defining the target stock
ticker = "<TICKER_NAME>"

# 3. Downloading data from yahoo finance
print(f"Downloading data for {ticker}...")
df_prices = yf.download(ticker, start=start_date, end=end_date)

# 4. Modifying the MultiIndex to columns (handles newer yfinance formats)
if isinstance(df_prices.columns, pd.MultiIndex):
    df_prices.columns = df_prices.columns.get_level_values(0)

# 5. Extracting and formatting the date
df_prices = df_prices.reset_index()
df_prices['Date'] = pd.to_datetime(df_prices['Date']).dt.strftime('%Y-%m-%d')

# 6. Selecting only the desired columns (Fixed df_prices -> df_final)
export_columns = ['Date', 'Open', 'Close', 'Volume']
df_final = df_prices[export_columns]

# 7. Sorting by date (ascending)
df_final = df_final.sort_values(by='Date', ascending=True)

# 8. Exporting to excel file
filename = f"{ticker}_daily_prices.xlsx"
df_final.to_excel(filename, index=False, sheet_name=f"{ticker} Data")
print(f"The new file was saved as: {filename}")
