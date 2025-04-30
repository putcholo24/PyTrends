#!/usr/bin/env python3
import os
from playwright.sync_api import sync_playwright
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials

def scrape_all_trends() -> pd.DataFrame:
    with sync_playwright() as p:
        
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        url = "https://trends.google.com/trending?geo=KR&category=17"
        page.goto(url)

        page.wait_for_timeout(10000)

        trends_data = []
        trend_cards = page.locator('div.mZ3RIc')
        total_cards = trend_cards.count()
        print(f"📝 Found {total_cards} trending cards")

        for i in range(total_cards):
            try:
                card = trend_cards.nth(i)

                title = card.locator('a.title').inner_text().strip()
                search_volume = card.locator('div.search-count-title').inner_text().strip()

                
                try:
                    started_time = card.locator('xpath=../following-sibling::div//span').inner_text().strip()
                except:
                    started_time = ''

                
                try:
                    breakdown_items = card.locator('xpath=../following-sibling::div//div[@class="feed-item-breakdown-text"]').all_inner_texts()
                    breakdown = ', '.join([b.strip() for b in breakdown_items])
                except:
                    breakdown = ''

                trends_data.append([
                    title,
                    search_volume,
                    started_time,
                    breakdown
                ])

            except Exception as e:
                print(f"⚠️ Error processing card {i}: {e}")
                continue

        browser.close()

    
    df = pd.DataFrame(trends_data, columns=[
        "Trending Topic", 
        "Search Volume", 
        "Started Time", 
        "Trend Breakdown"
    ])
    return df
    
def upload_to_google_sheets(df: pd.DataFrame):
    # The workflow writes your secret into service_account.json
    keyfile = os.getenv("GOOGLE_SA_KEYFILE", "service_account.json")

    scope = [
        "https://spreadsheets.google.com/feeds",
        "https://www.googleapis.com/auth/drive"
    ]
    creds = ServiceAccountCredentials.from_json_keyfile_name(keyfile, scope)
    client = gspread.authorize(creds)

    sheet = client.open("Trends").sheet2  # Ensure a sheet called "Trends" exists
    sheet.clear()
    sheet.update([df.columns.tolist()] + df.values.tolist())

def main():
    print("🚀 Starting Korean Trending Now Scraper...")
    df_trends = scrape_all_trends()

    if df_trends.empty:
        print("⚠️ No trends found today or page structure changed.")
    else:
        print(f"✅ Scraped {len(df_trends)} trends.")
        upload_to_google_sheets(df_trends)
        print("✅ Successfully uploaded to Google Sheets!")

if __name__ == "__main__":
    main()
