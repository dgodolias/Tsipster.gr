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
