#!/usr/bin/env python3

import os
from playwright.sync_api import sync_playwright
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# STEP 1: Scrape all Google Trends – South Korea Trending Now
def scrape_all_trends() -> pd.DataFrame:
    with sync_playwright() as p:
        # headless=True for CI environments
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        url = "https://trends.google.com/trends/trendingsearches/daily?geo=KR"
        page.goto(url)

        # Wait for content to load, then scroll
        page.wait_for_timeout(5000)
        page.mouse.wheel(0, 5000)
        page.wait_for_timeout(5000)

        trends_data = []
        titles = page.locator('a.trending-search')
        total = titles.count()
        print(f"📝 Found {total} trending topics")

        for i in range(total):
            try:
                title = titles.nth(i).inner_text().strip()
                link = titles.nth(i).get_attribute('href') or ''
                trends_data.append([title, link.strip()])
            except Exception as e:
                print(f"⚠️ Error on item {i}: {e}")

        browser.close()

    df = pd.DataFrame(trends_data, columns=["Trending Topic", "Link to Trend"])
    return df

# STEP 2: Upload to Google Sheets
def upload_to_google_sheets(df: pd.DataFrame):
    # The workflow writes your secret into service_account.json
    keyfile = os.getenv("GOOGLE_SA_KEYFILE", "service_account.json")

    scope = [
        "https://spreadsheets.google.com/feeds",
        "https://www.googleapis.com/auth/drive"
    ]
    creds = ServiceAccountCredentials.from_json_keyfile_name(keyfile, scope)
    client = gspread.authorize(creds)

    sheet = client.open("Trends").sheet1
    sheet.clear()
    sheet.update([df.columns.tolist()] + df.values.tolist())

# STEP 3: Main runner
def main():
    print("🚀 Starting Korean Trending Now Scraper...")
    df = scrape_all_trends()

    if df.empty:
        print("⚠️ No trends found or page structure changed.")
    else:
        print(f"✅ Scraped {len(df)} trends.")
        upload_to_google_sheets(df)
        print("✅ Uploaded to Google Sheets!")

if __name__ == "__main__":
    main()
