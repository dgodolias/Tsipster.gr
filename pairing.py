import json
from collections import defaultdict

# Standardize match titles for consistent grouping
def standardize_match_title(match_title):
    return match_title.replace('\n', ' vs ').strip()

# Extract home and away team names from the match title
def extract_teams(match_title):
    standardized_title = standardize_match_title(match_title)
    if ' vs ' in standardized_title:
        home, away = standardized_title.split(' vs ')
        return home.strip(), away.strip()
    else:
        return "Home", "Away"  # Fallback if format is unexpected

# Standardize outcome descriptions to a common format
def standardize_outcome(outcome, home_team, away_team):
    outcome_lower = outcome.lower()
    if outcome == "1":
        return "Home Win"
    elif outcome == "2":
        return "Away Win"
    elif outcome in ["X", "Ισοπαλία"]:
        return "Draw"
    elif home_team.lower() in outcome_lower or outcome_lower in home_team.lower():
        return "Home Win"
    elif away_team.lower() in outcome_lower or outcome_lower in away_team.lower():
        return "Away Win"
    elif "over" in outcome_lower or "under" in outcome_lower:
        return outcome  # Keep Over/Under outcomes as is
    elif outcome == "Ναι":
        return "Yes"  # Greek "Yes" for markets like Both Teams to Score
    elif outcome == "Όχι":
        return "No"   # Greek "No"
    else:
        return outcome  # Default to original if no rule applies

# Process a match to extract betting options
def process_match(match, bookmaker, home_team, away_team):
    betting_options = []
    for market in match['markets']:
        # Check if the market has subgroups (group_title is not null)
        if all(group['group_title'] is None for group in market['groups']):
            # Single-group market (e.g., Match Winner, Draw No Bet)
            outcomes = market['groups'][0]['outcomes']
            standardized_outcomes = [standardize_outcome(outcome['outcome'], home_team, away_team) 
                                   for outcome in outcomes]
            key = tuple(sorted(standardized_outcomes))  # Unique key for grouping
            odds_dict = {standardize_outcome(outcome['outcome'], home_team, away_team): outcome['odds'] 
                        for outcome in outcomes}
            betting_options.append({
                'key': key,
                'bookmaker': bookmaker,
                'market_name': market['market_name'],
                'odds': odds_dict
            })
        else:
            # Multi-group market (e.g., Over/Under with different lines)
            for group in market['groups']:
                outcomes = group['outcomes']
                standardized_outcomes = [standardize_outcome(outcome['outcome'], home_team, away_team) 
                                       for outcome in outcomes]
                key = tuple(sorted(standardized_outcomes))
                odds_dict = {standardize_outcome(outcome['outcome'], home_team, away_team): outcome['odds'] 
                            for outcome in outcomes}
                betting_options.append({
                    'key': key,
                    'bookmaker': bookmaker,
                    'market_name': market['market_name'],
                    'group_title': group['group_title'],
                    'odds': odds_dict
                })
    return betting_options

def main():
    # List of bookmakers to process
    bookmakers = ['Stoiximan', 'Winmasters']
    
    # Collect all matches, grouped by standardized title
    all_matches = defaultdict(list)
    for bookmaker in bookmakers:
        file_path = f'odds/{bookmaker.lower()}/UEL_odds_{bookmaker.lower()}'+'.json'
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                matches = json.load(f)
                for match in matches:
                    standardized_title = standardize_match_title(match['match_title'])
                    all_matches[standardized_title].append((bookmaker, match))
        except FileNotFoundError:
            print(f"Error: Could not find file {file_path}")
            continue
    
    # Process each match group and group betting options
    grouped_data = []
    for match_title, bookmaker_matches in all_matches.items():
        match_data = {
            'match_title': match_title,
            'betting_options': defaultdict(list)
        }
        for bookmaker, match in bookmaker_matches:
            home_team, away_team = extract_teams(match['match_title'])
            betting_options = process_match(match, bookmaker, home_team, away_team)
            for option in betting_options:
                key = option['key']
                match_data['betting_options'][key].append({
                    'bookmaker': option['bookmaker'],
                    'market_name': option['market_name'],
                    'group_title': option.get('group_title', None),
                    'odds': option['odds']
                })
        
        # Convert betting options to a list for JSON serialization
        match_data['betting_options'] = [
            {
                'key': list(key),  # Tuple to list for JSON compatibility
                'bookmakers': bookmakers_list
            }
            for key, bookmakers_list in match_data['betting_options'].items()
        ]
        grouped_data.append(match_data)
    
    # Save the grouped data to a JSON file
    output_file = 'grouped_odds.json'
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(grouped_data, f, ensure_ascii=False, indent=4)
    print(f"Grouped odds data saved to {output_file}")

if __name__ == "__main__":
    main()