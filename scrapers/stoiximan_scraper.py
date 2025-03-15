import json
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
import re
import time
from queue import Queue
from threading import Thread

def truncate_url(url):
    return url[:100] + "..." if len(url) > 100 else url

def fetch_page_source(driver, url):
    try:
        print(f"Fetching {truncate_url(url)}")
        initial_time = time.time()
        driver.get(url)
        
        # Wait for the page to load
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "div[data-marketid]"))
        )
        
        # Check for and close any popup ads
        try:
            # Check for landing page modal
            modal = WebDriverWait(driver, 3).until(
                EC.presence_of_element_located((By.ID, "landing-page-modal"))
            )
            
            # Try to find and click close button
            close_button = modal.find_element(By.CSS_SELECTOR, "button.button-close")
            close_button.click()
            print("Closed popup ad")
            
            # Wait for modal to disappear
            WebDriverWait(driver, 3).until(
                EC.invisibility_of_element(modal)
            )
        except:
            # If no popup or failed to close, remove it using JavaScript
            try:
                driver.execute_script("""
                    var elements = document.querySelectorAll('#landing-page-modal');
                    for(var i=0; i<elements.length; i++){
                        elements[i].remove();
                    }
                    
                    // Also remove overlay if present
                    var overlays = document.querySelectorAll('.sb-modal-overlay');
                    for(var i=0; i<overlays.length; i++){
                        overlays[i].remove();
                    }
                """)
                print("Removed popup using JavaScript")
            except:
                print("No popup ads found or couldn't remove")

        # Get match title
        match_title = "Unknown Match"
        try:
            match_title_elem = driver.find_element(By.TAG_NAME, "h1")
            match_title = match_title_elem.text.strip() if match_title_elem else "Unknown Match"
            print(f"Found match: {match_title}")
        except Exception as e:
            print(f"Could not extract match title for {truncate_url(url)}: {e}")
        
        # Find all market sections
        market_divs = driver.find_elements(By.CSS_SELECTOR, "div[data-marketid]")
        
        # Open all closed market sections
        total_divs = len(market_divs)
        for i, market_div in enumerate(market_divs):
            try:
                # Locate the arrow SVG within the market div
                arrow = market_div.find_element(By.CSS_SELECTOR, 
                    "svg.sb-arrow.tw-icon-xs.push-right.tw-icon.tw-fill-n-48-slate.dark\\:tw-fill-n-75-smokey.tw-cursor-pointer")
                # Check if the arrow has the 'sb-arrow--collapsed' class (indicating it's closed)
                if "sb-arrow--collapsed" not in arrow.get_attribute("class"):
                    arrow.click()
                    # Wait for the selections to load after clicking
                    WebDriverWait(driver, 5).until(
                        EC.presence_of_element_located((By.CLASS_NAME, "selections"))
                    )
                    # Use a longer delay for the last 10% of sections
                    if i >= int(total_divs * 0.9):
                        time.sleep(0.2)
                    else:
                        time.sleep(0.01)
            except:
                # Skip if no arrow is found or it's already open
                continue
        
        # Get the full HTML content after all sections are expanded
        source = driver.page_source
        
        print(f"Time to fetch {truncate_url(url)}: {time.time() - initial_time:.2f} seconds")
        return match_title, source
    except Exception as e:
        print(f"Error fetching {truncate_url(url)}: {e}")
        return "Unknown Match", None

def parse_source(match_title, source):
    if source is None:
        return None
    
    print(f"Parsing data for {match_title}")
    initial_time = time.time()
    
    # Use BeautifulSoup to parse the HTML
    soup = BeautifulSoup(source, 'html.parser')
    
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
    
    match_object = {"match_title": match_title, "markets": markets}
    print(f"Time to parse {match_title}: {time.time() - initial_time:.2f} seconds")
    return match_object

# Fetcher thread function
def fetcher(queue, urls, driver):
    for url in urls:
        match_title, source = fetch_page_source(driver, url)
        queue.put((match_title, source))
    # Signal end of fetching
    queue.put(None)

# Parser thread function
def parser(queue, results):
    while True:
        item = queue.get()
        if item is None:
            break
        match_title, source = item
        match_object = parse_source(match_title, source)
        if match_object:
            results.append(match_object)

def main():
    # Load URLs
    with open('matches/stoiximan/uel/match_urls.json', 'r', encoding='utf-8') as f:
        match_urls = json.load(f)
    
    # Initialize queue and results list
    queue = Queue()
    results = []
    
    # Set up WebDriver options
    chrome_options = Options()
    chrome_options.add_argument("--headless")  # Use traditional headless mode
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--log-level=3")  # Suppress driver debug logs
    chrome_options.add_experimental_option('excludeSwitches', ['enable-logging'])

    # Make headless less detectable
    chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_argument("--window-size=1920,1080")
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
    
    # Start parser threads
    num_workers = 4  # Adjust based on your system's capabilities
    parsers = []
    for _ in range(num_workers):
        p = Thread(target=parser, args=(queue, results))
        p.start()
        parsers.append(p)
    
    # Start fetcher thread
    fetcher_thread = Thread(target=fetcher, args=(queue, match_urls, driver))
    fetcher_thread.start()
    
    # Wait for fetcher to complete
    fetcher_thread.join()
    
    # Signal all parsers to stop
    for _ in range(num_workers):
        queue.put(None)
    
    # Wait for all parsers to finish
    for p in parsers:
        p.join()
    
    # Clean up WebDriver
    driver.quit()
    
    # Save results
    with open("odds/stoiximan/UEL_odds_stoiximan.json", "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=4)
    
    print(f"Processed {len(results)} matches. Odds data saved to odds/stoiximan/UEL_odds_stoiximan.json")

if __name__ == "__main__":
    main()