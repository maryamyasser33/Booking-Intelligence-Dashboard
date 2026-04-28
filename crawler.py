from playwright.sync_api import sync_playwright
import pandas as pd
import time

def scrape_booking_data(url):
    hotel_data = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False) 
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = context.new_page()

        print(f"Navigating to: {url}")
        page.goto(url, timeout=60000)

        page.wait_for_selector('[data-testid="property-card"]', timeout=15000)

        for _ in range(5):
            page.mouse.wheel(0, 1000)
            time.sleep(1)

        property_cards = page.locator('[data-testid="property-card"]').all()
        print(f"Found {len(property_cards)} properties. Extracting data and URLs...")

        for card in property_cards:
            try:
                # 1. Extract Hotel Name
                title_locator = card.locator('[data-testid="title"]')
                name = title_locator.inner_text() if title_locator.count() > 0 else "N/A"

                # 2. Extract the unique Hotel URL (NEW)
                link_locator = card.locator('[data-testid="title-link"]')
                raw_url = link_locator.get_attribute('href') if link_locator.count() > 0 else "N/A"
                
                # Booking.com sometimes returns relative URLs (e.g., /hotel/eg/...). 
                # We need to make sure it's a full, clickable link.
                full_url = raw_url
                if raw_url != "N/A" and raw_url.startswith('/'):
                    full_url = f"https://www.booking.com{raw_url}"
                # Sometimes the URL has heavy tracking parameters. We can clean it up by splitting at the '?'
                clean_url = full_url.split('?')[0] if full_url != "N/A" else "N/A"

                # 3. Extract Price
                price_locator = card.locator('[data-testid="price-and-discounted-price"]')
                price = price_locator.inner_text().replace('\n', ' ') if price_locator.count() > 0 else "N/A"

                # 4. Extract Review Score
                score_locator = card.locator('[data-testid="review-score"] > div:first-child')
                score = score_locator.inner_text() if score_locator.count() > 0 else "N/A"

                hotel_data.append({
                    "Hotel Name": name,
                    "Price": price,
                    "Review Score": score,
                    "Property URL": clean_url # Added to our dataset
                })
                
            except Exception as e:
                print(f"Error extracting a card: {e}")
                continue

        browser.close()

    return hotel_data

if __name__ == "__main__":
    target_url = "https://www.booking.com/searchresults.en-gb.html?ss=Cairo&checkin=2026-04-29&checkout=2026-04-30"
    
    data = scrape_booking_data(target_url)
    
    if data:
        df = pd.DataFrame(data)
        df.to_csv("booking_cairo_data_with_urls.csv", index=False, encoding='utf-8')
        print("\nScraping complete! Data saved to booking_cairo_data_with_urls.csv")
        # Print just the names and URLs to verify
        print(df[['Hotel Name', 'Property URL']].head())
    else:
        print("No data extracted.")