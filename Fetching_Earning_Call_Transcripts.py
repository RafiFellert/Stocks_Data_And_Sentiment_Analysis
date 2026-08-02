import os
import re
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup


# -------------------------------------------------------
# Configuration
# -------------------------------------------------------

BASE_URL = "https://stockanalysis.com"
TICKER = "GOOGL"

INDEX_URL = (
    f"{BASE_URL}/stocks/{TICKER.lower()}/transcripts/"
)

OUTPUT_DIR = os.path.join("transcripts", TICKER.upper())

os.makedirs(OUTPUT_DIR, exist_ok=True)


# -------------------------------------------------------
# Start browser
# -------------------------------------------------------

options = Options()
options.add_argument("--headless")
options.add_argument("--disable-gpu")
options.add_argument("--window-size=1920,1080")

driver = webdriver.Chrome(options=options)


# -------------------------------------------------------
# Get transcript list
# -------------------------------------------------------

print("Loading transcript page...")

driver.get(INDEX_URL)

time.sleep(5)

soup = BeautifulSoup(driver.page_source, "html.parser")


links = []

for a in soup.find_all("a", href=True):

    href = a["href"]

    if (
        f"/stocks/{TICKER.lower()}/transcripts/" in href
        and href != f"/stocks/{TICKER.lower()}/transcripts/"
    ):
        links.append(href)


# Remove duplicates

links = sorted(set(links))


# Keep only earnings calls from 2025

links = [
    x for x in links
    if re.search(
        r'q[1-4]-2025',
        x,
        re.IGNORECASE
    )
]


print(f"Found {len(links)} 2025 earnings calls")


# -------------------------------------------------------
# Download each transcript
# -------------------------------------------------------

for i, link in enumerate(links, 1):

    url = BASE_URL + link

    print(
        f"[{i}/{len(links)}] {url}"
    )


    driver.get(url)

    time.sleep(3)


    soup = BeautifulSoup(
        driver.page_source,
        "html.parser"
    )


    # -----------------------------
    # Title
    # -----------------------------

    title_tag = soup.find("h1")

    title = (
        title_tag.get_text(strip=True)
        if title_tag
        else "Unknown"
    )


    # -----------------------------
    # Transcript text
    # -----------------------------

    article = soup.find(
        "div",
        class_="transcript-body"
    )


    if article:

        transcript = article.get_text(
            "\n",
            strip=True
        )

    else:

        transcript = soup.get_text(
            "\n",
            strip=True
        )


      # -----------------------------
    # Create filename
    # Format: YYYY-Mon-DD-TICKER.txt
    # -----------------------------

    filename = None

    # Try to extract a date such as "Apr 24, 2025" from the title
    date_match = re.search(
        r'([A-Z][a-z]{2})\s+(\d{1,2}),\s+(\d{4})',
        title
    )

    if date_match:
        month, day, year = date_match.groups()
        filename = f"{year}-{month}-{int(day):02d}-{TICKER.upper()}.txt"

    else:
        # Fallback: use year and quarter from the URL
        q_match = re.search(
            r'q([1-4])-(\d{4})',
            link,
            re.IGNORECASE
        )

        if q_match:
            quarter, year = q_match.groups()
            filename = f"{year}-Q{quarter}-{TICKER.upper()}.txt"
        else:
            filename = f"Unknown-{TICKER.upper()}.txt"


    # -----------------------------
    # Save transcript
    # -----------------------------

    file_path = os.path.join(OUTPUT_DIR, filename)

    with open(
        file_path,
        "w",
        encoding="utf-8"
    ) as f:
        f.write(transcript)

    print(f"Saved: {file_path}")


    time.sleep(2)


driver.quit()


print("Done!")
