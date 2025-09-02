import re

# Define Node classes for the tree structure
class Node:
    def __init__(self, value):
        self.value = value
        self.children = []

    def add_child(self, child):
        self.children.append(child)

class OperatorNode(Node):
    """Represents logical operators like OR, AND, NOT."""
    pass

class BettingTypeNode(Node):
    """Represents betting types like DOUBLE_CHANCE 1X."""
    pass

class BasicTermNode(Node):
    """Represents basic terms like WINS<TEAM_HOME,TEAM_AWAY>."""
    pass

class PrimitiveNode(Node):
    """Represents primitive expressions that cannot be further reduced."""
    pass

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
        # Assume this is already implemented as in your original code
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

    def build_reduction_tree(self, expr):
        """
        Build a reduction tree from the given betting expression.
        
        Args:
            expr (str): The betting expression, e.g., "(DOUBLE_CHANCE 1X) OR (DOUBLE_CHANCE X2)".
        
        Returns:
            Node: The root of the reduction tree.
        """
        ast = self.parse_expression(expr)
        self.expand_node(ast)
        return ast

    def expand_node(self, node):
        # Handle betting type nodes (e.g., DOUBLE_CHANCE 1X)
        if isinstance(node, BettingTypeNode):
            definition = self.get_definition_for_betting_type(node.value)
            child_ast = self.parse_expression(definition)  # Parse the definition into an AST
            self.expand_node(child_ast)  # Recursively expand the child AST
            node.add_child(child_ast)    # Add the expanded child to the tree
        
        # Handle basic term nodes (e.g., WINS<TEAM_HOME,TEAM_AWAY>)
        elif isinstance(node, BasicTermNode):
            definition = self.get_definition_for_basic_term(node.value)
            child_ast = self.parse_expression(definition)  # Parse the basic term's definition
            self.expand_node(child_ast)  # Recursively expand the child AST
            node.add_child(child_ast)    # Replace the basic term with its expanded form
        
        # Handle operator nodes (e.g., OR, ||)
        elif isinstance(node, OperatorNode):
            for child in node.children:
                self.expand_node(child)  # Recursively expand each child
        
        # Primitive nodes (e.g., final conditions) have no children, so stop here

    def find_top_level_operator(self, expr):
        level = 0
        for i in range(len(expr)):
            if expr[i] == '(':
                level += 1
            elif expr[i] == ')':
                level -= 1
            elif level == 0:
                if expr[i:i+4] == ' OR ' or expr[i:i+4] == ' || ':
                    return expr[i:i+4], i  # ' OR ' or ' || '
                elif expr[i:i+5] == ' AND ' or expr[i:i+5] == ' && ':
                    return expr[i:i+5], i  # ' AND ' or ' && '
        return None, -1

    # Optional: Update parse_expression for '!' support
    def parse_expression(self, expr):
        expr = self.strip_outer_parens(expr)
        if expr.startswith('NOT ') or expr.startswith('!'):
            if expr.startswith('NOT '):
                operand = expr[4:].strip()
            else:
                operand = expr[1:].strip()
            node = OperatorNode('NOT')  # or '!' to keep original symbol
            child = self.parse_expression(operand)
            node.add_child(child)
            return node
        else:
            operator, pos = self.find_top_level_operator(expr)
            if operator:
                left = expr[:pos].strip()
                right = expr[pos + len(operator):].strip()
                node = OperatorNode(operator.strip())
                left_node = self.parse_expression(left)
                right_node = self.parse_expression(right)
                node.add_child(left_node)
                node.add_child(right_node)
                return node
            else:
                if self.is_betting_type(expr):
                    return BettingTypeNode(expr)
                elif self.is_basic_term(expr):
                    return BasicTermNode(expr)
                else:
                    return PrimitiveNode(expr)

    def strip_outer_parens(self, expr):
        """Remove outer parentheses if they enclose the entire expression."""
        expr = expr.strip()
        if expr.startswith('(') and expr.endswith(')') and self._is_balanced(expr[1:-1]):
            return expr[1:-1].strip()
        return expr

    def _is_balanced(self, expr):
        """Check if parentheses in the expression are balanced."""
        stack = 0
        for char in expr:
            if char == '(':
                stack += 1
            elif char == ')':
                stack -= 1
                if stack < 0:
                    return False
        return stack == 0

    def find_top_level_operator(self, expr):
        """Find the top-level binary operator (AND/OR) outside parentheses."""
        level = 0
        for i in range(len(expr)):
            if expr[i] == '(':
                level += 1
            elif expr[i] == ')':
                level -= 1
            elif level == 0:
                if expr[i:i+4] == ' OR ':
                    return ' OR ', i
                elif expr[i:i+5] == ' AND ':
                    return ' AND ', i
        return None, -1

    def is_betting_type(self, expr):
        """Check if the expression is a betting type like 'DOUBLE_CHANCE 1X'."""
        parts = expr.split(" ", 1)
        if len(parts) == 2:
            betting_type = parts[0]
            param = parts[1].strip()
            if betting_type in self.betting_types and not param.startswith('<'):
                return True
        return False

    def is_basic_term(self, expr):
        """Check if the expression is a basic term like 'WINS<TEAM_HOME,TEAM_AWAY>'."""
        match = re.match(r"(\w+)<([^>]+)>", expr)
        if match:
            term = match.group(1)
            if term in self.basic_terms:
                return True
        return False

    def get_definition_for_betting_type(self, expr):
        """Retrieve the definition for a betting type."""
        parts = expr.split(" ", 1)
        if len(parts) != 2:
            raise ValueError("Invalid betting type expression")
        betting_type, param = parts[0], parts[1].strip()
        if betting_type not in self.betting_types:
            raise ValueError(f"Unknown betting type: {betting_type}")
        betting_rules = self.betting_types[betting_type]
        definition = betting_rules.get(param, betting_rules.get('default'))
        if definition is None:
            raise ValueError(f"No definition for parameter '{param}' in {betting_type}")
        return definition

    def get_definition_for_basic_term(self, expr):
        """Retrieve the definition for a basic term, substituting parameters."""
        match = re.match(r"(\w+)<([^>]+)>", expr)
        if not match:
            raise ValueError("Invalid basic term expression")
        term = match.group(1)
        params_str = match.group(2)
        params = [p.strip() for p in params_str.split(",")]
        if term not in self.basic_terms:
            raise ValueError(f"Unknown basic term: {term}")
        term_info = self.basic_terms[term]
        definition = term_info['definition']
        for i, param in enumerate(params):
            placeholder = f"<{term_info['params'][i]}>"
            definition = definition.replace(placeholder, f"<{param}>")
        return definition

def print_tree(node, depth=0):
    """
    Print the reduction tree hierarchically.
    
    Args:
        node (Node): The node to print.
        depth (int): The current indentation level.
    """
    indent = "  " * depth
    if isinstance(node, OperatorNode):
        print(f"{indent}{node.value}")
        for child in node.children:
            print_tree(child, depth + 1)
    elif isinstance(node, BettingTypeNode):
        print(f"{indent}{node.value}")
        if node.children:
            print_tree(node.children[0], depth + 1)
    elif isinstance(node, BasicTermNode):
        print(f"{indent}{node.value}")
        if node.children:
            print_tree(node.children[0], depth + 1)
    elif isinstance(node, PrimitiveNode):
        print(f"{indent}{node.value}")

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
    expression = input("Enter the betting expression (e.g., (DOUBLE_CHANCE 1X) OR (DOUBLE_CHANCE X2)): ").strip()
    tree = reducer.build_reduction_tree(expression)
    print("Reduction Tree:")
    print_tree(tree)

if __name__ == "__main__":
    main()