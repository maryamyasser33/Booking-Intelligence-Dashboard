from playwright.sync_api import sync_playwright
import pandas as pd
import time
import re

def scrape_reviews(urls):
    all_reviews = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            viewport={'width': 1280, 'height': 800},
            locale='en-US' 
        )
        page = context.new_page()

        for url in urls[3:5]:
            if pd.isna(url) or url == "N/A":
                continue
                
            print(f"\nNavigating to: {url}")
            try:
                page.goto(url, timeout=60000, wait_until="domcontentloaded")
                time.sleep(3) 
                
                try:
                    page.locator('button:has-text("Accept"), button:has-text("Decline")').first.click(timeout=2000)
                except:
                    pass 

                print("Hunting down the page to open the reviews modal...")
                
                modal_opened = False
                for i in range(15): 
                    page.mouse.wheel(0, 500) 
                    time.sleep(1)
                    
                    try:
                        button_selectors = [
                            'text="Read all reviews"',
                            '[data-testid="review-score-right-component"]'
                        ]
                        
                        for btn_sel in button_selectors:
                            btn = page.locator(btn_sel).first
                            if btn.is_visible(timeout=500):
                                print(f"--> Found trigger '{btn_sel}'. Clicking it...")
                                btn.click()
                                time.sleep(3) # Wait for modal animation
                                modal_opened = True
                                break 
                                
                        if modal_opened:
                            break 
                    except:
                        pass 

# Clear silent filters (Targeting the SPAN)
                try:
                    print("Checking for 'Show all reviews' filter button...")
                    
                    # Target the span directly
                    show_all_btn = page.locator('span:has-text("Show all reviews")').first
                    
                    if show_all_btn.is_visible(timeout=4000):
                        print("--> Detected active filter (SPAN)! Attempting to click...")
                        show_all_btn.click(force=True) 
                        time.sleep(4) # Give the server time to fetch the new reviews
                        print("--> Click successful, waiting for refresh.")
                    else:
                        print("--> No filter button visible.")
                except Exception as e:
                    print(f"--> Filter button error: {e}")


                # THE FIX: Explicitly wait for the review cards to exist in the DOM
                print("Waiting for review cards to render from the server...")
                try:
                    page.wait_for_selector('[data-testid="review-card"], .c-review-block', timeout=15000)
                    print("--> Cards loaded successfully!")
                except:
                    print("--> Warning: Cards took too long to load.")

                print("Extracting review text...")
                
                review_elements = []
                selectors_to_try = [
                    '[data-testid="review-card"]',     
                    '[data-testid="featured-review-card"]', 
                    '.c-review-block'                  
                ]

                for selector in selectors_to_try:
                    elements = page.locator(selector).all()
                    if len(elements) > 0:
                        review_elements = elements
                        print(f"Matched selector: {selector}")
                        break

                print(f"Extracted {len(review_elements)} reviews on this page.")

                if len(review_elements) == 0:
                    safe_name = re.sub(r'[^a-zA-Z0-9]', '_', url.split('/')[-1].split('.')[0])
                    page.screenshot(path=f"debug_{safe_name}.png")

                # Grabbing 10 reviews instead of 5 for a better dataset
                for element in review_elements[:10]: 
                    try:
                        text_body = element.locator('[data-testid="review-text"]').first
                        if text_body.count() > 0:
                            raw_text = text_body.inner_text()
                        else:
                            raw_text = element.inner_text()
                            
                        clean_text = raw_text.replace('\n', ' ').replace('Read more', '').replace('Show less', '').strip()
                        
                        if len(clean_text) > 15: 
                            all_reviews.append({
                                "Hotel URL": url,
                                "Review Text": clean_text
                            })
                    except Exception as e:
                        print(f"Could not parse a review: {e}")
            
            except Exception as e:
                print(f"Error scraping {url}: {e}")
                continue

        browser.close()
    return all_reviews

if __name__ == "__main__":
    print("Loading URLs from CSV...")
    df = pd.read_csv("booking_cairo_data_with_urls.csv")
    hotel_urls = df['Property URL'].tolist()
    
    print(f"Total URLs loaded: {len(hotel_urls)}. Starting deep scrape on the first 3...")
    
    scraped_reviews = scrape_reviews(hotel_urls)
    
    if scraped_reviews:
        reviews_df = pd.DataFrame(scraped_reviews)
        reviews_df.to_csv("hotel_raw_reviews.csv", index=False, encoding='utf-8')
        print("\nSuccess! Saved reviews to hotel_raw_reviews.csv")
        print(reviews_df.head())
    else:
        print("\nNo reviews extracted. Check the new debug images.")