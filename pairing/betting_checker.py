import re

# Function to evaluate basic terms based on the score and KB definitions
def evaluate_basic_terms(score, basic_terms):
    try:
        home_goals, away_goals = map(int, score.split('-'))
        if not (0 <= home_goals <= 10 and 0 <= away_goals <= 10):
            raise ValueError("Score out of range (0-10)")
    except ValueError:
        raise ValueError("Invalid score format. Use e.g., '1-1'.")
    
    # Context dictionary to hold evaluated basic terms
    context = {}
    for term, condition in basic_terms.items():
        # Replace placeholders with actual values
        eval_condition = condition.replace('home_goals', str(home_goals)).replace('away_goals', str(away_goals))
        # Convert logical operators to Python syntax
        eval_condition = eval_condition.replace('AND', 'and').replace('OR', 'or')
        # Evaluate the condition
        context[term] = eval(eval_condition)
    return context

def parse_kb(file_path):
    basic_terms = {}
    betting_rules = {}

    with open(file_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            parts = line.split('<==')
            if len(parts) != 2:
                continue
            key = parts[0].strip()
            condition = parts[1].strip()

            # Check if it's a basic term or betting type
            if key.startswith('"') and key.endswith('"'):
                # Betting type (e.g., "Διπλή ευκαιρία")
                bet_type = key.strip('"')
                betting_rules[bet_type] = {}
                
                # Split by OR to process each option separately
                option_conditions = re.split(r'\s+OR\s+', condition)
                for opt_cond in option_conditions:
                    # Updated regex: using non-greedy matching to correctly capture the full condition
                    match = re.search(r'\((.*?)\)-\{\s*"([^"]+)"\s*\}', opt_cond.strip())
                    if match:
                        cond, opt = match.groups()
                        betting_rules[bet_type][opt] = cond
            else:
                # Basic term (e.g., WINS(team_home))
                basic_terms[key] = condition

    return basic_terms, betting_rules

# Main function
def main():
    # Load the knowledge base
    kb_file = 'pairing/KB.txt'
    try:
        basic_terms, betting_rules = parse_kb(kb_file)
        # Debug information
        print("\nDEBUG - Available betting rules:")
        for bet_type, options in betting_rules.items():
            print(f"  {bet_type}: {list(options.keys())}")
        print()  # Add an empty line for readability
    except FileNotFoundError:
        print("Error: 'KB.txt' file not found.")
        return
    except Exception as e:
        print(f"Error parsing KB file: {e}")
        return
    
    # Get user input
    team_home = input("Enter home team (e.g., Μπόντο Γκλιμτ): ").strip()
    team_away = input("Enter away team (e.g., Λάτσιο): ").strip()
    print("Available betting types:", ', '.join(betting_rules.keys()))
    bet_type = input("Enter betting type (e.g., 'Διπλή ευκαιρία'): ").strip()
    user_option = input("Enter your betting option (e.g., '1X'): ").strip()
    score = input("Enter the match score (e.g., '1-1'): ").strip()
    
    # Validate betting type
    if bet_type not in betting_rules:
        print(f"Error: Betting type '{bet_type}' not found in knowledge base.")
        return
    
    conditions = betting_rules[bet_type]
    
    # Validate betting option
    if user_option not in conditions:
        print(f"Error: Option '{user_option}' not found for betting type '{bet_type}'. Available options: {', '.join(conditions.keys())}")
        return
    
    # Get the logical condition for the selected option
    expression = conditions[user_option]
    
    # Evaluate basic terms based on the score
    try:
        context = evaluate_basic_terms(score, basic_terms)
    except ValueError as e:
        print(f"Error: {e}")
        return
    
    # Specialize the expression with team names (replace placeholders)
    expression = expression.replace('team_home', f'"{team_home}"').replace('team_away', f'"{team_away}"')
    eval_expr = expression.replace('OR', 'or').replace('AND', 'and')
    
    # Replace basic term placeholders in the expression with their boolean values
    for key, value in context.items():
        # Replace team placeholders in the key to match the specialized expression
        key_replaced = key.replace('team_home', f'"{team_home}"').replace('team_away', f'"{team_away}"')
        # Use simple string replacement to substitute the boolean value
        eval_expr = eval_expr.replace(key_replaced, str(value))
    
    # Evaluate the condition
    try:
        result = eval(eval_expr)
        if result:
            print(f"The betting option '{user_option}' for {team_home} vs {team_away} is **met** for the score {score}.")
        else:
            print(f"The betting option '{user_option}' for {team_home} vs {team_away} is **not met** for the score {score}.")
    except Exception as e:
        print(f"Error evaluating condition: {e}")

if __name__ == "__main__":
    main()