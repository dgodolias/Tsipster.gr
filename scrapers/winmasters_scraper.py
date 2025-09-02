import json
import csv
import os
import logging
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

# Set up logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(levelname)s - %(message)s',
                    handlers=[
                        logging.FileHandler("winmasters_scraper.log"),
                        logging.StreamHandler()
                    ])
logger = logging.getLogger(__name__)

def truncate_url(url):
    return url[:100] + "..." if len(url) > 100 else url

def fetch_page_source(driver, url):
    try:
        logger.info(f"Fetching {truncate_url(url)}")
        initial_time = time.time()
        driver.get(url)
        logger.info(f"Successfully retrieved the initial HTML page for {truncate_url(url)}")
        
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "SportsIframe")))
        driver.switch_to.frame("SportsIframe")
        
        match_title = "Unknown Match"
        home_team = "Home"
        away_team = "Away"
        try:
            WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CLASS_NAME, "MatchDetailsHeader__Participants")))
            home_team = driver.find_element(By.CLASS_NAME, "MatchDetailsHeader__PartName--Home").text or "Home"
            away_team = driver.find_element(By.CLASS_NAME, "MatchDetailsHeader__PartName--Away").text or "Away"
            match_title = f"{home_team} vs {away_team}"
            logger.info(f"Found match: {match_title}")
        except Exception as e:
            logger.error(f"Could not extract match title for {truncate_url(url)}: {e}")
        
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CLASS_NAME, "MarketContainer")))
        source = driver.page_source
        
        logger.info(f"Time to fetch {truncate_url(url)}: {time.time() - initial_time:.2f} seconds")
        return home_team, away_team, source
    except Exception as e:
        logger.error(f"Error fetching {truncate_url(url)}: {e}")
        return "Home", "Away", None

def parse_source(home_team, away_team, source, tournament_name=None):
    if source is None:
        return None
    
    logger.info(f"Parsing data for {home_team} vs {away_team}")
    initial_time = time.time()
    soup = BeautifulSoup(source, "html.parser")
    markets = soup.find_all("article", class_="Market")
    
    if not markets:
        logger.warning(f"No markets found for {home_team} vs {away_team}")
        return None
    
    all_markets = []
    for market in markets:
        # ...existing code...
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
                
                if is_over_under and len(odds_buttons) == 2:
                    for i, button in enumerate(odds_buttons):
                        odds_elem = button.find("span", class_="OddsButton__Odds")
                        odds = odds_elem.text.strip() if odds_elem else "N/A"
                        outcome_text = f"Over {group_title}" if i == 0 else f"Under {group_title}"
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
                
                market_dict["groups"].append({"group_title": group_title, "outcomes": outcomes})
        else:
            outcomes = []
            odds_buttons = market.find_all("button", class_="OddsButton")
            if is_over_under and len(odds_buttons) == 2:
                for i, button in enumerate(odds_buttons):
                    odds_elem = button.find("span", class_="OddsButton__Odds")
                    odds = odds_elem.text.strip() if odds_elem else "N/A"
                    outcome_text = "Over" if i == 0 else "Under"
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
    
    # Ensure we have required fields
    match_object = {
        "home_team": home_team, 
        "away_team": away_team, 
        "markets": all_markets,
        "datetime": time.strftime("%Y-%m-%dT%H:%M:%S")
    }
    
    # Always include tournament if provided
    if tournament_name:
        match_object["tournament"] = tournament_name
        
    logger.info(f"Time to parse {home_team} vs {away_team}: {time.time() - initial_time:.2f} seconds")
    
    # Validate the match object before returning
    if not validate_match_object(match_object):
        logger.error(f"Invalid match object for {home_team} vs {away_team}")
        return None
        
    return match_object

def validate_match_object(match_object):
    """Validate that a match object has all required fields and valid data."""
    required_fields = ["home_team", "away_team", "markets", "datetime"]
    
    # Check for required fields
    for field in required_fields:
        if field not in match_object:
            logger.error(f"Match is missing required field: {field}")
            return False
            
    # Check that home_team and away_team are not empty
    if not match_object["home_team"] or not match_object["away_team"]:
        logger.error(f"Match has empty team name: {match_object.get('home_team', 'N/A')} vs {match_object.get('away_team', 'N/A')}")
        return False
        
    # Check that markets is a non-empty list
    if not isinstance(match_object["markets"], list) or not match_object["markets"]:
        logger.error(f"Match has invalid markets: {match_object.get('markets', 'N/A')}")
        return False
        
    # Validate each market
    for market in match_object["markets"]:
        if "market_name" not in market or "groups" not in market:
            logger.error(f"Market is missing required fields: {market}")
            return False
            
        if not isinstance(market["groups"], list):
            logger.error(f"Market groups is not a list: {market['groups']}")
            return False
            
        # Validate groups
        for group in market["groups"]:
            if "outcomes" not in group:
                logger.error(f"Group is missing outcomes: {group}")
                return False
                
            if not isinstance(group["outcomes"], list):
                logger.error(f"Group outcomes is not a list: {group['outcomes']}")
                return False
    
    return True

