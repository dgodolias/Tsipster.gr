import re

# ------------------------
# Basic terms evaluation
def evaluate_basic_terms(score, basic_terms):
    try:
        home_goals, away_goals = map(int, score.split('-'))
        if not (0 <= home_goals <= 10 and 0 <= away_goals <= 10):
            raise ValueError("Score out of range (0-10)")
    except ValueError:
        raise ValueError("Invalid score format. Use e.g., '1-1'.")
    
    context = {}
    for term, condition in basic_terms.items():
        eval_condition = condition.replace('home_goals', str(home_goals)).replace('away_goals', str(away_goals))
        eval_condition = eval_condition.replace('AND', 'and').replace('OR', 'or')
        context[term] = eval(eval_condition)
    return context

# ------------------------
# Parse KB file into basic terms and betting function definitions
def parse_kb(file_path):
    basic_terms = {}
    betting_functions = {}
    
    with open(file_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            if '<==' not in line:
                continue
            key, condition = line.split('<==', 1)
            key = key.strip()
            condition = condition.strip()
            
            # If the key has a parameter (e.g., DOUBLE_CHANCE[X]) then store as betting function
            if '[' in key and ']' in key:
                func_name = key.split('[')[0]
                betting_functions[func_name] = condition
            else:
                # Otherwise, it's a basic term
                basic_terms[key] = condition
    return basic_terms, betting_functions

# ------------------------
# Load pairing names mapping
def load_options_pairing_names(file_path):
    mapping = {}
    with open(file_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#') or ':' not in line:
                continue
            internal, aliases = line.split(':', 1)
            internal = internal.strip()
            aliases_list = [alias.strip() for alias in aliases.split(',')]
            # Map each alias to the internal standardized type.
            for alias in aliases_list:
                mapping[alias] = internal
            # Also add a mapping for the internal name
            mapping[internal] = internal
    return mapping

# ------------------------
# Evaluate a betting function definition
def evaluate_betting_function(func_def, user_option):
    # Expected format:
    # if X = "1X" then (expression1) else if X = "X2" then (expression2) else (expression3)
    pattern = r'if\s+X\s*=\s*"([^"]+)"\s*then\s*\((.*?)\)'
    conditions = re.findall(pattern, func_def)
    
    for opt, expr in conditions:
        if user_option == opt:
            return expr
    # Look for final else clause:
    else_pattern = r'else\s*\((.*?)\)\s*$'
    m = re.search(else_pattern, func_def)
    if m:
        return m.group(1)
    else:
        raise ValueError("No matching condition found in function definition.")

# ------------------------
# Main function
def main():
    # Load KB
    kb_file = 'pairing/KB.txt'
    try:
        basic_terms, betting_functions = parse_kb(kb_file)
        print("\nDEBUG - Available betting functions:")
        for func, definition in betting_functions.items():
            print(f"  {func}")
        print()  # empty line for readability
    except FileNotFoundError:
        print("Error: 'KB.txt' file not found.")
        return
    except Exception as e:
        print(f"Error parsing KB file: {e}")
        return

    # Load options pairing names mapping
    mapping_file = 'pairing/options_pairing_names.txt'
    try:
        pairing_mapping = load_options_pairing_names(mapping_file)
    except Exception as e:
        print(f"Error loading options pairing names: {e}")
        return

    # Get user input
    team_home = input("Enter home team (e.g., Μπόντο Γκλιμτ): ").strip()
    team_away = input("Enter away team (e.g., Λάτσιο): ").strip()
    print("Available betting types:", ', '.join(betting_functions.keys()))
    user_bet_type_input = input("Enter betting type (e.g., Διπλη ευκαιρια / Double chance): ").strip()
    # Translate user input to standardized betting type
    if user_bet_type_input in pairing_mapping:
        std_bet_type = pairing_mapping[user_bet_type_input]
    else:
        std_bet_type = user_bet_type_input

    if std_bet_type not in betting_functions:
        print(f"Error: Betting type '{user_bet_type_input}' not found in knowledge base.")
        return

    user_option = input("Enter your betting option (e.g., '1X'): ").strip()
    score = input("Enter the match score (e.g., '1-1'): ").strip()

    # Retrieve the betting function definition and pick the expression based on option.
    try:
        expression = evaluate_betting_function(betting_functions[std_bet_type], user_option)
    except ValueError as e:
        print(f"Error: {e}")
        return

    # Evaluate basic terms based on the score
    try:
        context = evaluate_basic_terms(score, basic_terms)
    except ValueError as e:
        print(f"Error: {e}")
        return

    # Specialize the expression with team names
    expression = expression.replace('team_home', f'"{team_home}"').replace('team_away', f'"{team_away}"')
    eval_expr = expression.replace('OR', 'or').replace('AND', 'and')

    # Replace basic term tokens in the expression with their boolean values.
    for key, value in context.items():
        key_replaced = key.replace('team_home', f'"{team_home}"').replace('team_away', f'"{team_away}"')
        eval_expr = eval_expr.replace(key_replaced, str(value))

    # Evaluate the final condition.
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