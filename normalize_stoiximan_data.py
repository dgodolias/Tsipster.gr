import json
import re
import subprocess
import sys
import os # Add os import

# Definitions copied from stoiximan_entity_extraction.py for self-containment
player_outcome_markets = [
    "Να σκοράρει",
    "Πρώτος σκόρερ",
    "Τελευταίος σκόρερ",
    "Να σκοράρει 2+ γκολ",
    "Να σκοράρει 3+ γκολ",
    "Να δεχτεί κάρτα",
    "Να σκοράρει με προσπάθεια εκτός περιοχής",
    "Να σκοράρει - 1ο Ημίχρονο",
    "Να δεχτεί κόκκινη κάρτα", # Added this as it also contains player names
    "Παίκτης που θα σκοράρει και στα δύο ημίχρονα", # Added based on user feedback
    "Να σκοράρει και να κερδίσει η ομάδα", # Added based on user feedback
    "Να σκοράρει με κεφαλιά" # Added based on user feedback
]

player_suffixes = [
    " Σουτ στην εστία",
    " Να σκοράρει",
    " Να δεχτεί κάρτα",
    " Να σκοράρει 2+ γκολ",
    " Να σκοράρει 3+ γκολ",
    " Προσπάθειες για γκολ" # Common suffix for player stats
]

team_pattern = re.compile(r'(.*) \((.*)\)$')

def strip_team_info(player_name):
    match = team_pattern.match(player_name)
    if match:
        return match.group(1).strip()
    return player_name.strip()

def get_entity_mapping():
    """
    Executes stoiximan_entity_extraction.py and returns its output as a dictionary.
    """
    try:
        script_path = sys.executable 
        extraction_script = "c:/Users/Demos/Desktop/Tsipster.gr/stoiximan_entity_extraction.py"
        
        # Set PYTHONIOENCODING for the subprocess environment
        env = os.environ.copy()
        env["PYTHONIOENCODING"] = "utf-8"
        
        process = subprocess.run(
            [script_path, extraction_script],
            capture_output=True,
            text=True,        # Decodes output using 'encoding'
            check=True,       # Raises CalledProcessError for non-zero exit codes
            encoding="utf-8", # Specify encoding for text mode decoding
            env=env           # Pass the modified environment
        )
        
        if process.stdout is None:
            # This should ideally be caught by check=True or other specific errors,
            # but added as a safeguard.
            print(f"Error: Subprocess stdout is None. stderr: {process.stderr}", file=sys.stderr)
            sys.exit(1)
            
        return json.loads(process.stdout)
    except subprocess.CalledProcessError as e:
        print(f"Error executing stoiximan_entity_extraction.py (CalledProcessError): {e}", file=sys.stderr)
        print(f"Exit Code: {e.returncode}", file=sys.stderr)
        print(f"Stdout: {e.stdout}", file=sys.stderr)
        print(f"Stderr: {e.stderr}", file=sys.stderr)
        sys.exit(1)
    except UnicodeDecodeError as e:
        print(f"Error decoding output from stoiximan_entity_extraction.py (UnicodeDecodeError): {e}", file=sys.stderr)
        if hasattr(e, 'object') and isinstance(e.object, bytes):
            problematic_bytes = e.object[e.start:e.end]
            print(f"Problematic bytes: {problematic_bytes}", file=sys.stderr)
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"Error decoding JSON from stoiximan_entity_extraction.py (JSONDecodeError): {e}", file=sys.stderr)
        # process.stdout should be available here if JSON decoding failed on a string
        # that was successfully decoded from bytes.
        if process and hasattr(process, 'stdout'):
             print(f"Received output that failed JSON parsing: {process.stdout}", file=sys.stderr)
        sys.exit(1)

def normalize_data(original_data, placeholder_to_entity_map):
    """
    Normalizes the JSON data by replacing names with placeholders and removing odds.
    """
    entity_to_placeholder_map = {v: k for k, v in placeholder_to_entity_map.items()}
    
    # Deep copy to avoid modifying the original data if it's passed around
    data = json.loads(json.dumps(original_data))

    if not data or not isinstance(data, list) or len(data) == 0:
        return data
        
    game_data = data[0]

    # Replace team names
    if "home_team" in game_data and game_data["home_team"] in entity_to_placeholder_map:
        game_data["home_team"] = entity_to_placeholder_map[game_data["home_team"]]
    if "away_team" in game_data and game_data["away_team"] in entity_to_placeholder_map:
        game_data["away_team"] = entity_to_placeholder_map[game_data["away_team"]]

    if "markets" in game_data:
        for market in game_data["markets"]:
            market_name_original = market["market_name"]
            
            # Process outcomes first to remove odds and replace player names if applicable
            if "groups" in market:
                for group in market["groups"]:
                    if "outcomes" in group:
                        new_outcomes = []
                        for outcome in group["outcomes"]:
                            # Always remove odds
                            if "odds" in outcome:
                                del outcome["odds"]
                            
                            # If market is player-specific outcome market, replace player name
                            if market_name_original in player_outcome_markets:
                                player_full = outcome.get("outcome", "").strip()
                                if player_full: # Ensure outcome field exists and is not empty
                                    player_name_stripped = strip_team_info(player_full)
                                    if player_name_stripped in entity_to_placeholder_map:
                                        outcome["outcome"] = entity_to_placeholder_map[player_name_stripped]
                            new_outcomes.append(outcome)
                        group["outcomes"] = new_outcomes
            
            # Process market name if it contains a player name
            # This check should be independent of player_outcome_markets, as some markets might have player in name
            # but outcomes are not player names (e.g. "Player X Shots on Target")
            
            # Check if market name itself contains a player name based on suffixes
            # This needs to be done carefully to match how stoiximan_entity_extraction.py finds players in market names
            found_player_in_market_name = False
            for suffix in player_suffixes:
                if market_name_original.endswith(suffix):
                    player_name_part = market_name_original[:-len(suffix)].strip()
                    # The player_name_part should be a stripped name as per extraction logic
                    if player_name_part in entity_to_placeholder_map:
                        market["market_name"] = entity_to_placeholder_map[player_name_part] + suffix
                        found_player_in_market_name = True
                        break
            
            # If not found by suffix, it might be a market like "Να σκοράρει" where outcomes are players
            # but the market name itself doesn't change beyond its generic form.
            # The example output implies "Να δεχτεί κάρτα" remains as is, and outcomes are PLAYER_X.
            # This is handled by the outcome processing loop above.

    return data

if __name__ == "__main__":
    # 1. Get the entity mapping
    placeholder_to_entity_map = get_entity_mapping()

    # 2. Load the original JSON data
    json_file_path = r"odds\stoiximan\UEL_odds_stoiximan.json"
    try:
        with open(json_file_path, "r", encoding="utf-8") as f:
            original_json_data = json.load(f)
    except FileNotFoundError:
        print(f"Error: Original JSON file not found at {json_file_path}", file=sys.stderr)
        sys.exit(1)
    except json.JSONDecodeError:
        print(f"Error: Could not decode JSON from {json_file_path}", file=sys.stderr)
        sys.exit(1)

    # 3. Normalize the data
    normalized_data = normalize_data(original_json_data, placeholder_to_entity_map)

    # 4. save the normalized data to a new JSON file
    normalized_json_file_path = r"odds\stoiximan\UEL_odds_stoiximan_normalized.json"
    try:
        with open(normalized_json_file_path, "w", encoding="utf-8") as f:
            json.dump(normalized_data, f, ensure_ascii=False, indent=4)
    except IOError as e:
        print(f"Error writing normalized JSON file: {e}", file=sys.stderr)
        sys.exit(1)



