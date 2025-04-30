import os
from playwright.sync_api import sync_playwright
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# STEP 1: Scrape all Google Trends – South Korea Trending Now
def scrape_all_trends():
    with sync_playwright() as p:
        # run in headless mode (needed on GitHub Actions)
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        url = "https://trends.google.com/trends/trendingsearches/daily?geo=KR"
        page.goto(url)

        # give the page a moment to load
        page.wait_for_timeout(5000)
        page.mouse.wheel(0, 5000)
        page.wait_for_timeout(5000)

        trends_data = []
        titles = page.locator('a.trending-search')
        total_trends = titles.count()
        print(f"📝 Found {total_trends} trending topics")

        for i in range(total_trends):
            try:
                title = titles.nth(i).inner_text().strip()
                link = titles.nth(i).get_attribute('href') or ''
                trends_data.append([title, link.strip()])
            except Exception as e:
                print(f"⚠️ Error processing a trend: {e}")
                continue

        browser.close()

    df = pd.DataFrame(trends_data, columns=["Trending Topic", "Link to Trend"])
    return df


# STEP 2: Upload to Google Sheets
def upload_to_google_sheets(df):
    # the workflow writes your secret JSON into service_account.json
    keyfile = os.getenv("GOOGLE_SA_KEYFILE", "service_account.json")
    scope = [
        "https://spreadsheets.google.com/feeds",
        "https://www.googleapis.com/auth/drive"
    ]
    creds = ServiceAccountCredentials.from_json_keyfile_name(keyfile, scope)
    client = gspread.authorize(creds)

    sheet = client.open("Trends").sheet1
    sheet.clear()
    sheet.update([df.columns.values.tolist()] + df.values.tolist())


# STEP 3: Main Runner
if __name__ == "__main__":
    print("🚀 Starting Korean Trending Now Scraper...")

    df_trends = scrape_all_trends()
    if not df_trends.empty:
        print(f"✅ Scraping successful! Found {len(df_trends)} trends.")
        upload_to_google_sheets(df_trends)
        print("✅ Successfully uploaded to Google Sheets!")
    else:
        print("⚠️ No trends found today or page structure changed.")
