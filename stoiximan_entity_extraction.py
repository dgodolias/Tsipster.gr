import json
import re

# Φόρτωση των δεδομένων JSON
with open(r"odds\stoiximan\UEL_odds_stoiximan.json", "r", encoding="utf-8") as f:
    data = json.load(f)

# Ορισμός αγορών όπου τα outcomes είναι ονόματα παικτών
player_outcome_markets = [
    "Να σκοράρει",
    "Πρώτος σκόρερ",
    "Τελευταίος σκόρερ",
    "Να σκοράρει 2+ γκολ",
    "Να σκοράρει 3+ γκολ",
    "Να δεχτεί κάρτα"
]

# Ορισμός καταλήξεων για αγορές που περιέχουν όνομα παίκτη στο όνομα της αγοράς
player_suffixes = [
    " Σουτ στην εστία",
    " Να σκοράρει",
    " Να δεχτεί κάρτα",
    " Να σκοράρει 2+ γκολ",
    " Να σκοράρει 3+ γκολ"
]

# Εξαγωγή ομάδων
teams = []
if data and isinstance(data, list) and len(data) > 0:
    game_data = data[0]
    if "home_team" in game_data:
        teams.append(game_data["home_team"])
    if "away_team" in game_data:
        teams.append(game_data["away_team"])

# Αρχικοποίηση λεξικού για παίκτες και τις ομάδες τους
player_info = {}

# Μοτίβο αναζήτησης για παίκτες με ομάδα σε παρένθεση
team_pattern = re.compile(r'(.*) \((.*)\)$')

# Συνάρτηση για να αφαιρεί την ομάδα από το όνομα παίκτη
def strip_team_info(player_name):
    match = team_pattern.match(player_name)
    if match:
        return match.group(1).strip()
    return player_name

# Εξέταση όλων των αγορών
if data and isinstance(data, list) and len(data) > 0 and "markets" in data[0]:
    for market in data[0]["markets"]:
        market_name = market["market_name"]
        
        # Αν η αγορά είναι στη λίστα player_outcome_markets, εξάγουμε τα outcomes
        if market_name in player_outcome_markets:
            for group in market["groups"]:
                for outcome in group["outcomes"]:
                    player_full = outcome["outcome"].strip()
                    
                    # Φιλτράρισμα για να βεβαιωθούμε ότι είναι όνομα παίκτη
                    if player_full and player_full[0].isupper() and player_full not in ["Κανένας", "Άλλος", *teams]:
                        # Αφαίρεση της ομάδας από το όνομα του παίκτη
                        player_name = strip_team_info(player_full)
                        
                        # Καταχώρηση του παίκτη χωρίς ομάδα
                        if player_name not in player_info:
                            player_info[player_name] = "Unknown"
        
        # Αλλιώς, ελέγχουμε αν το όνομα της αγοράς τελειώνει με κάποια κατάληξη
        else:
            for suffix in player_suffixes:
                if market_name.endswith(suffix):
                    player_full = market_name[:-len(suffix)].strip()
                    
                    if player_full and player_full[0].isupper() and player_full not in teams:
                        # Αφαίρεση της ομάδας από το όνομα του παίκτη
                        player_name = strip_team_info(player_full)
                        
                        # Καταχώρηση του παίκτη χωρίς ομάδα
                        if player_name not in player_info:
                            player_info[player_name] = "Unknown"
                    break

# Δημιουργία λίστας με μοναδικά ονόματα παικτών
clean_players = sorted(player_info.keys())

# Δημιουργία του τελικού λεξικού αντιστοίχισης
placeholder_to_entity_map = {}

if len(teams) > 0:
    placeholder_to_entity_map["TEAM_1"] = teams[0]
if len(teams) > 1:
    placeholder_to_entity_map["TEAM_2"] = teams[1]

for i, player_name in enumerate(clean_players):
    placeholder_to_entity_map[f"PLAYER_{i+1}"] = player_name

# Εκτύπωση του λεξικού ως JSON
print(json.dumps(placeholder_to_entity_map, ensure_ascii=False))