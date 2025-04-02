import re
import argparse
import unicodedata

class BettingEquivalenceChecker:
    def __init__(self, alias_path='pairing/options_pairing_names.txt'):
        """
        Initialize the checker with path to alias file.
        
        Args:
            alias_path: Path to the betting option aliases file
        """
        self.alias_path = alias_path
        self.option_aliases = {}
        self.outcome_aliases = {}
        
        # Load aliases
        self._load_aliases()
    
    def _load_aliases(self):
        """Load and parse the aliases file into separate option and outcome dictionaries."""
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
    
    def remove_accents(self, input_str):
        """
        Remove diacritics from a string for robust text normalization.
        """
        nfkd_form = unicodedata.normalize('NFKD', str(input_str))
        return "".join([c for c in nfkd_form if not unicodedata.combining(c)])
    
    def normalize_bet_name(self, bet_name):
        """
        Normalize a betting type name using option aliases.
        
        Args:
            bet_name: The betting type name to normalize
        
        Returns:
            The standardized betting type name.
        """
        if not bet_name:
            return ""
            
        # Remove accents and lowercase for comparison
        bet_name_norm = self.remove_accents(bet_name).lower()
        
        # Exact match check
        for standard_name, alias_list in self.option_aliases.items():
            for alias in alias_list:
                alias_norm = self.remove_accents(alias).lower()
                if bet_name_norm == alias_norm:
                    return standard_name
                    
        # Partial match check
        for standard_name, alias_list in self.option_aliases.items():
            for alias in alias_list:
                alias_norm = self.remove_accents(alias).lower()
                if bet_name_norm in alias_norm or alias_norm in bet_name_norm:
                    return standard_name
                    
        return bet_name
    
    def normalize_outcome(self, text):
        """
        Normalize the provided text using the outcome aliases.
        
        Returns the standardized outcome key if found, else returns the original text.
        """
        if not text:
            return ""
            
        # Remove accents and lowercase for comparison
        text_norm = self.remove_accents(text).lower()
        
        # Exact match check
        for std_out, alias_list in self.outcome_aliases.items():
            for alias in alias_list:
                alias_norm = self.remove_accents(alias).lower()
                if text_norm == alias_norm:
                    return std_out
                    
        # Partial match check
        for std_out, alias_list in self.outcome_aliases.items():
            for alias in alias_list:
                alias_norm = self.remove_accents(alias).lower()
                if text_norm in alias_norm or alias_norm in text_norm:
                    return std_out
                    
        return text
    
    def _normalize_parameters(self, parameters, home_team, away_team):
        """
        Normalize betting option parameters with team name handling.
        
        Args:
            parameters: Raw parameter string
            home_team: Home team name
            away_team: Away team name
            
        Returns:
            Normalized parameter string
        """
        if not parameters:
            return ""
            
        param = parameters
        
        # Replace team names with placeholders
        if home_team:
            param = re.sub(re.escape(home_team), "TEAM_HOME", param, flags=re.IGNORECASE)
        if away_team:
            param = re.sub(re.escape(away_team), "TEAM_AWAY", param, flags=re.IGNORECASE)
        
        # First try to match the entire pattern after team substitution
        for key, alias_list in self.outcome_aliases.items():
            for alias in alias_list:
                alias_norm = self.remove_accents(alias).lower()
                param_norm = self.remove_accents(param).lower()
                if param_norm == alias_norm:
                    return key
        
        # Handle composite parameters (with '/')
        tokens = [token.strip() for token in param.split("/")]
        if len(tokens) > 1:
            # Check if the entire parameter with slashes matches any outcome directly
            joined_tokens = "/".join(tokens)
            for key, alias_list in self.outcome_aliases.items():
                for alias in alias_list:
                    alias_norm = self.remove_accents(alias).lower()
                    param_norm = self.remove_accents(joined_tokens).lower()
                    if param_norm == alias_norm:
                        return key
            
            # If not a direct match, normalize each token separately
            normalized_tokens = [self.normalize_outcome(token) for token in tokens if token]
            normalized_param = "/".join(normalized_tokens)
            
            # Check again if the now-normalized form matches any outcome alias
            for key, alias_list in self.outcome_aliases.items():
                for alias in alias_list:
                    alias_norm = self.remove_accents(alias).lower()
                    param_norm = self.remove_accents(normalized_param).lower()
                    if param_norm == alias_norm:
                        return key
            
            return normalized_param
        
        # If no match found, return the parameter as is
        return param
    
    def standardize_betting_option(self, option, home_team, away_team):
        """
        Convert a betting option string to a standardized form.
        
        Args:
            option: Original betting option string
            home_team: Home team name
            away_team: Away team name
            
        Returns:
            A standardized string in the form "BET_TYPE [OUTCOME]"
        """
        # Split using common delimiters
        delimiters = ['-', '–', '|']
        split_pattern = '|'.join(map(re.escape, delimiters))
        parts = re.split(split_pattern, option, maxsplit=1)
        
        if len(parts) == 2:
            option_part = parts[0].strip()
            outcome_part = parts[1].strip()
        else:
            # If no explicit delimiter, try to split intelligently
            tokens = option.strip().split()
            option_part = option.strip()
            outcome_part = ""
            
            # Try to find a logical split point by checking for known betting types
            normalized_option = self.normalize_bet_name(option_part)
            if normalized_option != option_part:
                # Found a match for the entire string as a betting type
                # Now try to extract outcome from the end
                if len(tokens) > 1:
                    candidate = tokens[-1]
                    normalized = self.normalize_outcome(candidate)
                    if normalized != candidate:
                        outcome_part = candidate
                        option_part = " ".join(tokens[:-1])
        
        # Normalize the betting type
        bet_type = self.normalize_bet_name(option_part)
        
        # Normalize the outcome
        outcome = self._normalize_parameters(outcome_part, home_team, away_team) if outcome_part else ""
        
        # Combine standardized parts
        standardized = bet_type
        if outcome:
            standardized += " " + outcome
            
        return standardized.strip()
    
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
        # Standard comparison using normalization
        std_option1 = self.standardize_betting_option(option1, home_team, away_team)
        std_option2 = self.standardize_betting_option(option2, home_team, away_team)
        
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