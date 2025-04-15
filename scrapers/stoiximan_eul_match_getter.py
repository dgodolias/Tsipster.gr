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

def fetch_match_urls(tournament_url):
    """
    Fetches all match URLs from a given tournament page.
    
    Args:
        tournament_url (str): The URL of the tournament page to scrape (e.g., Europa League).
    
    Returns:
        list: A list of match URLs.
    """
    try:
        # Set up Chrome options for headless browsing
        chrome_options = Options()
        chrome_options.add_argument("--headless")  # Run in headless mode (no GUI)
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument("--disable-extensions")
        chrome_options.add_argument("--proxy-server='direct://'")
        chrome_options.add_argument("--proxy-bypass-list=*")
        chrome_options.add_argument("--start-maximized")
        chrome_options.add_argument("--ignore-certificate-errors")
        chrome_options.add_argument("--allow-insecure-localhost")
        chrome_options.add_argument("--disable-application-cache")
        chrome_options.add_argument("--disable-infobars")
        chrome_options.add_argument("--disable-notifications")
        chrome_options.add_argument("--disable-translate")
        chrome_options.add_argument("--disable-features=VizDisplayCompositor")
        chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")
        
        # Initialize the WebDriver
        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
        
        # Load the tournament page
        print(f"Loading page: {tournament_url}")
        driver.get(tournament_url)
        
        # Wait for the match blocks to load
        WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "div[data-qa='league_page_event']"))
        )
        print("Match items detected, waiting for full content to load...")
        
        # Allow extra time for all dynamic content to load
        time.sleep(3)
        
        # Get the page source
        page_source = driver.page_source
        
        # Parse the HTML with BeautifulSoup
        soup = BeautifulSoup(page_source, "html.parser")
        
        # Find all match blocks
        match_blocks = soup.select("div[data-qa='league_page_event']")
        
        if not match_blocks:
            print("No match links found on the page.")
            driver.quit()
            return []
        
        # Extract the href attributes (absolute URLs)
        match_urls = [block.find("a", {"data-qa": "pre-event"})["href"] for block in match_blocks if block.find("a", {"data-qa": "pre-event"})]
        match_urls = ["https://www.stoiximan.gr" + url for url in match_urls]
        print(f"Found {len(match_urls)} match URLs.")
        
        # Clean up: close the WebDriver
        driver.quit()
        
        return match_urls
    
    except Exception as e:
        print(f"An error occurred: {e}")
        if "driver" in locals():
            driver.quit()
        return []

if __name__ == "__main__":
    # Example tournament URL from the provided HTML (Europa League)
    tournament_url = "https://www.stoiximan.gr/sport/podosfairo/diorganoseis/europa-league/188567/"
    
    # Fetch the match URLs
    match_urls = fetch_match_urls(tournament_url)
    
    # Display the results
    if match_urls:
        print("\nMatch URLs extracted:")
        for idx, url in enumerate(match_urls, 1):
            print(f"{idx}. {url}")
        
        # Save to a JSON file for later use
        with open("matches/stoiximan/uel/match_urls.json", "w", encoding="utf-8") as f:
            json.dump(match_urls, f, ensure_ascii=False, indent=4)
        print("\nMatch URLs saved to 'matches/stoiximan/uel/match_urls.json'.")
    else:
        print("No match URLs were extracted.")