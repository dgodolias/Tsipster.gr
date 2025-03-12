import json
import math
import random
import torch
import torch.nn as nn
import torch.optim as optim
from pathlib import Path

# Load user profile
with open('profile/user_profile.json', 'r', encoding='utf-8') as f:
    user_profile = json.load(f)

# Load odds data
with open('odds/UEL_odds.json', 'r', encoding='utf-8') as f:
    odds_data = json.load(f)

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

# Initialize neural network
input_size = len(market_types) + 1
model = BetPredictor(input_size)
optimizer = optim.Adam(model.parameters(), lr=0.01)
criterion = nn.BCELoss()

# Load saved model state if exists
model_file = Path('nn_model.pth')
if model_file.exists():
    model.load_state_dict(torch.load(model_file, weights_only=True))
    print("Loaded saved neural network state.")
else:
    print("No saved model found. Starting with a fresh neural network.")

model.eval()

# User input
N = int(input("Enter number of bets: "))
A = float(input("Enter minimum total odds: "))
B = float(input("Enter maximum total odds: "))

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

# Select bets with dynamic odds filtering
current_total_odds = 1.0
selected_bets = []
used_matches = set()

for k in range(N):
    low, high = get_next_odds_range(current_total_odds, k, N, A, B)
    print(f"Selecting bet {k+1}: Odds range [{low:.2f}, {high:.2f}]")
    
    # Filter bets within the current odds range and from unused matches
    available_bets = [bet for bet in bets if bet['match'] not in used_matches and low <= bet['odds'] <= high]
    
    if not available_bets:
        print("No bets available in range. Widening search.")
        available_bets = [bet for bet in bets if bet['match'] not in used_matches]
        if not available_bets:
            print("No more unique match bets available.")
            break
    
    # Score available bets
    for bet in available_bets:
        features = get_bet_features(bet, market_types)
        with torch.no_grad():
            nn_score = model(features).item()
        base_score = bet['preference_score'] * nn_score
        if random.random() < 0.2:
            base_score *= random.uniform(0.8, 1.2)
        bet['total_score'] = base_score
    
    # Select the highest-scored bet
    best_bet = max(available_bets, key=lambda bet: bet['total_score'])
    selected_bets.append(best_bet)
    used_matches.add(best_bet['match'])
    current_total_odds *= best_bet['odds']

# Training data collection
training_data = []

while True:
    print("\nCurrent Betting Slip:")
    for i, bet in enumerate(selected_bets, 1):
        group_str = f" {bet['group']}" if bet['group'] else ""
        print(f"{i}. {bet['match']} - {bet['market']}{group_str}: {bet['outcome']} @ {bet['odds']}")
    user_input = input("Enter indices to reject (e.g., '1 3') or '-' to accept: ")
    
    if user_input.strip() == '-':
        for bet in selected_bets:
            features = get_bet_features(bet, market_types)
            training_data.append((features, torch.tensor([1.0], dtype=torch.float32)))
        break
    else:
        try:
            reject_indices = [int(x) - 1 for x in user_input.split()]
            if any(i < 0 or i >= len(selected_bets) for i in reject_indices):
                print("Invalid indices. Try again.")
                continue
            
            for i in reject_indices:
                bet = selected_bets[i]
                features = get_bet_features(bet, market_types)
                training_data.append((features, torch.tensor([0.0], dtype=torch.float32)))
            
            selected_bets = [bet for i, bet in enumerate(selected_bets) if i not in reject_indices]
            current_total_odds = math.prod(bet['odds'] for bet in selected_bets)
            used_matches = set(bet['match'] for bet in selected_bets)
            
            while len(selected_bets) < N:
                low, high = get_next_odds_range(current_total_odds, len(selected_bets), N, A, B)
                available_bets = [bet for bet in bets if bet['match'] not in used_matches and low <= bet['odds'] <= high]
                if not available_bets:
                    available_bets = [bet for bet in bets if bet['match'] not in used_matches]
                if not available_bets:
                    print("No more unique match bets available.")
                    break
                
                for bet in available_bets:
                    features = get_bet_features(bet, market_types)
                    with torch.no_grad():
                        nn_score = model(features).item()
                    base_score = bet['preference_score'] * nn_score
                    if random.random() < 0.2:
                        base_score *= random.uniform(0.8, 1.2)
                    bet['total_score'] = base_score
                
                best_bet = max(available_bets, key=lambda bet: bet['total_score'])
                selected_bets.append(best_bet)
                used_matches.add(best_bet['match'])
                current_total_odds *= best_bet['odds']
        except ValueError:
            print("Invalid input. Please enter numbers separated by spaces or '-' to accept.")
            continue

# Train the neural network
if training_data:
    model.train()
    for features, label in training_data:
        optimizer.zero_grad()
        output = model(features)
        loss = criterion(output, label)
        loss.backward()
        optimizer.step()
    model.eval()
    torch.save(model.state_dict(), 'nn_model.pth')
    print("Neural network updated and saved.")

# Display final betting slip
print("\nFinal Betting Slip:")
for bet in selected_bets:
    group_str = f" {bet['group']}" if bet['group'] else ""
    print(f"- {bet['match']} - {bet['market']}{group_str}: {bet['outcome']} @ {bet['odds']}")
total_odds = math.prod(bet['odds'] for bet in selected_bets)
print(f"Total Odds: {total_odds:.2f}")