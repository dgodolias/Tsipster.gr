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
        
        # Initialize the WebDriver
        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
        
        # Load the tournament page
        print(f"Loading page: {tournament_url}")
        driver.get(tournament_url)
        
        # Wait for the iframe to load
        WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.ID, "SportsIframe"))
        )
        print("Iframe detected, switching to it...")
        
        # Switch to the iframe where the match list resides
        driver.switch_to.frame("SportsIframe")
        
        # Wait for at least one EventItem to load (indicating match data is present)
        WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.CLASS_NAME, "EventItem"))
        )
        print("Match items detected, waiting for full content to load...")
        
        # Allow extra time for all dynamic content to load
        time.sleep(3)
        
        # Get the page source from the iframe
        iframe_source = driver.page_source
        
        # Parse the HTML with BeautifulSoup
        soup = BeautifulSoup(iframe_source, "html.parser")
        
        # Find all anchor tags with class "EventItem__Indicator" (match links)
        match_links = soup.find_all("a", class_="EventItem__Indicator")
        
        if not match_links:
            print("No match links found on the page.")
            driver.quit()
            return []
        
        # Extract the href attributes (absolute URLs)
        match_urls = [link["href"] for link in match_links if "href" in link.attrs]
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
    tournament_url = (
        "https://www.winmasters.gr/el/sports/i/tournament-location/%CF%80%CE%BF%CE%B4%CF%8C%CF%83%CF%86%CE%B1%CE%B9%CF%81%CE%BF/1/%CE%B5%CF%85%CF%81%CF%8E%CF%80%CE%B7/67/europa-league-2024-2025/239341156955492352"
    )
    
    # Fetch the match URLs
    match_urls = fetch_match_urls(tournament_url)
    
    # Display the results
    if match_urls:
        print("\nMatch URLs extracted:")
        for idx, url in enumerate(match_urls, 1):
            print(f"{idx}. {url}")
        
        # Save to a JSON file for later use
        with open("matches/winmasters/uel/match_urls.json", "w", encoding="utf-8") as f:
            json.dump(match_urls, f, ensure_ascii=False, indent=4)
        print("\nMatch URLs saved to 'match_urls.json'.")
    else:
        print("No match URLs were extracted.")