# Tsipster - Web-based Bet Suggestor

Tsipster is a web application that suggests bets based on machine learning and user preferences.

## Setup Instructions

1. Make sure you have Python 3.6+ installed
2. Install the required dependencies:
   ```
   pip install flask flask_cors torch selenium beautifulsoup4 webdriver_manager
   ```
3. Run the setup script to create necessary directories:
   ```
   python setup_directories.py
   ```
4. Run the Winmasters scraper to get real match data:
   ```
   python scrapers/winmasters_scraper.py
   ```

## Running the Application

1. Navigate to the Tsipster directory in your command prompt or terminal
2. Run the Flask backend:
   ```
   python app.py
   ```
3. Open your web browser and go to: http://localhost:5000

## Using the Flutter App (Optional)

If you prefer to use the Flutter frontend:

1. Make sure Flutter is installed on your system
2. Navigate to the Flutter project directory:
   ```
   cd flutter_tsipster
   ```
3. Get the dependencies:
   ```
   flutter pub get
   ```
4. Run the app:
   ```
   flutter run -d chrome
   ```

## Features

- Web-based interface
- Machine learning-powered bet suggestions
- Dynamic odds calculations
- Option to accept or reject specific bets
- Automatic replacement of rejected bets
- Responsive design that works on desktop and mobile

## Data Sources

The application currently uses odds data from:
- Winmasters (Europa League matches)
- Can be extended to support other sources

When a bet is rejected, the system will find a replacement from the same match to maintain the betting slip structure.

# Tsipster.gr - Sports Betting Odds Scraper

## Winmasters Scraper System

### Architecture Overview

The Winmasters scraper system uses a two-step process to efficiently collect betting odds:

1. **Match URL Collection** (`winmasters_match_getter.py`): Identifies and saves all match URLs from tournament pages
2. **Odds Extraction** (`winmasters_scraper.py`): Processes each match URL to extract detailed betting odds

This separation provides better performance, flexibility, and reliability.

### How Tournament Scraping Works

The system starts with tournament URLs that point to pages listing multiple matches:

```python
tournaments = [
    (
        "https://www.winmasters.gr/el/sports/i/tournament-location/...europa-league...",
        "Europa League"
    ),
    (
        "https://www.winmasters.gr/el/sports/i/tournament-location/...champions-league...",
        "Champions League"
    ),
    # Additional tournaments...
]
```

#### Step 1: Match URL Collection
- The tournament URL is opened in a headless browser
- All match links are extracted from the tournament page
- These links are saved to `matches/winmasters/{tournament_name}/match_urls.json`

#### Step 2: Odds Extraction
- Each match URL is processed to extract betting odds
- Results are combined into tournament-specific files
- A final combined output is created at `data/winmasters_data.json`

### Performance Benefits

This two-step architecture provides significant benefits:

1. **Caching**: Match URLs can be cached and reused without re-scraping tournament pages
2. **Resilience**: If odds scraping fails for some matches, you don't need to re-fetch all match URLs
3. **Scheduling**: Match URLs (which change less frequently) can be updated on a different schedule than odds (which change more often)
4. **Resource Efficiency**: Separating the process allows for better resource allocation

### Command-Line Options

The scraper supports several modes for flexibility:

- **Normal mode**: Fetches all match URLs and scrapes all odds
  ```
  python winmasters_scraper.py
  ```
  
- **Single tournament mode**: Only processes one tournament
  ```
  python winmasters_scraper.py single
  ```
  
- **Test mode**: Only tests URL fetching without processing odds
  ```
  python winmasters_scraper.py test
  ```
  
- **Fix JSON mode**: Repairs an existing JSON output file
  ```
  python winmasters_scraper.py fix-json
  ```

### Data Flow Diagram

```
Tournament URL → [Match URL Getter] → Match URLs → [Odds Scraper] → Betting Odds
                                        ↓
                                      JSON Files
                                        ↓
                                      [Odds Scraper]
```

### File Structure

```
scrapers/
  ├── winmasters_match_getter.py  # Collects match URLs from tournament pages
  └── winmasters_scraper.py       # Extracts odds from individual match pages
matches/
  └── winmasters/
      ├── europa_league/
      │   └── match_urls.json     # Cached match URLs for Europa League
      ├── champions_league/
      │   └── match_urls.json     # Cached match URLs for Champions League
      └── ...                     # Other tournaments
odds/
  └── winmasters/
      ├── europa_league/
      │   └── europa_league_odds_winmasters.json  # Tournament-specific odds
      ├── champions_league/
      │   └── champions_league_odds_winmasters.json
      └── ...
data/
  └── winmasters_data.json        # Combined odds data from all tournaments
```

## Technical Implementation

The system uses Selenium WebDriver with Chrome in headless mode to navigate and scrape the betting site. BeautifulSoup is used for HTML parsing, and the data is stored in JSON format for flexibility and ease of use.

Error handling ensures the system is robust against network issues and site changes, with detailed logging for troubleshooting.

## Contributors

- [Your Name]

## License

[Your License]

Copyright © 2025 Tsipster
