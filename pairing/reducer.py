import re

class BettingReducer:
    def __init__(self, kb_content):
        """
        Initialize the reducer with the KB content.
        
        Args:
            kb_content (str): The raw text of the knowledge base.
        """
        self.basic_terms = {}
        self.betting_types = {}
        self._parse_kb(kb_content)

    def _parse_kb(self, kb_content):
        """Parse the KB to extract basic terms and betting types."""
        lines = kb_content.split('\n')
        current_section = None
        current_betting_type = None
        current_conditions = []
    
        for line in lines:
            line = line.strip()
            if not line or line.startswith('#'):
                if 'Ορισμοί βασικών όρων' in line:
                    current_section = 'basic'
                elif 'Ορισμοί στοιχηματικών τύπων' in line:
                    current_section = 'betting'
                continue
    
            if current_section == 'basic' and '<--' in line:
                # Parse basic terms, e.g., "WINS<x,y> <-- ((GOALS<x>) > (GOALS<y>))"
                term, definition = line.split('<--', 1)
                term_name = term.split('<')[0].strip()
                params = re.search(r'<([^>]+)>', term).group(1).split(',')
                definition = definition.strip()
                self.basic_terms[term_name] = {'params': params, 'definition': definition}
    
            elif current_section == 'betting' and '<--' in line:
                # Start of a new betting type definition
                if current_betting_type and current_conditions:
                    self._process_conditions(current_betting_type, current_conditions)
                current_conditions = []
                type_part, conditions = line.split('<--', 1)
                betting_type = type_part.split('[')[0].strip()
    
                # Ensure square brackets exist before extracting the parameter variable
                if '[' in type_part and ']' in type_part:
                    param_var = type_part[type_part.index('[')+1:type_part.index(']')].strip()
                else:
                    print(f"Warning: Skipping invalid betting type definition: {line}")
                    continue
    
                current_betting_type = (betting_type, param_var)
                current_conditions.append(conditions.strip())
            elif line and current_betting_type:
                # Continuation of multi-line conditions
                current_conditions.append(line.strip())
    
        # Process the last betting type definition
        if current_betting_type and current_conditions:
            self._process_conditions(current_betting_type, current_conditions)

    def _process_conditions(self, betting_type_info, conditions):
        """Process conditional definitions for a betting type."""
        betting_type, param_var = betting_type_info
        self.betting_types[betting_type] = {}
        full_conditions = " ".join(conditions).strip()

        # Split into individual conditions, preserving 'if' and 'else if' parts
        condition_parts = re.split(r'\s*else\s+if\s*', full_conditions)
        for i, part in enumerate(condition_parts):
            part = part.strip()
            # For parts after the first, prepend 'if' if it was split from 'else if'
            if i > 0:
                part = f"if {part}"
            
            # Match the 'if (var = "value") then (expression)' pattern
            match = re.match(r'if\s*\(\s*([^=]+)\s*=\s*"([^"]+)"\s*\)\s*then\s*(.+)', part)
            if match:
                var, value, expr = match.groups()
                if var.strip() == param_var:
                    # Clean the expression by removing any trailing 'else' or extra text
                    expr = expr.strip()
                    if 'else' in expr.lower():
                        expr = expr[:expr.lower().index('else')].strip()
                    self.betting_types[betting_type][value] = expr
            elif 'else' in part.lower() and 'if' not in part[part.lower().index('else'):]:
                # Handle a standalone 'else' case
                else_expr = part.split('else')[-1].strip()
                self.betting_types[betting_type]['default'] = else_expr
            elif i == 0 and 'if' not in part:
                # Default case without 'if'
                self.betting_types[betting_type]['default'] = part

    def reduce_expression(self, expr):
        """
        Recursively reduce an expression by replacing basic terms with their definitions.
        
        Args:
            expr (str): The expression to reduce.
        
        Returns:
            str: The fully reduced expression.
        """
        pattern = r"(\w+)<([^>]+)>"
        while True:
            def replacer(match):
                term = match.group(1)
                params_str = match.group(2)
                params = [p.strip() for p in params_str.split(',')]

                if term in self.basic_terms:
                    term_info = self.basic_terms[term]
                    if len(params) == len(term_info['params']):
                        definition = term_info['definition']
                        for i, param in enumerate(params):
                            placeholder = f"<{term_info['params'][i]}>"
                            definition = definition.replace(placeholder, f"<{param}>")
                        return definition
                return match.group(0)  # No replacement if term not found or params mismatch

            new_expr = re.sub(pattern, replacer, expr)
            if new_expr == expr:
                break
            expr = new_expr
        return expr

    def reduce_option(self, option):
        """
        Reduce a betting option to its final form.
        
        Args:
            option (str): The betting option, e.g., "DOUBLE_CHANCE 1X".
        
        Returns:
            str: The reduced form.
        """
        parts = option.split(" ", 1)
        if len(parts) != 2:
            return "Invalid option format"
        
        betting_type, param = parts[0], parts[1]
        if betting_type not in self.betting_types:
            return f"Unknown betting type: {betting_type}"
        
        betting_rules = self.betting_types[betting_type]
        expr = betting_rules.get(param, betting_rules.get('default'))
        if not expr:
            return f"Unknown parameter '{param}' for {betting_type}"
        
        # Handle cases like ((GG)) or ((NG))
        expr = expr.strip('()')  # Remove outer parentheses from the KB definition
        if expr in self.basic_terms:
            expr = f"{expr}<TEAM_HOME,TEAM_AWAY>"

        return self.reduce_expression(expr)

def main():
    # Read the KB content from the file
    kb_file_path = "pairing/KB.txt"
    try:
        with open(kb_file_path, "r", encoding="utf-8") as kb_file:
            kb_content = kb_file.read()
    except FileNotFoundError:
        print(f"Error: Knowledge base file not found at {kb_file_path}")
        return
    except Exception as e:
        print(f"Error reading the knowledge base file: {e}")
        return

    # Initialize the BettingReducer with the KB content
    reducer = BettingReducer(kb_content)
    
    # Prompt the user for input
    option = input("Enter the betting option (e.g., DOUBLE_CHANCE 1X): ").strip()
    reduced_form = reducer.reduce_option(option)
    print("Reduced form:", reduced_form)

if __name__ == "__main__":
    main()