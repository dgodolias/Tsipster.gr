import json
import csv
import re
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
    """Truncate URL for logging if it exceeds 100 characters."""
    return url[:100] + "..." if len(url) > 100 else url

def fetch_page_source(driver, url):
    """Fetch the page source for a given URL and extract team names."""
    try:
        print(f"Fetching {truncate_url(url)}")
        initial_time = time.time()
        driver.get(url)
        
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "div[data-marketid]"))
        )
        
        try:
            modal = WebDriverWait(driver, 3).until(
                EC.presence_of_element_located((By.ID, "landing-page-modal"))
            )
            close_button = modal.find_element(By.CSS_SELECTOR, "button.button-close")
            close_button.click()
            print("Closed popup ad")
            WebDriverWait(driver, 3).until(
                EC.invisibility_of_element(modal)
            )
        except:
            try:
                driver.execute_script("""
                    var elements = document.querySelectorAll('#landing-page-modal');
                    for(var i=0; i<elements.length; i++){
                        elements[i].remove();
                    }
                    var overlays = document.querySelectorAll('.sb-modal-overlay');
                    for(var i=0; i<overlays.length; i++){
                        overlays[i].remove();
                    }
                """)
                print("Removed popup using JavaScript")
            except:
                print("No popup ads found or couldn't remove")

        # Get home and away team names
        home_team, away_team = "Unknown Home", "Unknown Away"
        try:
            match_title_elem = driver.find_element(By.TAG_NAME, "h1")
            match_title_text = match_title_elem.text.strip() if match_title_elem else "Unknown Match"
            teams = [team.strip() for team in match_title_text.split('\n')]
            if len(teams) == 2:
                home_team, away_team = teams
            else:
                home_team, away_team = "Unknown Home", "Unknown Away"
            print(f"Found match: {home_team} vs {away_team}")
        except Exception as e:
            print(f"Could not extract team names for {truncate_url(url)}: {e}")
        
        market_divs = driver.find_elements(By.CSS_SELECTOR, "div[data-marketid]")
        
        for i, market_div in enumerate(market_divs):
            try:
                arrow = market_div.find_element(By.CSS_SELECTOR, 
                    "svg.sb-arrow.tw-icon-xs.push-right.tw-icon.tw-fill-n-48-slate.dark\\:tw-fill-n-75-smokey.tw-cursor-pointer")
                if "sb-arrow--collapsed" not in arrow.get_attribute("class"):
                    arrow.click()
                    WebDriverWait(driver, 5).until(
                        EC.presence_of_element_located((By.CLASS_NAME, "selections"))
                    )
                    if i >= int(len(market_divs) * 0.9):
                        time.sleep(0.2)
                    else:
                        time.sleep(0.01)
            except:
                continue
        
        source = driver.page_source
        
        print(f"Time to fetch {truncate_url(url)}: {time.time() - initial_time:.2f} seconds")
        return home_team, away_team, source
    except Exception as e:
        print(f"Error fetching {truncate_url(url)}: {e}")
        return "Unknown Home", "Unknown Away", None

