import json
import os
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
        tournament_url (str): The URL of the tournament page to scrape.
    
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
        chrome_options.add_argument("--log-level=3")
        chrome_options.add_experimental_option('excludeSwitches', ['enable-logging'])
        
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

def extract_tournament_name(tournament_url):
    """
    Extract a human-readable tournament name from the URL.
    
    Args:
        tournament_url (str): URL of the tournament page
        
    Returns:
        str: Human-readable tournament name
    """
    # Try to extract the tournament name from the URL path
    parts = tournament_url.split('/')
    for part in reversed(parts):
        if part and part not in ['tournament-location', 'el', 'en', 'sports', 'i']:
            # Clean up the part to make it more readable
            if part.isdigit() or len(part) > 30:  # Skip numeric IDs or very long strings
                continue
            return part.replace('-', ' ').title()
    
    # Fallback to a generic name if extraction fails
    return "Unknown Tournament"

def save_match_urls(tournament_name, match_urls):
    """
    Save the match URLs to a JSON file in a tournament-specific directory.
    
    Args:
        tournament_name (str): Name of the tournament
        match_urls (list): List of match URLs
    """
    # Create a safe directory name from the tournament name
    dir_name = tournament_name.lower().replace(' ', '_')
    
    # Create the directories if they don't exist
    os.makedirs(f"matches/winmasters/{dir_name}", exist_ok=True)
    
    # Save the match URLs to a JSON file
    with open(f"matches/winmasters/{dir_name}/match_urls.json", "w", encoding="utf-8") as f:
        json.dump(match_urls, f, ensure_ascii=False, indent=4)
    
    print(f"\nMatch URLs saved to 'matches/winmasters/{dir_name}/match_urls.json'.")

if __name__ == "__main__":
    # Example tournaments to scrape
    tournaments = [
        (
            "https://www.winmasters.gr/el/sports/i/coupon/%CF%80%CE%BF%CE%B4%CF%8C%CF%83%CF%86%CE%B1%CE%B9%CF%81%CE%BF/1/location/239341156955492352",
            "Europa League"
        ),
        (
            "https://www.winmasters.gr/el/sports/i/tournament-location/%CF%80%CE%BF%CE%B4%CF%8C%CF%83%CF%86%CE%B1%CE%B9%CF%81%CE%BF/1/%CE%B1%CE%B3%CE%B3%CE%BB%CE%AF%CE%B1/77/premier-league-2024-2025/237845454844760064",
            "Premier League"
        ),
        (
            "https://www.winmasters.gr/el/sports/i/tournament-location/%CF%80%CE%BF%CE%B4%CF%8C%CF%83%CF%86%CE%B1%CE%B9%CF%81%CE%BF/1/%CE%B5%CE%BB%CE%BB%CE%AC%CE%B4%CE%B1/91/super-league-1-2024-2025/237881144163864576",
            "Super League 1"
        ),
        (
            "https://www.winmasters.gr/el/sports/i/tournament-location/%CF%80%CE%BF%CE%B4%CF%8C%CF%83%CF%86%CE%B1%CE%B9%CF%81%CE%BF/1/%CE%B9%CF%83%CF%80%CE%B1%CE%BD%CE%AF%CE%B1/65/laliga-2024-2025/238295245543346176",
            "La Liga"
        )
    ]
    
    for tournament_url, tournament_name in tournaments:
        # If tournament name is not provided, extract it from URL
        if not tournament_name:
            tournament_name = extract_tournament_name(tournament_url)
        
        print(f"\nScraping tournament: {tournament_name}")
        
        # Fetch the match URLs
        match_urls = fetch_match_urls(tournament_url)
        
        # Display the results
        if match_urls:
            print(f"\nMatch URLs extracted for {tournament_name}:")
            for idx, url in enumerate(match_urls, 1):
                print(f"{idx}. {url[:100]}..." if len(url) > 100 else f"{idx}. {url}")
            
            # Save to a JSON file for later use
            save_match_urls(tournament_name, match_urls)
        else:
            print(f"No match URLs were extracted for {tournament_name}.")
