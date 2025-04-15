import json

def extract_betting_data(bookmaker, json_file, output_file):
    with open(json_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    with open(output_file, 'w', encoding='utf-8') as out:
        for match in data:
            home_team = match['home_team']
            away_team = match['away_team']
            
            for market in match['markets']:
                market_name = market['market_name']
                
                for group in market['groups']:
                    group_title = group['group_title']
                    for outcome in group['outcomes']:
                        outcome_name = outcome['outcome']
                        odds = outcome['odds']
                        
                        # Format the output
                        if group_title:
                            out.write(f"{market_name} {group_title} {outcome_name} {odds}\n")
                        else:
                            out.write(f"{market_name} {outcome_name} {odds}\n")

if __name__ == "__main__":
    # Replace with the name of the bookmaker and paths to your JSON and output files
    bookmaker = 'stoiximan'
    json_file = f'c:\\Users\\USER\\Desktop\\PROJECTS\\Tsipster.gr\\odds\\{bookmaker.lower()}\\UEL_odds_{bookmaker.lower()}.json'
    output_file = f'c:\\Users\\USER\\Desktop\\PROJECTS\\Tsipster.gr\\bet_names_{bookmaker.lower()}.txt'
    extract_betting_data(bookmaker, json_file, output_file)