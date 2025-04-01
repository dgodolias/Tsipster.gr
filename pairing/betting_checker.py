import re

# Function to parse the knowledge base (KB) file
def parse_kb(file_path):
    """
    Parse the KB file into dictionaries for basic terms, betting types, constants, and functions.
    """
    basic_terms = {}
    betting_types = {}
    constants = {}
    functions = {}
    
    with open(file_path, 'r', encoding='utf-8') as f:
        current_section = None
        for line in f:
            line = line.strip()
            if line.startswith('#'):
                current_section = line[1:].strip()
                continue
            if not line or '<--' not in line:
                continue
            parts = line.split('<--')
            definition = parts[0].strip()
            condition = parts[1].strip()
            
            if current_section == 'Ορισμοί βασικών όρων':
                basic_terms[definition] = condition
            elif current_section == 'Ορισμοί στοιχηματικών τύπων ως συναρτήσεις':
                betting_types[definition] = condition
            elif current_section == 'σταθερες':
                # Store as string instead of evaluating
                constants[definition] = condition
            elif current_section == 'συναρτησεις':
                # Store as string instead of evaluating
                functions[definition] = condition
    
    return basic_terms, betting_types, constants, functions

# Function to load aliases from the options_pairing_names.txt file
def load_aliases(file_path):
    """
    Load aliases from a file into a dictionary.
    """
    aliases = {}
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if ':' in line:
                    key, values = line.split(':', 1)
                    aliases[key.strip()] = [v.strip() for v in values.split(',')]
    except Exception as e:
        print(f"Error loading aliases: {e}")
    return aliases

# Function to normalize a betting option
def normalize_option(option, aliases, betting_types, basic_terms, team_home, team_away):
    """
    Convert a betting option into its standardized logical condition.
    """
    # Split the option into parts (e.g., "Double Chance 1X" -> ["Double Chance", "1X"])
    parts = option.strip().split()
    if len(parts) < 1:
        return option
    
    # Identify the betting type and parameter
    bet_type = parts[0]
    param = ' '.join(parts[1:]) if len(parts) > 1 else ''
    
    # Check aliases to standardize the betting type
    for std_name, alias_list in aliases.items():
        if bet_type in alias_list or option in alias_list:
            bet_type = std_name
            break
    
    # Construct the full betting type with parameter if applicable
    full_bet_type = f"{bet_type}[{param}]" if param else bet_type
    
    # Expand the betting type using its definition
    if full_bet_type in betting_types:
        condition = betting_types[full_bet_type]
    elif bet_type in betting_types:
        condition = betting_types[bet_type]
        if param:
            # Handle conditional logic (e.g., if X = "GG" then ...)
            condition = condition.replace('X', f'"{param}"')
            # Simple parsing of if-then-else for this example
            if 'if' in condition:
                clauses = re.split('if|then|else', condition)
                clauses = [c.strip(' ()') for c in clauses if c.strip()]
                for i, clause in enumerate(clauses):
                    if f'X = "{param}"' in clause and i + 1 < len(clauses):
                        condition = clauses[i + 1]
                        break
    else:
        return option  # Return as-is if not found
    
    # Substitute team names
    condition = condition.replace('TEAM_HOME', team_home).replace('TEAM_AWAY', team_away)
    
    # Expand basic terms
    for term, defn in basic_terms.items():
        # Handle parameterized terms like WINS<x,y>
        pattern = rf"{term}\<([^>]+)\>"
        matches = re.findall(pattern, condition)
        for match in matches:
            params = match.split(',')
            if len(params) == 2:
                expanded = defn.replace('x', params[0]).replace('y', params[1])
                condition = condition.replace(f"{term}<{match}>", f"({expanded})")
        # Replace non-parameterized terms
        if term in condition:
            condition = condition.replace(term, f"({defn})")
    
    return condition

# Function to check equivalence of two betting options
def are_equivalent(option1, option2, team_home, team_away, kb_file, alias_file):
    """
    Determine if two betting options are logically equivalent.
    """
    basic_terms, betting_types, _, _ = parse_kb(kb_file)
    aliases = load_aliases(alias_file)
    
    norm_opt1 = normalize_option(option1, aliases, betting_types, basic_terms, team_home, team_away)
    norm_opt2 = normalize_option(option2, aliases, betting_types, basic_terms, team_home, team_away)
    
    # For simplicity, compare normalized strings
    # A full logical equivalence checker would require a more complex parser
    return norm_opt1 == norm_opt2

# Main execution
def main():
    """
    Main function to interact with the user and check betting option equivalence.
    """
    kb_file = 'pairing/KB.txt'  # Path to your KB file
    alias_file = 'pairing/options_pairing_names.txt'  # Path to your aliases file
    
    # Get user inputs
    print("Enter the team names and betting options.")
    team_home = input("Home team: ").strip()
    team_away = input("Away team: ").strip()
    option1 = input("First betting option: ").strip()
    option2 = input("Second betting option: ").strip()
    
    # Check equivalence
    try:
        if are_equivalent(option1, option2, team_home, team_away, kb_file, alias_file):
            print(f"\nThe betting options '{option1}' and '{option2}' are equivalent.")
        else:
            print(f"\nThe betting options '{option1}' and '{option2}' are not equivalent.")
    except Exception as e:
        print(f"Error comparing options: {e}")

if __name__ == "__main__":
    main()