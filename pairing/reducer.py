import re

class Reducer:
    def __init__(self, kb_path):
        self.rules = self._load_rules(kb_path)
        print("Loaded rules:")
        for pattern, replacement in self.rules:
            print(f"Pattern: {pattern}, Replacement: {replacement}")

    def _load_rules(self, kb_path):
        """Load reduction rules from KB.txt."""
        rules = []
        with open(kb_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                # Skip empty lines or comments
                if not line or line.startswith('#'):
                    continue
                if '<--' in line:
                    term, definition = line.split('<--', 1)
                    term = term.strip()
                    definition = definition.strip()

                    # Handle betting types with parameter X (e.g., DOUBLE_CHANCE[X])
                    if '[' in term:
                        match = re.match(r'(\w+)\[X\]', term)
                        if match:
                            term_name = match.group(1)
                            # Extract all if-then conditions - use a more robust pattern
                            # that captures the entire expression after "then"
                            if_matches = re.findall(r'if \(X = "(\w+)"\) then (.+?)(?=else if|$)', definition)
                            for value, expr in if_matches:
                                expr = expr.strip()  # Clean up any extra whitespace
                                pattern = r'\b' + re.escape(f"{term_name} {value}") + r'\b'
                                replacement = expr
                                rules.append((pattern, replacement))

                    # Handle basic terms with parameters <x,y> (e.g., WINS<x,y>)
                    elif '<' in term and '>' in term:
                        match = re.match(r'(\w+)<x,y>', term)
                        if match:
                            term_name = match.group(1)
                            pattern = rf'{re.escape(term_name)}<(\w+),(\w+)>'
                            # Replace <x> and <y> in definition with backreferences
                            replacement = definition.replace('<x>', '<\\1>').replace('<y>', '<\\2>')
                            rules.append((pattern, replacement))
        return rules

    def reduce_betting_option(self, standardized):
        expr = standardized
        iteration = 0
        while True:
            print(f"\nIteration {iteration}:")
            print(f"Starting expression: {expr}")
            new_expr = expr
            for pattern, replacement in self.rules:
                temp_expr = re.sub(pattern, replacement, new_expr)
                if temp_expr != new_expr:  # Only print if a substitution occurred
                    print(f"Applied rule: {pattern} -> {replacement}")
                    print(f"Result: {temp_expr}")
                    new_expr = temp_expr
            if new_expr == expr:  # No changes made in this iteration
                print("No more changes. Reduction complete.")
                break
            expr = new_expr
            iteration += 1
        print(f"\nFinal reduced form: {expr}")
        return expr

# Example usage
if __name__ == "__main__":
    reducer = Reducer(kb_path='pairing/KB.txt')  # Use relative path when running from pairing directory
    # Test with a betting option
    result = reducer.reduce_betting_option("DOUBLE_CHANCE 1X")
    print(result)