def fetcher(queue, urls, driver, tournament_name=None):
    for url in urls:
        home_team, away_team, source = fetch_page_source(driver, url)
        queue.put((home_team, away_team, source, tournament_name))
    queue.put(None)

def parser(queue, results):
    while True:
        item = queue.get()
        if item is None:
            break
        home_team, away_team, source, tournament_name = item
        match_object = parse_source(home_team, away_team, source, tournament_name)
        if match_object:
            results.append(match_object)

def process_tournament(tournament_info, output_dir="data"):
    tournament_url, tournament_name = tournament_info
    
    # This imports functions from the winmasters_match_getter.py file
    from winmasters_match_getter import fetch_match_urls, extract_tournament_name, save_match_urls
    
    if not tournament_name:
        tournament_name = extract_tournament_name(tournament_url)
    
    logger.info(f"Processing tournament: {tournament_name}")
    
    # This calls the fetch_match_urls function to get all match URLs from the tournament page
    match_urls = fetch_match_urls(tournament_url)
    
    if not match_urls:
        logger.warning(f"No matches found for tournament: {tournament_name}")
        return []
    
    # Save the match URLs to a JSON file
    save_match_urls(tournament_name, match_urls)
    
    tournament_dir = tournament_name.lower().replace(' ', '_')
    odds_dir = f"odds/winmasters/{tournament_dir}"
    os.makedirs(odds_dir, exist_ok=True)
    
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--log-level=3")
    chrome_options.add_experimental_option('excludeSwitches', ['enable-logging'])
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
    
    queue = Queue()
    results = []
    
    num_workers = 4
    parsers = []
    for _ in range(num_workers):
        p = Thread(target=parser, args=(queue, results))
        p.start()
        parsers.append(p)
    
    # Pass tournament name to fetcher to ensure it gets attached to each match
    fetcher_thread = Thread(target=fetcher, args=(queue, match_urls, driver, tournament_name))
    fetcher_thread.start()
    
    fetcher_thread.join()
    
    for _ in range(num_workers):
        queue.put(None)
    
    for p in parsers:
        p.join()
    
    driver.quit()
    
    if not results:
        logger.warning(f"No match data was successfully parsed for {tournament_name}")
        return []
    
    # Verify all matches have tournament assigned and all required fields
    valid_results = []
    for match in results:
        if "tournament" not in match:
            match["tournament"] = tournament_name
        
        if validate_match_object(match):
            valid_results.append(match)
        else:
            logger.warning(f"Dropping invalid match: {match.get('home_team', 'Unknown')} vs {match.get('away_team', 'Unknown')}")
    
    # Generate CSV and JSON only with valid results
    if valid_results:
        csv_file = f"{odds_dir}/{tournament_dir}_odds_winmasters.csv"
        with open(csv_file, "w", encoding="utf-8", newline='') as csvfile:
            csvwriter = csv.writer(csvfile, quoting=csv.QUOTE_ALL)
            for match in valid_results:
                home_team = match['home_team']
                away_team = match['away_team']
                for market in match['markets']:
                    for group in market['groups']:
                        row = [home_team, away_team]
                        if 'tournament' in match:
                            row.append(match['tournament'])
                        words = market['market_name'].split()
                        for word in words:
                            clean_word = word.rstrip(',')
                            row.append(clean_word)
                        row.append(":")
                        for outcome in group['outcomes']:
                            row.extend([outcome['outcome'], outcome['odds'], "|"])
                        csvwriter.writerow(row)
        
        json_file = f"{odds_dir}/{tournament_dir}_odds_winmasters.json"
        with open(json_file, "w", encoding="utf-8") as f:
            json.dump(valid_results, f, ensure_ascii=False, indent=4)
        
        logger.info(f"Processed {len(valid_results)} matches in {tournament_name}.")
        logger.info(f"Data saved to {csv_file} and {json_file}")
    
    return valid_results

def scrape_all_tournaments(tournament_list, output_file="data/winmasters_data.json"):
    all_matches = []
    
    for tournament_info in tournament_list:
        tournament_url, tournament_name = tournament_info
        # Process one tournament at a time and verify the results
        api_matches = process_tournament(tournament_info)
        
        # Double-check that all matches from this batch have the right tournament
        for match in api_matches:
            if "tournament" not in match or match["tournament"] != tournament_name:
                match["tournament"] = tournament_name
                logger.info(f"Fixed missing tournament for {match['home_team']} vs {match['away_team']}")
        
        all_matches.extend(api_matches)
    
    if not all_matches:
        logger.error("No valid matches found across all tournaments.")
        return 0
    
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    
    # Sort matches by tournament for better organization in the output file
    all_matches.sort(key=lambda x: x.get("tournament", "Unknown"))
    
    # Final validation before saving
    final_matches = [match for match in all_matches if validate_match_object(match)]
    
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(final_matches, f, ensure_ascii=False, indent=4)
    
    logger.info(f"Total matches processed across all tournaments: {len(final_matches)}")
    logger.info(f"Combined data saved to {output_file}")
    
    # Verify and report on tournament distribution
    tournament_counts = {}
    for match in final_matches:
        tournament = match.get("tournament", "Unknown")
        tournament_counts[tournament] = tournament_counts.get(tournament, 0) + 1
    
    logger.info("\nMatches by tournament:")
    for tournament, count in tournament_counts.items():
        logger.info(f"- {tournament}: {count} matches")
    
    return len(final_matches)

