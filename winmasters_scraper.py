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

def fetch_and_extract_all_odds(url):
    try:
        # Set up Chrome options for headless browsing
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")  # Disable GPU to reduce errors
        
        # Initialize the WebDriver
        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
        
        # Load the page
        driver.get(url)
        
        # Wait for the iframe to load
        WebDriverWait(driver, 15).until(EC.presence_of_element_located((By.ID, "SportsIframe")))
        
        # Switch to the iframe
        driver.switch_to.frame("SportsIframe")
        
        # First, extract the match title
        match_title = "Unknown Match"
        try:
            # Wait for the match header to load
            WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CLASS_NAME, "MatchDetailsHeader__Participants")))
            
            # Extract home team name
            home_team_elem = driver.find_element(By.CLASS_NAME, "MatchDetailsHeader__PartName--Home")
            home_team = home_team_elem.text if home_team_elem else "Home"
            
            # Extract away team name
            away_team_elem = driver.find_element(By.CLASS_NAME, "MatchDetailsHeader__PartName--Away")
            away_team = away_team_elem.text if away_team_elem else "Away"
            
            # Create match title
            match_title = f"{home_team} vs {away_team}"
            print(f"Found match: {match_title}")
        except Exception as e:
            print(f"Could not extract match title: {e}")
        
        # Wait for market containers to appear
        WebDriverWait(driver, 15).until(EC.presence_of_element_located((By.CLASS_NAME, "MarketContainer")))
        
        # Allow extra time for all dynamic content to load
        time.sleep(5)
        
        # Get the page source
        iframe_source = driver.page_source
        
        # Parse with BeautifulSoup
        soup = BeautifulSoup(iframe_source, "html.parser")
        
        # Find all market articles
        markets = soup.find_all("article", class_="Market")
        
        if not markets:
            print(f"No markets found for URL: {url}. The page might not have loaded correctly.")
            driver.quit()
            return None
        
        # List to hold all market data
        all_markets = []
        
        # Iterate through each market
        for market in markets:
            # Extract market name
            market_name_elem = market.find("span", class_="Market__CollapseText")
            market_name = market_name_elem.text.strip() if market_name_elem else "Unknown Market"
            
            # Extract market-level headers
            market_headers_wrapper = market.find("ul", class_="Market__Headers")
            market_headers = [header.text.strip() for header in market_headers_wrapper.find_all("li", class_="Market__Header")] if market_headers_wrapper else []
            
            # Find odds groups
            odds_groups = market.find_all("ul", class_="Market__OddsGroup")
            
            market_dict = {"market_name": market_name, "groups": []}
            
            if odds_groups:
                for group in odds_groups:
                    # Extract group title
                    group_title_elem = group.find("li", class_="Market__OddsGroupTitle")
                    group_title = group_title_elem.text.strip() if group_title_elem else None
                    
                    # Extract odds buttons for the group
                    odds_buttons = group.find_all("button", class_="OddsButton")
                    outcomes = []
                    
                    for i, button in enumerate(odds_buttons):
                        outcome_elem = button.find("span", class_="OddsButton__Text")
                        odds_elem = button.find("span", class_="OddsButton__Odds")
                        
                        # Determine outcome text
                        outcome_text = ""
                        if outcome_elem and outcome_elem.text.strip():
                            outcome_text = outcome_elem.text.strip()
                        elif button.get('title', '').strip():
                            outcome_text = button.get('title').strip()
                        elif market_headers and i < len(market_headers):
                            outcome_text = market_headers[i]
                        else:
                            outcome_text = f"Option {i+1}"
                        
                        odds = odds_elem.text.strip() if odds_elem else "N/A"
                        outcomes.append({"outcome": outcome_text, "odds": odds})
                    
                    # Add group to market
                    market_dict["groups"].append({"group_title": group_title, "outcomes": outcomes})
            else:
                # No groups, treat as a single group with no title
                outcomes = []
                odds_buttons = market.find_all("button", class_="OddsButton")
                for i, button in enumerate(odds_buttons):
                    outcome_elem = button.find("span", class_="OddsButton__Text")
                    odds_elem = button.find("span", class_="OddsButton__Odds")
                    
                    # Determine outcome text
                    outcome_text = ""
                    if outcome_elem and outcome_elem.text.strip():
                        outcome_text = outcome_elem.text.strip()
                    elif button.get('title', '').strip():
                        outcome_text = button.get('title').strip()
                    elif market_headers and i < len(market_headers):
                        outcome_text = market_headers[i]
                    else:
                        outcome_text = f"Option {i+1}"
                    
                    odds = odds_elem.text.strip() if odds_elem else "N/A"
                    outcomes.append({"outcome": outcome_text, "odds": odds})
                
                # Add a single group with no title
                market_dict["groups"].append({"group_title": None, "outcomes": outcomes})
            
            # Add market to the list
            all_markets.append(market_dict)
        
        # Create match object with title and markets
        match_object = {
            "match_title": match_title,
            "markets": all_markets
        }
        
        # Clean up
        driver.quit()
        
        return match_object
        
    except Exception as e:
        print(f"Error occurred for URL {url}: {e}")
        if 'driver' in locals():
            driver.quit()
        return None

def main():
    # Load match URLs
    with open('match_urls.json', 'r', encoding='utf-8') as f:
        match_urls = json.load(f)
    
    all_matches = []
    
    # Process each URL sequentially
    for i, url in enumerate(match_urls):
        print(f"Processing match {i+1} of {len(match_urls)}: {url}")
        match_data = fetch_and_extract_all_odds(url)
        if match_data:
            all_matches.append(match_data)  # Add the complete match object
        print(f"Completed match {i+1} of {len(match_urls)}")
    
    # Save all odds data to JSON
    with open("odds.json", "w", encoding="utf-8") as f:
        json.dump(all_matches, f, ensure_ascii=False, indent=4)
    
    print("Odds data successfully saved to odds.json")

if __name__ == "__main__":
    main()