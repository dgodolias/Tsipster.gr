import json
import re
from stoiximan_entity_extraction import strip_team_info

def anonymize_json(input_file, output_file):
    # Φόρτωση των δεδομένων JSON
    with open(input_file, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    # Εξαγωγή ομάδων
    teams = {}
    team_counter = 1
    
    # Εντοπισμός και αντικατάσταση ομάδων
    for match in data:
        home_team = match["home_team"]
        away_team = match["away_team"]
        
        if home_team not in teams:
            teams[home_team] = f"TEAM_{team_counter}"
            team_counter += 1
        
        if away_team not in teams:
            teams[away_team] = f"TEAM_{team_counter}"
            team_counter += 1
        
        # Αντικατάσταση ομάδων στα δεδομένα
        match["home_team"] = teams[home_team]
        match["away_team"] = teams[away_team]
    
    # Λίστα για να αποθηκεύσουμε όλα τα ονόματα παικτών
    all_players = set()
    
    # Μοτίβο αναζήτησης για παίκτες με ομάδα σε παρένθεση
    team_pattern = re.compile(r'(.*) \((.*)\)$')
    
    # Συλλογή ονομάτων παικτών από market_name και outcome
    for match in data:
        for market in match["markets"]:
            market_name = market["market_name"]
            
            # Έλεγχος για ονόματα παικτών στο όνομα της αγοράς
            player_in_market = None
            for team_name in teams.keys():
                if team_name in market_name:
                    market_name = market_name.replace(team_name, teams[team_name])
                
            # Έλεγχος για ονόματα παικτών σε αγορές με σουτ, κάρτες, γκολ κλπ
            player_market_patterns = [
                r"^(.*) Σουτ στην εστία$",
                r"^(.*) Να σκοράρει$",
                r"^(.*) Να δεχτεί κάρτα$",
                r"^(.*) Προσπάθειες για γκολ$",
                r"^(.*) Αποκρούσεις τερματοφύλακα$"
            ]
            
            for pattern in player_market_patterns:
                match_player = re.match(pattern, market_name)
                if match_player:
                    player_name = match_player.group(1).strip()
                    # Αφαίρεση του ονόματος της ομάδας αν υπάρχει
                    player_name = strip_team_info(player_name)
                    all_players.add(player_name)
            
            # Συλλογή ονομάτων παικτών από outcomes
            for group in market["groups"]:
                for outcome in group["outcomes"]:
                    if "outcome" in outcome:
                        player_name = outcome["outcome"].strip()
                        # Αφαίρεση του ονόματος της ομάδας αν υπάρχει
                        player_name = strip_team_info(player_name)
                        
                        # Έλεγχος αν το outcome είναι πιθανό όνομα παίκτη
                        if player_name and player_name[0].isupper() and len(player_name) > 3 and player_name not in ["Κανένας", "Άλλος"]:
                            # Εξαίρεση αν είναι όνομα ομάδας
                            if player_name not in teams.keys():
                                all_players.add(player_name)
                    
                    # Αφαίρεση του πεδίου odds
                    if "odds" in outcome:
                        del outcome["odds"]
    
    # Αντιστοίχιση παικτών με placeholders
    players = {}
    player_counter = 1
    for player in sorted(all_players):
        players[player] = f"PLAYER_{player_counter}"
        player_counter += 1
    
    # Αντικατάσταση ονομάτων παικτών
    for match in data:
        for market in match["markets"]:
            # Αντικατάσταση στο όνομα της αγοράς
            for player_name, placeholder in players.items():
                if player_name in market["market_name"]:
                    market["market_name"] = market["market_name"].replace(player_name, placeholder)
            
            # Αντικατάσταση στα outcomes
            for group in market["groups"]:
                for outcome in group["outcomes"]:
                    if "outcome" in outcome:
                        # Πρώτα αφαιρούμε τις ομάδες από τα ονόματα παικτών
                        player_name = strip_team_info(outcome["outcome"])
                        
                        # Μετά κάνουμε την αντικατάσταση με τα placeholders
                        if player_name in players:
                            outcome["outcome"] = players[player_name]
    
    # Αποθήκευση τροποποιημένων δεδομένων
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)
    
    print(f"Το ανωνυμοποιημένο JSON αποθηκεύτηκε στο {output_file}")
    print(f"Αντικαταστάθηκαν {len(teams)} ομάδες και {len(players)} παίκτες")
    
    # Επιστροφή των αντιστοιχίσεων για αναφορά
    return {"teams": teams, "players": players}

if __name__ == "__main__":
    input_file = r"odds\stoiximan\UEL_odds_stoiximan.json"
    output_file = r"odds\stoiximan\UEL_odds_stoiximan_anonymized.json"
    
    mappings = anonymize_json(input_file, output_file)
    
    # Εκτύπωση των αντιστοιχίσεων
    print("\nΑντιστοιχίσεις Ομάδων:")
    for original, placeholder in mappings["teams"].items():
        print(f"{original} -> {placeholder}")
    
    print("\nΑντιστοιχίσεις Παικτών:")
    for original, placeholder in mappings["players"].items():
        print(f"{original} -> {placeholder}")
