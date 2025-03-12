import json
import math
import random
import torch
import torch.nn as nn
import torch.optim as optim
from pathlib import Path

# Load user profile
with open('user_profile.json', 'r', encoding='utf-8') as f:
    user_profile = json.load(f)

# Load odds data
with open('odds.json', 'r', encoding='utf-8') as f:
    odds_data = json.load(f)

# Define bet type categorization
def get_bet_type(market_name):
    if "Over/Under" in market_name:
        return "Over/Under"
    elif "Να Σκοράρουν Και Οι Δύο Ομάδες" in market_name:
        return "Goal-Goal"
    elif "Τελικό Αποτέλεσμα" in market_name or "Αποτέλεσμα" in market_name:
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
    market_type = get_bet_type(bet['market'])
    # One-hot encode market type
    market_vector = [1 if mt == market_type else 0 for mt in market_types]
    # Normalize odds (assuming odds range from 1 to 1000)
    odds_normalized = (bet['odds'] - 1.0) / 999.0
    return torch.tensor(market_vector + [odds_normalized], dtype=torch.float32)

# Calculate preference score
def calculate_bet_score(bet, user_profile):
    market_type = get_bet_type(bet['market'])
    return user_profile['preferences'].get(market_type, 1)

# Collect bets with match information
bets = []
market_types = ["Over/Under", "Goal-Goal", "Final Result", "Handicap", "Player-Specific", "Other"]

# Iterate over each match and its markets (modified to include match title)
for match in odds_data:
    match_title = match['match_title']
    for market in match['markets']:
        market_name = market['market_name']
        for group in market['groups']:
            group_title = group['group_title']
            for outcome in group['outcomes']:
                if outcome['odds'] != "N/A":  # Skip invalid odds
                    odds = float(outcome['odds'])
                    bet = {
                        'match': match_title,  # Added match information
                        'market': market_name,
                        'group': group_title,
                        'outcome': outcome['outcome'],
                        'odds': odds
                    }
                    bet['preference_score'] = calculate_bet_score(bet, user_profile)
                    bets.append(bet)

# Initialize neural network
input_size = len(market_types) + 1  # Market type one-hot + odds
model = BetPredictor(input_size)
optimizer = optim.Adam(model.parameters(), lr=0.01)
criterion = nn.BCELoss()

# Load saved model state if exists
model_file = Path('nn_model.pth')
if model_file.exists():
    model.load_state_dict(torch.load(model_file))
    print("Loaded saved neural network state.")
else:
    print("No saved model found. Starting with a fresh neural network.")

model.eval()

# User input
N = int(input("Enter number of bets: "))
A = float(input("Enter minimum total odds: "))
B = float(input("Enter maximum total odds: "))

# Calculate target odds range per bet using nth root method
low = A ** (1.0 / N)
high = B ** (1.0 / N)
midpoint = (low + high) / 2
print(f"Target odds per bet: {low:.2f} - {high:.2f}")

# Filter bets within the target odds range
filtered_bets = [bet for bet in bets if low <= bet['odds'] <= high]

# Score bets with neural network and preference, with slight randomness for exploration
for bet in filtered_bets:
    features = get_bet_features(bet, market_types)
    with torch.no_grad():
        nn_score = model(features).item()
    base_score = bet['preference_score'] * nn_score
    if random.random() < 0.2:
        base_score *= random.uniform(0.8, 1.2)
    bet['total_score'] = base_score

# Sort bets by total_score descending
sorted_bets = sorted(filtered_bets, key=lambda bet: bet['total_score'], reverse=True)

# Select bets ensuring only one bet per match
selected_bets = []
used_matches = set()
next_idx = 0
for bet in sorted_bets:
    if bet['match'] not in used_matches:
        selected_bets.append(bet)
        used_matches.add(bet['match'])
    if len(selected_bets) == N:
        break

if len(selected_bets) < N:
    print(f"Not enough unique match bets available. Found {len(selected_bets)}, need {N}.")
    exit()

# Training data collection
training_data = []

while True:
    print("\nCurrent Betting Slip:")
    for i, bet in enumerate(selected_bets, 1):
        group_str = f" {bet['group']}" if bet['group'] else ""
        print(f"{i}. {bet['match']} - {bet['market']}{group_str}: {bet['outcome']} @ {bet['odds']}")
    user_input = input("Enter indices to reject (e.g., '1 3') or '-' to accept: ")
    
    if user_input.strip() == '-':
        # Accept current bets (positive examples)
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
            
            # Collect rejected bets as negative examples
            for i in reject_indices:
                bet = selected_bets[i]
                features = get_bet_features(bet, market_types)
                training_data.append((features, torch.tensor([0.0], dtype=torch.float32)))
            
            # Remove rejected bets
            selected_bets = [bet for i, bet in enumerate(selected_bets) if i not in reject_indices]
            
            # Add new bets ensuring unique matches
            while len(selected_bets) < N and next_idx < len(sorted_bets):
                next_bet = sorted_bets[next_idx]
                next_idx += 1
                if next_bet['match'] not in [bet['match'] for bet in selected_bets]:
                    selected_bets.append(next_bet)
            
            if len(selected_bets) < N:
                print("Not enough remaining unique match bets to complete the slip.")
                break
        except ValueError:
            print("Invalid input. Please enter numbers separated by spaces or '-' to accept.")
            continue

# Train the neural network with collected training data
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
