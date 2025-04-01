import re
import argparse
from pathlib import Path

class BettingEquivalenceChecker:
    def __init__(self, kb_path='pairing/KB.txt', alias_path='pairing/options_pairing_names.txt'):
        """
        Initialize the checker with paths to knowledge base and alias files.
        
        Args:
            kb_path: Path to the knowledge base file
            alias_path: Path to the betting option aliases file
        """
        self.kb_path = kb_path
        self.alias_path = alias_path
        self.basic_terms = {}
        self.betting_types = {}
        self.constants = {}
        self.functions = {}
        self.aliases = {}
        
        # Load knowledge base and aliases
        self._load_kb()
        self._load_aliases()
    
    def _load_kb(self):
        """Load and parse the knowledge base file."""
        try:
            with open(self.kb_path, 'r', encoding='utf-8') as f:
                current_section = None
                for line in f:
                    line = line.strip()
                    if not line or line.startswith('#'):
                        if line.startswith('#'):
                            current_section = line[1:].strip()
                        continue
                    
                    if '<--' not in line:
                        continue
                        
                    parts = line.split('<--')
                    if len(parts) != 2:
                        continue
                        
                    definition = parts[0].strip()
                    condition = parts[1].strip()
                    
                    if current_section == 'Ορισμοί βασικών όρων':
                        self.basic_terms[definition] = condition
                    elif current_section == 'Ορισμοί στοιχηματικών τύπων ως συναρτήσεις':
                        self.betting_types[definition] = condition
                    elif current_section == 'σταθερες':
                        self.constants[definition] = condition
                    elif current_section == 'συναρτησεις':
                        self.functions[definition] = condition
        except Exception as e:
            print(f"Error loading knowledge base: {e}")
    
    def _load_aliases(self):
        """Load and parse the aliases file into separate option and outcome dictionaries."""
        self.option_aliases = {}
        self.outcome_aliases = {}
        current_section = None
        try:
            with open(self.alias_path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    # Switch sections based on comment lines
                    if line.startswith("#"):
                        if "options" in line.lower():
                            current_section = "options"
                        elif "outcomes" in line.lower():
                            current_section = "outcomes"
                        else:
                            current_section = None
                        continue
                    if ':' not in line:
                        continue
                    key, values = line.split(':', 1)
                    aliases = [v.strip() for v in values.split(',')]
                    key = key.strip()
                    if current_section == "outcomes":
                        self.outcome_aliases[key] = aliases
                    else:
                        # Default to options if section is not outcomes
                        self.option_aliases[key] = aliases
        except Exception as e:
            print(f"Error loading aliases: {e}")
    
    def normalize_bet_name(self, bet_name):
        """
        Normalize a betting type name using option aliases.
        
        Args:
            bet_name: The betting type name to normalize
        
        Returns:
            The standardized betting type name.
        """
        # Exact match check (case insensitive)
        for standard_name, alias_list in self.option_aliases.items():
            if bet_name.lower() in [alias.lower() for alias in alias_list]:
                return standard_name
        # Then check for partial matches
        for standard_name, alias_list in self.option_aliases.items():
            for alias in alias_list:
                if alias.lower() in bet_name.lower() or bet_name.lower() in alias.lower():
                    return standard_name
        return bet_name
    
    def _parse_complex_bet(self, bet_string):
        """
        Parse a complex betting option into individual components.
        
        Args:
            bet_string: Complex betting string like "Double chance 1X & Goal/No Goal GG"
        
        Returns:
            List of individual betting components
        """
        # Special case for 'GG/NG' which should be treated as a single entity
        if 'GG/NG' in bet_string or 'gg/ng' in bet_string.lower():
            # Check if this is the only component or part of a complex bet
            if '&' not in bet_string and 'και' not in bet_string.lower() and 'and' not in bet_string.lower() and 'with' not in bet_string.lower() and 'με' not in bet_string.lower():
                return [bet_string.strip()]
        
        # Split by common separators for combined bets
        components = re.split(r'\s+(?:&|και|and|with|με)\s+', bet_string)
        return [comp.strip() for comp in components if comp.strip()]
    
    def _extract_team_references(self, bet_string, teams):
        """
        Extract team references from a betting option.
        
        Args:
            bet_string: Betting option string
            teams: List of team names to look for
        
        Returns:
            Tuple of (modified bet string, referenced team)
        """
        referenced_team = None
        for team in teams:
            if team.lower() in bet_string.lower():
                referenced_team = team
                # Remove the team name but preserve the betting type
                bet_string = bet_string.replace(team, '').strip()
                break
        
        return bet_string, referenced_team
    
    def _normalize_option_parameters(self, bet_type, parameters):
        """
        Normalize betting option parameters like 1X, X2, etc.
        
        Args:
            bet_type: The normalized betting type
            parameters: Option parameters as string
        
        Returns:
            Normalized parameters
        """
        # Clean parameters
        params = parameters.strip()
        
        # Double chance normalizations
        if bet_type == "DOUBLE_CHANCE":
            if "1" in params and "X" in params:
                return "1X"
            if "X" in params and "2" in params:
                return "X2"
            if "1" in params and "2" in params:
                return "12"
        
        # Goal/No Goal normalizations
        if bet_type == "GOAL_NO_GOAL":
            if any(term in params.lower() for term in ["gg", "yes", "ναι", "goal"]):
                return "GG"
            if any(term in params.lower() for term in ["ng", "no", "οχι", "όχι"]):
                return "NG"
        
        return params
    
    def standardize_betting_option(self, option, home_team, away_team):
        """
        Convert a betting option string to a standardized form.

        The method first attempts to split the input using a set of common delimiters.
        If no delimiter is present, it tokenizes the input and checks whether the last
        token matches an outcome alias. Then it normalizes both the betting type and outcome.

        Args:
            option: Original betting option string.
            home_team: Home team name (for future extension, if needed).
            away_team: Away team name.

        Returns:
            A standardized string in the form "BET_TYPE [OUTCOME]".
        """
        # Try splitting by common delimiters.
        delimiters = ['-', '–', '|']
        split_pattern = '|'.join(map(re.escape, delimiters))
        parts = re.split(split_pattern, option, maxsplit=1)
        
        if len(parts) == 2:
            option_part = parts[0].strip()
            outcome_part = parts[1].strip()
        else:
            # No explicit delimiter; try to detect an outcome from the last token.
            tokens = option.strip().split()
            outcome_part = ""
            option_part = option.strip()
            if len(tokens) > 1:
                # Use the last token as outcome if it normalizes to a known outcome.
                candidate = tokens[-1]
                normalized = self.normalize_outcome(candidate)
                if normalized:  # removed check for inequality
                    outcome_part = candidate
                    option_part = " ".join(tokens[:-1])
        
        # Normalize each part using alias lookups.
        bet_type = self.normalize_bet_name(option_part)
        outcome = self.normalize_outcome(outcome_part) if outcome_part else ""
        
        standardized = bet_type
        if outcome:
            standardized += " " + outcome
        return standardized.strip()
    
    def normalize_outcome(self, text):
        """
        Normalize the provided text using the outcome aliases.
    
        Returns the standardized outcome key if found, else returns the original text.
        """
        if not text:
            return ""
        # Exact match check (case insensitive)
        for std_out, alias_list in self.outcome_aliases.items():
            if text.lower() in [a.lower() for a in alias_list]:
                return std_out
        # Partial match check: if the text is contained in any alias.
        for std_out, alias_list in self.outcome_aliases.items():
            for alias in alias_list:
                if text.lower() in alias.lower() or alias.lower() in text.lower():
                    return std_out
        return text
    
    # A similar normalize_bet_name is assumed to exist that checks self.option_aliases.
    def are_equivalent(self, option1, option2, home_team, away_team):
        """
        Check if two betting options are equivalent.
        
        Args:
            option1: First betting option string
            option2: Second betting option string
            home_team: Home team name
            away_team: Away team name
        
        Returns:
            Boolean indicating if the options are equivalent
        """
        # Special case handling for common formats
        option1_lower = option1.lower().strip()
        option2_lower = option2.lower().strip()
        
        # Direct equivalence check for Goal/No Goal and GG/NG
        if any(s in option1_lower for s in ["goal/no goal", "gg/ng"]) and any(s in option2_lower for s in ["goal/no goal", "gg/ng"]):
            return True
        
        # Standard comparison using normalization
        std_option1 = self.standardize_betting_option(option1, home_team, away_team)
        std_option2 = self.standardize_betting_option(option2, home_team, away_team)
        
        # Debug output to help diagnose equivalence issues
        # print(f"DEBUG - Standardized option1: {std_option1}")
        # print(f"DEBUG - Standardized option2: {std_option2}")
        
        # Compare standardized options
        return std_option1 == std_option2

def main():
    parser = argparse.ArgumentParser(description='Check if two betting options are equivalent.')
    parser.add_argument('--option1', type=str, help='First betting option')
    parser.add_argument('--option2', type=str, help='Second betting option')
    parser.add_argument('--home', type=str, help='Home team name')
    parser.add_argument('--away', type=str, help='Away team name')
    
    # Parse command-line arguments or use interactive mode
    args = parser.parse_args()
    
    checker = BettingEquivalenceChecker()
    
    if args.option1 and args.option2 and args.home and args.away:
        # Command-line mode
        result = checker.are_equivalent(args.option1, args.option2, args.home, args.away)
        if result:
            print(f"The betting options are equivalent.")
        else:
            print(f"The betting options are NOT equivalent.")
    else:
        # Interactive mode
        print("Betting Equivalence Checker")
        print("==========================")
        home_team = input("Enter home team name: ").strip()
        away_team = input("Enter away team name: ").strip()
        option1 = input("Enter first betting option: ").strip()
        option2 = input("Enter second betting option: ").strip()
        
        try:
            result = checker.are_equivalent(option1, option2, home_team, away_team)
            print("\nStandardized options:")
            print("Option 1:", checker.standardize_betting_option(option1, home_team, away_team))
            print("Option 2:", checker.standardize_betting_option(option2, home_team, away_team))
            print("\nResult:", "EQUIVALENT" if result else "NOT EQUIVALENT")
        except Exception as e:
            print(f"Error comparing options: {e}")

if __name__ == "__main__":
    main()