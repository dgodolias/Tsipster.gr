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
driver.get("https://www.stoiximan.gr/apodoseis/olybiakos-bodo-glimt/64219187/?bt=13")

# Wait for the page to load market sections
WebDriverWait(driver, 10).until(
    EC.presence_of_element_located((By.CSS_SELECTOR, "div[data-marketid]"))
)

# Find all market sections
market_divs = driver.find_elements(By.CSS_SELECTOR, "div[data-marketid]")

# Open all closed market sections
for market_div in market_divs:
    try:
        # Locate the arrow SVG within the market div
        arrow = market_div.find_element(By.CSS_SELECTOR, "svg.sb-arrow")
        # Check if the arrow has the 'sb-arrow--collapsed' class (indicating it's closed)
        if "sb-arrow--collapsed" not in arrow.get_attribute("class"):
            arrow.click()
            # Wait for the selections to load after clicking
            WebDriverWait(driver, 5).until(
                EC.presence_of_element_located((By.CLASS_NAME, "selections"))
            )
            # Small delay to ensure content loads completely
            time.sleep(0.01)
    except:
        # Skip if no arrow is found or it's already open
        continue

# Get the full HTML content after all sections are expanded
html_content = driver.page_source

# Close the WebDriver as we no longer need Selenium
driver.quit()

# Now use BeautifulSoup to parse the HTML
soup = BeautifulSoup(html_content, 'html.parser')

# Extract match title
try:
    match_title = soup.find('h1').text.strip()
except:
    match_title = "Ολυμπιακός vs Μπόντο Γκλιμτ"  # Fallback

# Define markets that require grouping
grouped_markets = [
    "Γκολ Over/Under", "Γκολ Over/Under, 1ο Ημίχρονο", "Ασιατικό Χάντικαπ",
    "Ασιατικό Χάντικαπ, 1ο Ημίχρονο", "Κόρνερ Over/Under", "Κάρτες Over/Under",
    "Χάντικαπ"
]

# Extract markets and outcomes using BeautifulSoup
markets = []
market_divs = soup.select('div[data-marketid]')

for market_div in market_divs:
    # Get market name
    market_name_elem = market_div.select_one('div.tw-self-center')
    if not market_name_elem:
        continue
    
    market_name = market_name_elem.text.strip()
    
    # Get all selections within the market
    selections = market_div.select('div.selections__selection')
    if not selections:
        continue
    
    outcomes = []
    for selection in selections:
        title_elem = selection.select_one('span.selection-horizontal-button__title')
        odds_elem = selection.select_one('span.tw-text-s.tw-leading-s.tw-font-bold')
        
        if title_elem and odds_elem:
            outcome_name = title_elem.text.strip()
            odds = odds_elem.text.strip()
            outcomes.append({"outcome": outcome_name, "odds": odds})
    
    # Handle grouping based on market type
    if market_name in grouped_markets:
        groups_dict = {}
        for outcome in outcomes:
            # Extract line (e.g., "0.5" from "Over 0.5" or "-1.5" from "-1.5")
            match = re.search(r"(Over|Under|\+|-)?\s*([\d.]+)", outcome["outcome"])
            if match:
                line = match.group(2) if match.group(1) in ["Over", "Under"] else outcome["outcome"]
                if line not in groups_dict:
                    groups_dict[line] = []
                groups_dict[line].append(outcome)
            elif "Ισοπαλία" in outcome["outcome"] or market_name == "Χάντικαπ":
                # Handle Handicap markets with format like "0:1"
                handicap_match = re.search(r"(\d+:\d+)", market_div.text)
                line = handicap_match.group(1) if handicap_match else "unknown"
                if line not in groups_dict:
                    groups_dict[line] = []
                groups_dict[line].append(outcome)
            else:
                # Fallback for unexpected formats
                groups_dict["default"] = groups_dict.get("default", []) + [outcome]

        market_groups = [
            {"group_title": line, "outcomes": outcomes}
            for line, outcomes in groups_dict.items()
        ]
    else:
        # Single group for markets without lines
        market_groups = [{"group_title": None, "outcomes": outcomes}]

    markets.append({"market_name": market_name, "groups": market_groups})

# Construct the final JSON
data = [{"match_title": match_title, "markets": markets}]

# Output the JSON
print(json.dumps(data, ensure_ascii=False, indent=4))