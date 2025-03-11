
import requests
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
import time

def fetch_and_extract_all_odds():
    # URL of the event page
    url = "https://www.winmasters.gr/el/sports/i/event/1/%CF%80%CE%BF%CE%B4%CF%8C%CF%83%CF%86%CE%B1%CE%B9%CF%81%CE%BF/%CE%B5%CF%85%CF%81%CF%8E%CF%80%CE%B7/europa-league/%CF%81%CE%AD%CE%B9%CE%BD%CF%84%CE%B6%CE%B5%CF%81%CF%82-%CF%86%CE%B5%CE%BD%CE%AD%CF%81%CE%BC%CF%80%CE%B1%CF%87%CF%84%CF%83%CE%B5/263983735756566528/all"
    
    try:
        # Set up Chrome options for headless browsing
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        
        # Initialize the WebDriver
        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
        
        # Load the page
        driver.get(url)
        
        # Wait for the iframe to load
        WebDriverWait(driver, 15).until(EC.presence_of_element_located((By.ID, "SportsIframe")))
        
        # Switch to the iframe
        driver.switch_to.frame("SportsIframe")
        
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
            print("No markets found. The page might not have loaded correctly.")
            driver.quit()
            return
        
        # Iterate through each market
        for market in markets:
            # Extract market name
            market_name_elem = market.find("span", class_="Market__CollapseText")
            market_name = market_name_elem.text.strip() if market_name_elem else "Unknown Market"
            print(f"\n### {market_name}")
            
            # Check for odds groups (e.g., Over/Under with multiple lines)
            odds_groups = market.find_all("ul", class_="Market__OddsGroup")
            
            if odds_groups:
                for group in odds_groups:
                    # Extract group title (e.g., line value like "1.5" or handicap value)
                    group_title_elem = group.find("li", class_="Market__OddsGroupTitle")
                    group_title = group_title_elem.text.strip() if group_title_elem else None
                    
                    # Extract headers if present (e.g., "Over", "Under")
                    headers_wrapper = market.find("ul", class_="Market__Headers")
                    headers = [header.text.strip() for header in headers_wrapper.find_all("li", class_="Market__Header")] if headers_wrapper else []
                    
                    # Extract odds buttons
                    odds_buttons = group.find_all("button", class_="OddsButton")
                    outcomes = []
                    
                    for button in odds_buttons:
                        outcome_elem = button.find("span", class_="OddsButton__Text")
                        odds_elem = button.find("span", class_="OddsButton__Odds")
                        # Use button title attribute as fallback if outcome_elem is empty
                        outcome = outcome_elem.text.strip() if outcome_elem and outcome_elem.text.strip() else button.get('title', 'N/A')
                        odds = odds_elem.text.strip() if odds_elem else "N/A"
                        outcomes.append((outcome, odds))
                    
                    # Print the group data
                    if group_title:
                        print(f"#### {group_title}")
                    
                    if headers and len(headers) == len(outcomes):
                        for header, (outcome, odds) in zip(headers, outcomes):
                            print(f"- {header}: {odds}")
                    elif outcomes:
                        for outcome, odds in outcomes:
                            print(f"- {outcome}: {odds}")
            else:
                # Handle markets without groups (e.g., simple 1X2 or Yes/No bets)
                odds_buttons = market.find_all("button", class_="OddsButton")
                if odds_buttons:
                    for button in odds_buttons:
                        outcome_elem = button.find("span", class_="OddsButton__Text")
                        odds_elem = button.find("span", class_="OddsButton__Odds")
                        # Use button title attribute as fallback if outcome_elem is empty
                        outcome = outcome_elem.text.strip() if outcome_elem and outcome_elem.text.strip() else button.get('title', 'N/A')
                        odds = odds_elem.text.strip() if odds_elem else "N/A"
                        print(f"- {outcome}: {odds}")
        
        # Clean up
        driver.quit()
        
    except Exception as e:
        print(f"Error occurred: {e}")
        driver.quit()

if __name__ == "__main__":
    fetch_and_extract_all_odds()