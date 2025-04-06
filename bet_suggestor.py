import json
import math
import random
import torch
import torch.nn as nn
import torch.optim as optim
from pathlib import Path

# Load user profile
try:
    with open('profile/user_profile.json', 'r', encoding='utf-8') as f:
        user_profile = json.load(f)
except FileNotFoundError:
    # Default profile if file doesn't exist
    user_profile = {
        "preferences": {
            "Over/Under": 1.0,
            "Goal-Goal": 1.0,
            "Final Result": 1.0,
            "1X2": 1.0,
            "Handicap": 1.0,
            "Player-Specific": 1.0,
            "Other": 1.0
        }
    }
    print("User profile not found, using default")

# Load odds data
try:
    # Try to load winmasters data first
    with open('odds/winmasters/UEL_odds.json', 'r', encoding='utf-8') as f:
        odds_data = json.load(f)
        print(f"Loaded winmasters odds data with {len(odds_data)} matches")
except FileNotFoundError:
    try:
        # Fall back to bet365 data if available
        with open('bet365_output.json', 'r', encoding='utf-8') as f:
            odds_data = json.load(f)
            print(f"Loaded bet365 odds data with {len(odds_data)} matches")
    except FileNotFoundError:
        odds_data = []
        print("No odds data found! Make sure to run the winmasters scraper first.")

# Define bet type categorization
def get_bet_type(market_name, outcome=None):
    if "Over/Under" in market_name:
        return "Over/Under"
    elif "Να Σκοράρουν Και Οι Δύο Ομάδες" in market_name:
        return "Goal-Goal"
    elif "Τελικό Αποτέλεσμα" in market_name or "Αποτέλεσμα" in market_name:
        # Check if it's a 1, X, 2 bet based on outcome
        if outcome in ["Αθλέτικ Μπιλμπάο", "Ισοπαλία", "Ρόμα", "Μάντσεστερ Γιουνάιτεντ", "Σοσιεδάδ"]:
            return "1X2"
        return "Final Result"
    elif "Χάντικαπ" in market_name:
        return "Handicap"
    elif "Σκόρερ" in market_name or "Να Σκοράρει" in market_name:
        return "Player-Specific"
    return "Other"

# Define a simple neural network
class BetPredictor(nn.Module):
    def __init__(self, input_size):
        super(BetPredictor, self).__init__()
        self.fc1 = nn.Linear(input_size, 16)
        self.relu = nn.ReLU()
        self.fc2 = nn.Linear(16, 1)
        self.sigmoid = nn.Sigmoid()

    def forward(self, x):
        x = self.fc1(x)
        x = self.relu(x)
        x = self.fc2(x)
        x = self.sigmoid(x)
        return x

def get_bet_features(bet, market_types):
    market_type = get_bet_type(bet['market'], bet['outcome'])
    market_vector = [1 if mt == market_type else 0 for mt in market_types]
    odds_normalized = (bet['odds'] - 1.0) / 999.0
    return torch.tensor(market_vector + [odds_normalized], dtype=torch.float32)

# Calculate preference score
def calculate_bet_score(bet, user_profile):
    market_type = get_bet_type(bet['market'], bet['outcome'])
    return user_profile['preferences'].get(market_type, 1)

# Collect unique match names to determine max possible bets
unique_matches = set()
for match in odds_data:
    unique_matches.add(match['match_title'])

# Get the max number of unique matches
max_unique_matches = len(unique_matches)
print(f"Maximum available unique matches: {max_unique_matches}")

# Collect bets with match information
bets = []
market_types = ["Over/Under", "Goal-Goal", "Final Result", "1X2", "Handicap", "Player-Specific", "Other"]

for match in odds_data:
    match_title = match['match_title']
    for market in match['markets']:
        market_name = market['market_name']
        for group in market['groups']:
            group_title = group['group_title']
            for outcome in group['outcomes']:
                if outcome['odds'] != "N/A":
                    try:
                        odds = float(outcome['odds'])
                        bet = {
                            'match': match_title,
                            'market': market_name,
                            'group': group_title,
                            'outcome': outcome['outcome'],
                            'odds': odds
                        }
                        bet['preference_score'] = calculate_bet_score(bet, user_profile)
                        bets.append(bet)
                    except ValueError:
                        print(f"Invalid odds value: {outcome['odds']}")

# Initialize neural network
input_size = len(market_types) + 1
model = BetPredictor(input_size)
optimizer = optim.Adam(model.parameters(), lr=0.01)
criterion = nn.BCELoss()

# Load saved model state if exists
model_file = Path('nn_model.pth')
if model_file.exists():
    try:
        model.load_state_dict(torch.load(model_file))
        print("Loaded saved neural network state.")
    except Exception as e:
        print(f"Error loading model: {e}")
else:
    print("No saved model found. Starting with a fresh neural network.")

model.eval()

# Function to calculate dynamic odds range
def get_next_odds_range(current_total_odds, bets_selected, total_bets, min_total_odds, max_total_odds):
    remaining_bets = total_bets - bets_selected
    if remaining_bets <= 0:
        return 1.01, 1000.0  # Default wide range if no bets remain
    
    # Calculate required odds per remaining bet to reach target range
    low = (min_total_odds / current_total_odds) ** (1 / remaining_bets)
    high = (max_total_odds / current_total_odds) ** (1 / remaining_bets)
    
    # Widen the range initially (more for early bets)
    widen_factor = 0.5 * (1 - bets_selected / total_bets)  # Decreases as more bets are selected
    low = max(1.01, low - widen_factor)
    high = min(1000.0, high + widen_factor)
    
    # With 10% probability, allow higher odds (e.g., up to 2.1)
    if random.random() < 0.1:
        low = max(1.01, low * 0.9)
        high = min(1000.0, high * 1.2)  # Allows odds up to ~2.1 or more
    
    return low, high

# Function to get available unique matches count
def get_max_unique_matches():
    return max_unique_matches