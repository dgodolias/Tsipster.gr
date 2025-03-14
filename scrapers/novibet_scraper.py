from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import re
import json
import time

# Initialize Selenium WebDriver
driver = webdriver.Chrome()
driver.get("https://www.novibet.gr/stoixima/matches/ofi-atromitos/e39606712")

# Check for and close the specific "registerOrLogin_closeButton" FIRST
try:
    close_button = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.CSS_SELECTOR, "div.registerOrLogin_closeButton.u-flex.u-flexCenter.u-clickable"))
    )
    close_button.click()
    print("Closed registerOrLogin_closeButton using normal click")
except Exception as e:
    print(f"Normal click failed: {str(e)}")
    try:
        close_button = driver.find_element(By.CSS_SELECTOR, "div.registerOrLogin_closeButton.u-flex.u-flexCenter.u-clickable")
        driver.execute_script("arguments[0].click();", close_button)
        print("Closed registerOrLogin_closeButton using JavaScript click")
    except Exception as js_e:
        print(f"JavaScript click also failed: {str(js_e)}")

# Wait for the popup to disappear
try:
    WebDriverWait(driver, 5).until(
        EC.invisibility_of_element((By.CSS_SELECTOR, "div.registerOrLogin_closeButton.u-flex.u-flexCenter.u-clickable"))
    )
    print("Popup successfully closed")
except Exception as e:
    print(f"Popup might still be present or different selector needed: {str(e)}")

# Wait for the page to load (use a generic body selector as fallback)
try:
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.TAG_NAME, "body"))
    )
    print("Page body loaded successfully")
except Exception as e:
    print(f"Error waiting for page to load (continuing anyway): {str(e)}")
    with open("novibet_error_page.html", "w", encoding="utf-8") as f:
        f.write(driver.page_source)

# Scroll to the bottom to ensure all content is loaded
print("Scrolling to the bottom of the page...")
driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
time.sleep(10)  # Increased wait time for dynamic content

# Check for market presence before capturing HTML
try:
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, "app-event-marketview.u-cmp.eventPrelive_marketviewCategory.ng-star-inserted"))
    )
    print("Markets detected in DOM")
except Exception as e:
    print(f"No markets detected with current selector: {str(e)}")

# Get the full HTML content
html_content = driver.page_source

# Save HTML for debugging
with open("novibet_page_content.html", "w", encoding="utf-8") as f:
    f.write(html_content)

# Close the WebDriver
driver.quit()

# Use BeautifulSoup to parse the HTML
soup = BeautifulSoup(html_content, 'html.parser')

# Extract match title
try:
    match_title = soup.find('h1').text.strip()
except:
    match_title = "ΟΦΗ vs Ατρόμητος"  # Fallback
print(f"Match title: {match_title}")

# Define markets that require grouping
grouped_markets = [
    "Γκολ Over/Under", "Γκολ Over/Under, 1ο Ημίχρονο", "Ασιατικό Χάντικαπ",
    "Ασιατικό Χάντικαπ, 1ο Ημίχρονο", "Κόρνερ Over/Under", "Κάρτες Over/Under",
    "Χάντικαπ"
]

# Extract markets and outcomes
markets = []
market_divs = soup.select("app-event-marketview.u-cmp.eventPrelive_marketviewCategory.ng-star-inserted")
print(f"Found {len(market_divs)} market divs in HTML")
if len(market_divs) == 0:
    # Debug: Check for any market-like elements
    alt_market_divs = soup.select("div[class*='market']")
    print(f"Alternative market divs found (using 'market' class): {len(alt_market_divs)}")
    if alt_market_divs:
        print(f"First alternative market content: {alt_market_divs[0].text.strip()[:100]}...")

for idx, market_div in enumerate(market_divs):
    try:
        market_name_elem = market_div.select_one('span.eventMarketview_title')
        if not market_name_elem:
            print(f"Skipping market {idx+1}: No market name found")
            print(f"  Market div content (first 100 chars): {market_div.text.strip()[:100]}...")
            continue
        
        market_name = market_name_elem.text.strip()
        print(f"Processing market {idx+1}/{len(market_divs)}: {market_name}")
        
        selections = market_div.select("div.marketBetItem.prelive.u-flex.u-flexCenter")
        if not selections:
            print(f"Skipping market '{market_name}': No selections found")
            continue
        
        outcomes = []
        for selection_idx, selection in enumerate(selections):
            try:
                title_elem = selection
                odds_elem = selection.select_one('span.marketBetItem_price.ng-star-inserted')
                
                if title_elem and odds_elem:
                    odds = odds_elem.text.strip()
                    outcome_name = title_elem.text.strip().replace(odds, "").strip()
                    print(f"  Selection {selection_idx+1}: {outcome_name} - {odds}")
                    outcomes.append({"outcome": outcome_name, "odds": odds})
                else:
                    print(f"  Skipping selection {selection_idx+1} in '{market_name}': Missing title or odds")
                    print(f"    Selection content: {selection.text.strip()[:100]}...")
            except Exception as e:
                print(f"  Error parsing selection {selection_idx+1} in '{market_name}': {str(e)}")
                continue
        
        if not outcomes:
            print(f"No outcomes recorded for market '{market_name}'")
            continue
        
        try:
            if market_name in grouped_markets:
                groups_dict = {}
                for outcome in outcomes:
                    try:
                        match = re.search(r"(Over|Under|\+|-)?\s*([\d.]+)", outcome["outcome"], re.IGNORECASE)
                        if match:
                            line = match.group(2) if match.group(1) in ["Over", "Under"] else outcome["outcome"]
                            if line not in groups_dict:
                                groups_dict[line] = []
                            groups_dict[line].append(outcome)
                        elif "Ισοπαλία" in outcome["outcome"] or market_name == "Χάντικαπ":
                            handicap_match = re.search(r"(\d+:\d+)", market_div.text)
                            line = handicap_match.group(1) if handicap_match else "unknown"
                            if line not in groups_dict:
                                groups_dict[line] = []
                            groups_dict[line].append(outcome)
                        else:
                            print(f"  Outcome '{outcome['outcome']}' in '{market_name}' doesn't match grouping patterns")
                            groups_dict["default"] = groups_dict.get("default", []) + [outcome]
                    except Exception as e:
                        print(f"  Error grouping outcome '{outcome['outcome']}' in market '{market_name}': {str(e)}")
                        groups_dict["default"] = groups_dict.get("default", []) + [outcome]

                market_groups = [
                    {"group_title": line, "outcomes": outcomes}
                    for line, outcomes in groups_dict.items()
                ]
            else:
                market_groups = [{"group_title": None, "outcomes": outcomes}]
        except Exception as e:
            print(f"Error creating groups for market '{market_name}': {str(e)}")
            market_groups = [{"group_title": None, "outcomes": outcomes}]

        markets.append({"market_name": market_name, "groups": market_groups})

    except Exception as e:
        print(f"Error processing market {idx+1}: {str(e)}")
        continue

# Construct the final JSON
data = [{"match_title": match_title, "markets": markets}]
print(f"Processed {len(markets)} markets")

# Output the JSON to console
print(json.dumps(data, ensure_ascii=False, indent=4))

# Save to a file for debugging
with open("novibet_output.json", "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=4)

print("Scraping completed")