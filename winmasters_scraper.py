import json
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
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
        print(f"Successfully retrieved the initial HTML page for {truncate_url(url)}")
        
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "SportsIframe")))
        driver.switch_to.frame("SportsIframe")
        
        match_title = "Unknown Match"
        try:
            WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CLASS_NAME, "MatchDetailsHeader__Participants")))
            home_team = driver.find_element(By.CLASS_NAME, "MatchDetailsHeader__PartName--Home").text or "Home"
            away_team = driver.find_element(By.CLASS_NAME, "MatchDetailsHeader__PartName--Away").text or "Away"
            match_title = f"{home_team} vs {away_team}"
            print(f"Found match: {match_title}")
        except Exception as e:
            print(f"Could not extract match title for {truncate_url(url)}: {e}")
        
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CLASS_NAME, "MarketContainer")))
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
    soup = BeautifulSoup(source, "html.parser")
    markets = soup.find_all("article", class_="Market")
    
    if not markets:
        print(f"No markets found for {match_title}")
        return None
    
    all_markets = []
    for market in markets:
        market_name_elem = market.find("span", class_="Market__CollapseText")
        market_name = market_name_elem.text.strip() if market_name_elem else "Unknown Market"
        
        market_headers_wrapper = market.find("ul", class_="Market__Headers")
        market_headers = [header.text.strip() for header in market_headers_wrapper.find_all("li", class_="Market__Header")] if market_headers_wrapper else []
        
        odds_groups = market.find_all("ul", class_="Market__OddsGroup")
        market_dict = {"market_name": market_name, "groups": []}
        
        is_over_under = "Over/Under" in market_name
        
        if odds_groups:
            for group in odds_groups:
                group_title_elem = group.find("li", class_="Market__OddsGroupTitle")
                group_title = group_title_elem.text.strip() if group_title_elem else None
                odds_buttons = group.find_all("button", class_="OddsButton")
                outcomes = []
                
                # Check if this is an Over/Under market with exactly 2 outcomes
                if is_over_under and len(odds_buttons) == 2:
                    # Explicitly assign "Over" and "Under" with group title
                    for i, button in enumerate(odds_buttons):
                        odds_elem = button.find("span", class_="OddsButton__Odds")
                        odds = odds_elem.text.strip() if odds_elem else "N/A"
                        outcome_text = f"Over {group_title}" if i == 0 else f"Under {group_title}"
                        outcomes.append({"outcome": outcome_text, "odds": odds})
                else:
                    # Fallback to existing logic for other markets
                    for i, button in enumerate(odds_buttons):
                        outcome_elem = button.find("span", class_="OddsButton__Text")
                        odds_elem = button.find("span", class_="OddsButton__Odds")
                        outcome_text = (outcome_elem.text.strip() if outcome_elem and outcome_elem.text.strip() else
                                        button.get('title', '').strip() or
                                        (market_headers[i] if i < len(market_headers) else f"Option {i+1}"))
                        odds = odds_elem.text.strip() if odds_elem else "N/A"
                        outcomes.append({"outcome": outcome_text, "odds": odds})
                
                market_dict["groups"].append({"group_title": group_title, "outcomes": outcomes})
        else:
            outcomes = []
            odds_buttons = market.find_all("button", class_="OddsButton")
            if is_over_under and len(odds_buttons) == 2:
                for i, button in enumerate(odds_buttons):
                    odds_elem = button.find("span", class_="OddsButton__Odds")
                    odds = odds_elem.text.strip() if odds_elem else "N/A"
                    outcome_text = "Over" if i == 0 else "Under"  # No group title available
                    outcomes.append({"outcome": outcome_text, "odds": odds})
            else:
                for i, button in enumerate(odds_buttons):
                    outcome_elem = button.find("span", class_="OddsButton__Text")
                    odds_elem = button.find("span", class_="OddsButton__Odds")
                    outcome_text = (outcome_elem.text.strip() if outcome_elem and outcome_elem.text.strip() else
                                    button.get('title', '').strip() or
                                    (market_headers[i] if i < len(market_headers) else f"Option {i+1}"))
                    odds = odds_elem.text.strip() if odds_elem else "N/A"
                    outcomes.append({"outcome": outcome_text, "odds": odds})
            market_dict["groups"].append({"group_title": None, "outcomes": outcomes})
        
        all_markets.append(market_dict)
    
    match_object = {"match_title": match_title, "markets": all_markets}
    print(f"Time to parse {match_title}: {time.time() - initial_time:.2f} seconds")
    return match_object

# Fetcher thread function
def fetcher(queue, urls, driver):
    for url in urls:
        match_title, source = fetch_page_source(driver, url)
        queue.put((match_title, source))
    # Signal end of fetching (one None is sufficient; main thread adds more for each parser)
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
    with open('matches/uel/match_urls.json', 'r', encoding='utf-8') as f:
        match_urls = json.load(f)
    
    # Initialize queue and results list
    queue = Queue()
    results = []
    
    # Set up WebDriver once for all URLs
        # In your driver setup inside main(), add these lines:
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--log-level=3")  # suppress driver debug logs
    chrome_options.add_experimental_option('excludeSwitches', ['enable-logging'])
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
    with open("odds/UEL_odds.json", "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=4)
    
    print(f"Processed {len(results)} matches. Odds data saved to odds/UEL_odds.json")

if __name__ == "__main__":
    main()