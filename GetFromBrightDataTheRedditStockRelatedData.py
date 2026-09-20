import requests
import time
import pandas as pd
import json
from datetime import datetime

# ============================================================
# BRIGHT DATA
# ============================================================

API_KEY = <Your Bright Data API Key>
DATASET_ID = "Your Bright Data Data Set ID"
BASE_URL = "Your Bright Data Base URL"

# ============================================================
# SETTINGS
# ============================================================

KEYWORD = <Stock Ticker>
NUM_POSTS = <Num of Posts You Want to Download"

# Target filter settings
TARGET_YEAR = 2026
TARGET_MONTH = 4  # April

OUTPUT_FILE = <file name>
RAW_JSON_FILE = <file name>

# ============================================================
# HEADERS
# ============================================================

headers = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json"
}

# ============================================================
# STEP 1 — START COLLECTION
# ============================================================

payload = {
    "input": [
        {
            "keyword": KEYWORD,
            "date": "Past year",
            "num_of_posts": NUM_POSTS
        }
    ]
}

print("Starting Bright Data collection...")

response = requests.post(
    f"{BASE_URL}/scrape",
    params={
        "dataset_id": DATASET_ID,
        "type": "discover_new",
        "discover_by": "keyword"
    },
    headers=headers,
    json=payload,
    timeout=120
)

print("Collection status:", response.status_code)

if response.status_code not in [200, 202]:
    raise Exception(f"Bright Data request failed: {response.text}")

# ============================================================
# GET SNAPSHOT ID
# ============================================================

result = response.json()
snapshot_id = result.get("snapshot_id")

if not snapshot_id:
    raise Exception("No snapshot_id returned by Bright Data")

print("\nSnapshot ID:", snapshot_id)

# ============================================================
# STEP 2 — MONITOR PROGRESS
# ============================================================

progress_url = f"{BASE_URL}/progress/{snapshot_id}"
print("\nWaiting for Reddit data...")

while True:
    response = requests.get(
        progress_url,
        headers=headers,
        timeout=30
    )

    if response.status_code != 200:
        print("Progress check failed:", response.status_code)
        print(response.text)
        break

    progress = response.json()
    status = progress.get("status")

    print("Status:", status)

    if status == "ready":
        print("\nCollection completed!")
        break

    if status == "failed":
        print("\nCollection FAILED:")
        print(progress)
        raise Exception("Bright Data collection failed")

    time.sleep(10)

# ============================================================
# STEP 3 — DOWNLOAD SNAPSHOT
# ============================================================

print("\nDownloading Reddit data...")

download_url = f"{BASE_URL}/snapshot/{snapshot_id}"

response = requests.get(
    download_url,
    headers=headers,
    params={"format": "json"},
    timeout=120
)

if response.status_code != 200:
    print(response.text)
    raise Exception("Could not download snapshot")

data = response.json()
print(f"\nTotal raw records returned from API: {len(data)}")

# ============================================================
# STEP 4 — FILTER DATA BY DATE
# ============================================================

filtered_data = []

for post in data:
    # Bright Data usually uses 'date_posted', 'created_at', or 'date'
    raw_date = post.get("date_posted") or post.get("created_at") or post.get("date")
    
    if not raw_date:
        continue
        
    try:
        # Check if epoch timestamp (integer/float) or ISO string
        if isinstance(raw_date, (int, float)):
            post_dt = datetime.fromtimestamp(raw_date)
        else:
            # Clean ISO string formatting (e.g. "2025-10-15T14:30:00Z")
            clean_date_str = str(raw_date).replace("Z", "+00:00")
            post_dt = datetime.fromisoformat(clean_date_str)

        # Match Year and Month
        if post_dt.year == TARGET_YEAR and (post_dt.month == TARGET_MONTH or post_dt.month == (TARGET_MONTH + 1)):
            filtered_data.append(post)

    except Exception:
        # Skip record if date parsing fails
        continue

print(f"Filtered records for {TARGET_YEAR}-{TARGET_MONTH:02d}: {len(filtered_data)}")

# ============================================================
# SAVE FILTERED RAW JSON
# ============================================================

with open(RAW_JSON_FILE, "w", encoding="utf-8") as f:
    json.dump(filtered_data, f, indent=2, ensure_ascii=False)

# ============================================================
# SAVE FILTERED CSV
# ============================================================

df = pd.DataFrame(filtered_data)

if not df.empty:
    df.to_csv(OUTPUT_FILE, index=False, encoding="utf-8-sig")

# ============================================================
# DISPLAY RESULTS
# ============================================================

print("\n" + "=" * 80)
print("RESULT")
print("=" * 80)

print("Number of posts kept:", len(df))

if not df.empty:
    print("\nColumns:")
    for column in df.columns:
        print(" -", column)

    print("\nFirst 5 posts:")
    print(df.head().to_string())
else:
    print(f"\nNo posts found matching month {TARGET_MONTH}/{TARGET_YEAR}.")

print("\nSaved CSV:", OUTPUT_FILE)
print("Saved Raw JSON:", RAW_JSON_FILE)