def main():
    tournaments = [
        (
            "https://www.winmasters.gr/el/sports/i/tournament-location/%CF%80%CE%BF%CE%B4%CF%8C%CF%83%CF%86%CE%B1%CE%B9%CF%81%CE%BF/1/%CE%B5%CF%85%CF%81%CF%8E%CF%80%CE%B7/67/europa-league-2024-2025/239341156955492352",
            "Europa League"
        ),
        (
            "https://www.winmasters.gr/el/sports/i/tournament-location/%CF%80%CE%BF%CE%B4%CF%8C%CF%83%CF%86%CE%B1%CE%B9%CF%81%CE%BF/1/%CE%B5%CF%85%CF%81%CF%8E%CF%80%CE%B7/67/champions-league-2024-2025/239341156946103296",
            "Champions League"
        ),
        (
            "https://www.winmasters.gr/el/sports/i/tournament-location/%CF%80%CE%BF%CE%B4%CF%8C%CF%83%CF%86%CE%B1%CE%B9%CF%81%CE%BF/1/%CE%B5%CE%BB%CE%BB%CE%AC%CE%B4%CE%B1/72/super-league-1/239341156992634880",
            "Super League 1"
        ),
        (
            "https://www.winmasters.gr/el/sports/i/tournament-location/%CF%80%CE%BF%CE%B4%CF%8C%CF%83%CF%86%CE%B1%CE%B9%CF%81%CE%BF/1/%CE%B9%CF%83%CF%80%CE%B1%CE%BD%CE%AF%CE%B1/65/laliga-2024-2025/238295245543346176",
            "La Liga"
        )
    ]
    
    import sys
    
    # Default mode - process all tournaments
    process_all = True
    test_mode = False
    fix_json_mode = False
    
    # Check for command line arguments
    if len(sys.argv) > 1:
        if sys.argv[1].lower() == "single":
            process_all = False
            logger.info("Running in single tournament mode (only processing Europa League)")
        elif sys.argv[1].lower() == "test":
            test_mode = True
            logger.info("Running in test mode (only fetching match URLs, not processing odds)")
        elif sys.argv[1].lower() == "fix-json":
            fix_json_mode = True
            logger.info("Running in fix JSON mode (will repair existing data file)")
    
    if fix_json_mode:
        # Try to fix an existing JSON file
        try:
            json_file = "data/winmasters_data.json"
            logger.info(f"Attempting to fix {json_file}")
            
            with open(json_file, "r", encoding="utf-8") as f:
                existing_data = json.load(f)
            
            # Filter out invalid entries and ensure all required fields
            fixed_data = []
            for match in existing_data:
                if validate_match_object(match):
                    fixed_data.append(match)
                else:
                    logger.warning(f"Removing invalid match: {match.get('home_team', 'Unknown')} vs {match.get('away_team', 'Unknown')}")
            
            # Save the fixed data
            backup_file = json_file + ".bak"
            os.rename(json_file, backup_file)
            logger.info(f"Created backup of original file at {backup_file}")
            
            with open(json_file, "w", encoding="utf-8") as f:
                json.dump(fixed_data, f, ensure_ascii=False, indent=4)
            
            logger.info(f"Fixed JSON saved with {len(fixed_data)} valid matches (removed {len(existing_data) - len(fixed_data)} invalid entries)")
            
        except FileNotFoundError:
            logger.error(f"JSON file not found. Please run the scraper first.")
        except json.JSONDecodeError:
            logger.error(f"JSON file is corrupted and cannot be parsed.")
        except Exception as e:
            logger.error(f"Error fixing JSON: {e}")
    elif test_mode:
        from winmasters_match_getter import fetch_match_urls, extract_tournament_name
        # Just test URL fetching for each tournament
        for tournament_url, tournament_name in tournaments:
            if not tournament_name:
                tournament_name = extract_tournament_name(tournament_url)
            logger.info(f"\nTesting URL fetching for tournament: {tournament_name}")
            match_urls = fetch_match_urls(tournament_url)
            if match_urls:
                logger.info(f"Success! Found {len(match_urls)} match URLs for {tournament_name}")
                if len(match_urls) > 0:
                    logger.info(f"First URL: {match_urls[0][:100]}...")
            else:
                logger.error(f"Failed to fetch match URLs for {tournament_name}")
    elif process_all:
        scrape_all_tournaments(tournaments)
    else:
        tournament_info = tournaments[0]
        process_tournament(tournament_info)
    
    logger.info("\nProcessing complete!")

if __name__ == "__main__":
    main()