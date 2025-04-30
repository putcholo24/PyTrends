from playwright.sync_api import sync_playwright
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import time

# STEP 1: Scrape all Google Trends - South Korea Trending Now
def scrape_all_trends():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)  # headless=False temporarily to debug visually
        page = browser.new_page()

        # Open Google Trends Daily Trending Now for South Korea
        url = "https://trends.google.com/trends/trendingsearches/daily?geo=KR"
        page.goto(url)

        # Wait and scroll slowly to make sure all content loads
        page.wait_for_timeout(5000)
        page.mouse.wheel(0, 5000)  # Scroll down

        page.wait_for_timeout(5000)  # Wait again for full content load

        trends_data = []

        # Now locate all trend titles correctly
        titles = page.locator('a.trending-search')

        total_trends = titles.count()
        print(f"📝 Found {total_trends} trending topics")

        for i in range(total_trends):
            try:
                title = titles.nth(i).inner_text()
                link = titles.nth(i).get_attribute('href')

                trends_data.append([
                    title.strip(),
                    link.strip() if link else ''
                ])

            except Exception as e:
                print(f"⚠️ Error processing a trend: {e}")
                continue

        browser.close()

    # Create DataFrame
    df = pd.DataFrame(trends_data, columns=["Trending Topic", "Link to Trend"])
    return df


# STEP 2: Upload to Google Sheets
def upload_to_google_sheets(df):
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_name('trends-458208-4d1f98834c57.json', scope)
    client = gspread.authorize(creds)

    sheet = client.open("Trends").sheet1  # Make sure your Google Sheet is named "Trends"

    # Clear previous data
    sheet.clear()

    # Upload new data
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
