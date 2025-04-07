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
        self.operators = set()
        self._parse_kb(kb_content)

    def _parse_kb(self, kb_content):
        """Parse the KB to extract basic terms, betting types, and operators."""
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
                elif 'συνδεσμοι' in line:
                    current_section = 'operators'
                continue

            if current_section == 'basic' and '<--' in line:
                term, definition = line.split('<--', 1)
                term_name = term.split('<')[0].strip()
                params = re.search(r'<([^>]+)>', term).group(1).split(',')
                definition = definition.strip()
                self.basic_terms[term_name] = {'params': params, 'definition': definition}

            elif current_section == 'betting' and '<--' in line:
                if current_betting_type and current_conditions:
                    self._process_conditions(current_betting_type, current_conditions)
                current_conditions = []
                type_part, conditions = line.split('<--', 1)
                betting_type = type_part.split('[')[0].strip()
                if '[' in type_part and ']' in type_part:
                    param_var = type_part[type_part.index('[')+1:type_part.index(']')].strip()
                else:
                    print(f"Warning: Skipping invalid betting type definition: {line}")
                    continue
                current_betting_type = (betting_type, param_var)
                current_conditions.append(conditions.strip())
            elif current_section == 'betting' and line and current_betting_type:
                current_conditions.append(line.strip())

            elif current_section == 'operators':
                self.operators.add(line.strip())

        if current_betting_type and current_conditions:
            self._process_conditions(current_betting_type, current_conditions)

    def _process_conditions(self, betting_type_info, conditions):
        """Process conditional definitions for a betting type."""
        betting_type, param_var = betting_type_info
        self.betting_types[betting_type] = {}
        full_conditions = " ".join(conditions).strip()

        condition_parts = re.split(r'\s*else\s+if\s*', full_conditions)
        for i, part in enumerate(condition_parts):
            part = part.strip()
            if i > 0:
                part = f"if {part}"
            
            match = re.match(r'if\s*\(\s*([^=]+)\s*=\s*"([^"]+)"\s*\)\s*then\s*(.+)', part)
            if match:
                var, value, expr = match.groups()
                if var.strip() == param_var:
                    expr = expr.strip()
                    if 'else' in expr.lower():
                        expr = expr[:expr.lower().index('else')].strip()
                    self.betting_types[betting_type][value] = expr
            elif 'else' in part.lower() and 'if' not in part[part.lower().index('else'):]:
                else_expr = part.split('else')[-1].strip()
                self.betting_types[betting_type]['default'] = else_expr
            elif i == 0 and 'if' not in part:
                self.betting_types[betting_type]['default'] = part

    def reduce_expression(self, expr):
        """
        Recursively reduce an expression, handling operators AND, OR, NOT.
        
        Args:
            expr (str): The expression to reduce.
        
        Returns:
            str: The fully reduced expression.
        """
        expr = expr.strip()
        if expr.startswith('(') and expr.endswith(')'):
            stack = 0
            for i, char in enumerate(expr):
                if char == '(':
                    stack += 1
                elif char == ')':
                    stack -= 1
                if stack == 0 and i < len(expr) - 1:
                    break
            else:
                return f"({self.reduce_expression(expr[1:-1])})"

        term_pattern = r"(\w+)<([^>]+)>"
        if re.fullmatch(term_pattern, expr):
            match = re.match(term_pattern, expr)
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
                    return self.reduce_expression(definition)
            return expr

        # Check for betting option pattern (e.g., "DOUBLE_CHANCE 1X")
        betting_option_pattern = r"(\w+)\s+([^\s]+)"
        if re.fullmatch(betting_option_pattern, expr):
            return self.reduce_option(expr)

        for op in self.operators:
            if op in expr:
                if op == 'NOT':
                    match = re.match(r'NOT\s*\((.+)\)', expr)
                    if match:
                        sub_expr = match.group(1)
                        reduced_sub = self.reduce_expression(sub_expr)
                        return f"NOT({reduced_sub})"
                    match = re.match(r'NOT\s*(\w+<[^>]+>)', expr)
                    if match:
                        sub_expr = match.group(1)
                        reduced_sub = self.reduce_expression(sub_expr)
                        return f"NOT({reduced_sub})"
                else:
                    parts = self._split_expression(expr, op)
                    if parts:
                        left, right = parts
                        reduced_left = self.reduce_expression(left)
                        reduced_right = self.reduce_expression(right)
                        return f"({reduced_left} {op} {reduced_right})"

        return expr

    def _split_expression(self, expr, operator):
        """Split an expression on a binary operator, respecting parentheses."""
        stack = 0
        split_idx = -1
        for i, char in enumerate(expr):
            if char == '(':
                stack += 1
            elif char == ')':
                stack -= 1
            elif stack == 0 and expr[i:i+len(operator)] == operator:
                if (i == 0 or not expr[i-1].isalnum()) and (i+len(operator) == len(expr) or not expr[i+len(operator)].isalnum()):
                    split_idx = i
                    break
        if split_idx != -1:
            left = expr[:split_idx].strip()
            right = expr[split_idx + len(operator):].strip()
            return left, right
        return None

    def reduce_option(self, option):
        """
        Reduce a single betting option to its final form.
        
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
        
        expr = expr.strip('()')
        return self.reduce_expression(expr)

def main():
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

    reducer = BettingReducer(kb_content)
    
    # Prompt the user for a complex expression
    expression = input("Enter the betting expression (e.g., (DOUBLE_CHANCE 1X) OR (DOUBLE_CHANCE X2)): ").strip()
    reduced_form = reducer.reduce_expression(expression)
    print("Reduced form:", reduced_form)

if __name__ == "__main__":
    main()