def parse_source(home_team, away_team, source):
    """Parse the page source to extract betting markets and outcomes."""
    if source is None:
        return None
    
    print(f"Parsing data for {home_team} vs {away_team}")
    initial_time = time.time()
    
    soup = BeautifulSoup(source, 'html.parser')
    
    grouped_markets = [
        "Γκολ Over/Under", "Γκολ Over/Under, 1ο Ημίχρονο", "Ασιατικό Χάντικαπ",
        "Ασιατικό Χάντικαπ, 1ο Ημίχρονο", "Κόρνερ Over/Under", "Κάρτες Over/Under",
        "Χάντικαπ"
    ]
    
    markets = []
    market_divs = soup.select('div[data-marketid]')
    
    for market_div in market_divs:
        market_name_elem = market_div.select_one('div.tw-self-center')
        if not market_name_elem:
            continue
        
        market_name = market_name_elem.text.strip()
        
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
        
        if market_name in grouped_markets:
            groups_dict = {}
            for outcome in outcomes:
                match = re.search(r"(Over|Under|\+|-)?\s*([\d.]+)", outcome["outcome"])
                if match:
                    line = match.group(2) if match.group(1) in ["Over", "Under"] else outcome["outcome"]
                    if line not in groups_dict:
                        groups_dict[line] = []
                    groups_dict[line].append(outcome)
                elif "Ισοπαλία" in outcome["outcome"] or market_name == "Χάντικαπ":
                    handicap_match = re.search(r"(\d+:\d+)", market_div.text)
                    line = handicap_match.group(1) if handicap_match else "unknown"
                    if line not in groups_dict:
                        groups_dict[line] = []
                    groups_dict[line].append(outcome)
                else:
                    groups_dict["default"] = groups_dict.get("default", []) + [outcome]
    
            market_groups = [
                {"group_title": line, "outcomes": outcomes}
                for line, outcomes in groups_dict.items()
            ]
        else:
            market_groups = [{"group_title": None, "outcomes": outcomes}]
    
        markets.append({"market_name": market_name, "groups": market_groups})
    
    match_object = {"home_team": home_team, "away_team": away_team, "markets": markets}
    print(f"Time to parse {home_team} vs {away_team}: {time.time() - initial_time:.2f} seconds")
    return match_object

def fetcher(queue, urls):
    """Fetcher thread to retrieve page sources and put them in the queue."""
    for url in urls:
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--log-level=3")
        chrome_options.add_experimental_option('excludeSwitches', ['enable-logging'])
        chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_argument("--window-size=1920,1080")
        
        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
        
        home_team, away_team, source = fetch_page_source(driver, url)
        queue.put((home_team, away_team, source))
        
        driver.quit()
    
    queue.put(None)

def parser(queue, results):
    """Parser thread to process page sources from the queue."""
    while True:
        item = queue.get()
        if item is None:
            break
        home_team, away_team, source = item
        match_object = parse_source(home_team, away_team, source)
        if match_object:
            results.append(match_object)

def main():
    """Main function to orchestrate fetching, parsing, CSV generation, and JSON saving."""
    with open('matches/stoiximan/uel/match_urls.json', 'r', encoding='utf-8') as f:
        match_urls = json.load(f)
    
    queue = Queue()
    results = []
    
    num_workers = 4
    parsers = []
    for _ in range(num_workers):
        p = Thread(target=parser, args=(queue, results))
        p.start()
        parsers.append(p)
    
    fetcher_thread = Thread(target=fetcher, args=(queue, match_urls))
    fetcher_thread.start()
    
    fetcher_thread.join()
    
    for _ in range(num_workers):
        queue.put(None)
    
    for p in parsers:
        p.join()
    
    with open("odds/stoiximan/UEL_odds_stoiximan.csv", "w", encoding="utf-8", newline='') as csvfile:
        csvwriter = csv.writer(csvfile, quoting=csv.QUOTE_ALL)
        for match in results:
            home_team = match['home_team']
            away_team = match['away_team']
            for market in match['markets']:
                for group in market['groups']:
                    row = [home_team, away_team]
                    words = market['market_name'].split()
                    for word in words:
                        clean_word = word.rstrip(',')
                        row.append(clean_word)
                    if group['group_title'] is not None:
                        row.append(group['group_title'])
                    row.append(":")
                    for outcome in group['outcomes']:
                        row.extend([outcome['outcome'], outcome['odds'], "|"])
                    csvwriter.writerow(row)
    
    for match in results:
        for market in match['markets']:
            for group in market['groups']:
                group.pop('group_title', None)
    
    with open("odds/stoiximan/UEL_odds_stoiximan.json", "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=4)
    
    print(f"Processed {len(results)} matches. Odds data saved to odds/stoiximan/UEL_odds_stoiximan.json and odds/stoiximan/UEL_odds_stoiximan.csv")

if __name__ == "__main__":
    main()