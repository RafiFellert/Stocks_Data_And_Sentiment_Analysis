import requests
import pandas as pd
from io import StringIO
import time

# ============================================================
# SETTINGS
# ============================================================

API_TOKEN = "<YOUR_FINRA_ACCESS_TOKEN>"
TICKER = "<TICKER_NAME>"

START_DATE = "<YYYY-MM-DD>"
END_DATE   = "<YYYY-MM-DD>"

URL = (
    "https://api.finra.org/data/"
    "group/otcMarket/name/consolidatedShortInterest"
)

HEADERS = {
    "Authorization": f"Bearer {API_TOKEN}",
    "Data-API-Version": "1"
}


# ============================================================
# GET ONE DATE
# ============================================================

def get_short_interest_date(date):

    payload = {
        "limit": 100,
        "offset": 0,
        "compareFilters": [
            {
                "compareType": "equal",
                "fieldName": "settlementDate",
                "fieldValue": date
            },
            {
                "compareType": "equal",
                "fieldName": "symbolCode",
                "fieldValue": TICKER
            }
        ]
    }

    r = requests.post(
        URL,
        json=payload,
        headers=HEADERS,
        timeout=30
    )

    if r.status_code == 204:
        print(f"Downloading: {date} -> HTTP 204 (No data)")
        return pd.DataFrame()

    print(f"Downloading: {date} -> HTTP {r.status_code}")

    if r.status_code != 200:
        print(r.text[:1000])
        return pd.DataFrame()

    try:
        df = pd.read_csv(StringIO(r.text))
        return df

    except Exception as e:
        print("CSV parsing error:", e)
        print(r.text[:1000])
        return pd.DataFrame()


# ============================================================
# OFFICIAL FINRA 2026 SETTLEMENT DATES GENERator
# ============================================================

def get_finra_settlement_dates(start_str, end_str):
    """
    Generates exact official FINRA settlement dates for 2026 
    (15th and last business day of the month, rolled back if weekend).
    """
    months = pd.date_range(start_str, end_str, freq="MS")
    settlement_dates = []

    for m in months:
        # 1st candidate: Mid-month (15th)
        mid_date = pd.Timestamp(year=m.year, month=m.month, day=15)
        # Roll back if weekend
        while mid_date.weekday() > 4:  # Saturday=5, Sunday=6
            mid_date -= pd.Timedelta(days=1)
        settlement_dates.append(mid_date)

        # 2nd candidate: Last day of the month
        last_day = m + pd.offsets.MonthEnd(0)
        # Roll back if weekend
        while last_day.weekday() > 4:
            last_day -= pd.Timedelta(days=1)
        settlement_dates.append(last_day)

    # Filter within bounds and remove duplicates/sorting
    start_ts = pd.Timestamp(start_str)
    end_ts = pd.Timestamp(end_str)
    
    valid_dates = sorted(list(set([
        d for d in settlement_dates if start_ts <= d <= end_ts
    ])))
    
    return valid_dates

candidate_dates = get_finra_settlement_dates(START_DATE, END_DATE)


# ============================================================
# DOWNLOAD
# ============================================================

results = []

for d in candidate_dates:

    date_str = d.strftime("%Y-%m-%d")

    df_date = get_short_interest_date(
        date_str
    )

    if not df_date.empty:
        results.append(df_date)

    time.sleep(0.2)


# ============================================================
# COMBINE & PROCESS
# ============================================================

if results:

    df = pd.concat(
        results,
        ignore_index=True
    )

    numeric_columns = [
        "currentShortPositionQuantity",
        "previousShortPositionQuantity",
        "averageDailyVolumeQuantity",
        "daysToCoverQuantity",
        "changePercent",
        "changePreviousNumber"
    ]

    for col in numeric_columns:
        if col in df.columns:
            df[col] = pd.to_numeric(
                df[col],
                errors="coerce"
            )

    df["short_change"] = (
        df["currentShortPositionQuantity"]
        -
        df["previousShortPositionQuantity"]
    )

    df["short_change_pct"] = (
        df["short_change"]
        /
        df["previousShortPositionQuantity"]
        * 100
    )

    print("\n==============================================")
    print(f"{TICKER} HISTORICAL SHORT INTEREST")
    print("==============================================")

    print(
        df[
            [
                "settlementDate",
                "symbolCode",
                "currentShortPositionQuantity",
                "previousShortPositionQuantity",
                "short_change",
                "short_change_pct",
                "averageDailyVolumeQuantity",
                "daysToCoverQuantity"
            ]
        ].to_string(index=False)
    )

    df.to_csv(
        f"{TICKER}_short_interest_history.csv",
        index=False
    )

    print(f"\nSaved: {TICKER}_short_interest_history.csv")

else:
    print(f"\nNo data found for {TICKER}.")
