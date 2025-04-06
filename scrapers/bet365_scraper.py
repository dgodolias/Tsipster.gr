import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import json
import time
import random

# Initialize undetected-chromedriver with enhanced options
options = uc.ChromeOptions()
options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")
options.add_argument("--window-size=1920,1080")  # Mimic real browser size
options.add_argument("--disable-extensions")
driver = uc.Chrome(options=options)

# Replace with your working Bet365 match URL
match_url = "https://www.bet365.gr/#/AC/B1/C1/D8/E170419906/F3/I0/"
driver.get(match_url)
print(f"Attempting to load: {match_url}")

# Simulate human-like behavior
print("Simulating mouse movement...")
driver.execute_script("window.scrollBy(0, 200);")  # Small initial scroll
time.sleep(random.uniform(1, 2))  # Random delay

# Wait for page load (try a match-specific element)
try:
    WebDriverWait(driver, 30).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, "div[class*='event'], div[class*='match'], div[class*='market']"))
    )
    print("Match-related element detected")
except Exception as e:
    print(f"No match content detected: {str(e)}")

# Check current URL
current_url = driver.current_url
print(f"Current URL after load: {current_url}")

# Check for popup/login prompt
try:
    modal = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, "div[class*='modal'], div[class*='popup'], div[class*='login']"))
    )
    print("Popup or login prompt detected")
    try:
        close_button = modal.find_element(By.CSS_SELECTOR, "button[class*='close'], a[class*='close'], span[class*='close']")
        close_button.click()
        WebDriverWait(driver, 5).until(EC.invisibility_of_element(modal))
        print("Popup closed")
    except Exception as e:
        print(f"Couldn’t find close button: {str(e)}")
except Exception as e:
    print(f"No popup/login detected: {str(e)}")

# Scroll to the bottom with human-like pauses
print("Scrolling to the bottom of the page...")
for _ in range(3):  # Scroll in steps
    driver.execute_script("window.scrollBy(0, 500);")
    time.sleep(random.uniform(1, 2))
driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
time.sleep(15)  # Extended wait

# Get HTML content
html_content = driver.page_source
print(f"HTML content length: {len(html_content)} characters")

# Save HTML for debugging
with open("bet365_page_content.html", "w", encoding="utf-8") as f:
    f.write(html_content)

# Close the WebDriver
driver.quit()

# Parse with BeautifulSoup
soup = BeautifulSoup(html_content, 'html.parser')

# Extract match title (broader search)
match_title_elem = soup.find('h1') or soup.find('div', class_=lambda x: x and ('header' in x.lower() or 'title' in x.lower() or 'match' in x.lower()))
match_title = match_title_elem.text.strip() if match_title_elem else "Unknown Match"
print(f"Match title (if found): {match_title}")

# Check for markets (common Bet365 selectors)
markets = soup.select("div.gl-MarketGroup, div[class*='market'], div[class*='event']")
print(f"Found {len(markets)} market divs in HTML")

if not markets:
    alt_markets = soup.select("div[class*='group'], div[class*='participant']")
    print(f"Alternative market divs found: {len(alt_markets)}")
    if alt_markets:
        print(f"First alternative market content: {alt_markets[0].text.strip()[:100]}...")

# Output JSON
data = [{"match_title": match_title, "markets": []}]
print(json.dumps(data, ensure_ascii=False, indent=4))

print("Scraping attempt completed")