import os
import json
from pathlib import Path

def create_directories():
    """Create all necessary directories for the application."""
    # Create base directories
    directories = [
        'odds/winmasters',
        'matches/winmasters/uel',
        'profile',
        'static/images',
        'static/css',
        'static/js',
        'templates',
        'scrapers',
        'flutter_tsipster/assets/images',
        'flutter_tsipster/assets/data'
    ]
    
    for directory in directories:
        os.makedirs(directory, exist_ok=True)
        print(f"Created directory: {directory}")
    
    # Create default user profile if it doesn't exist
    profile_path = 'profile/user_profile.json'
    if not os.path.exists(profile_path):
        default_profile = {
            "preferences": {
                "Over/Under": 1.2,
                "Goal-Goal": 1.0,
                "Final Result": 1.1,
                "1X2": 1.3,
                "Handicap": 0.9,
                "Player-Specific": 0.8,
                "Other": 0.7
            },
            "leagues": ["Europa League"],
            "risk_tolerance": 4,
            "preferred_odds_range": [1.5, 2.0],
            "live_betting": "No",
            "favorite_teams": ["Rangers"]
        }
        
        with open(profile_path, 'w', encoding='utf-8') as f:
            json.dump(default_profile, f, indent=4)
        print(f"Created default profile: {profile_path}")
    
    # Create empty output file if needed
    output_path = 'odds/winmasters/UEL_odds.json'
    if not os.path.exists(output_path):
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write('[]')
        print(f"Created empty output file: {output_path}")
        print("IMPORTANT: Run the winmasters scraper to populate with real data")

if __name__ == "__main__":
    create_directories()
    print("\nDirectory setup complete.")
    print("Next steps:")
    print("1. Run the winmasters scraper: python scrapers/winmasters_scraper.py")
    print("2. Start the Flask server: python app.py")
    print("3. Start the Flutter app: cd flutter_tsipster && flutter run -d chrome")
