"""
Code Analysis Plugin for Semantic Kernel
Provides deep code analysis capabilities for the AI interviewer
"""
from typing import Annotated
import re
from semantic_kernel.functions import kernel_function


class CodeAnalysisPlugin:
    """
    Advanced code analysis tools for the AI interviewer.
    Analyzes JavaScript code for patterns, complexity, and potential issues.
    """

    @kernel_function(
        description="Analyze code structure, complexity, and identify potential bugs or issues",
        name="analyze_code_structure"
    )
    def analyze_code_structure(
        self,
        code: Annotated[str, "The JavaScript source code to analyze"]
    ) -> Annotated[str, "Structured analysis of the code"]:
        """Performs structural analysis of the code"""
        
        if not code or code.strip() == "":
            return "No code provided to analyze."
        
        analysis = {
            "lines_of_code": len(code.strip().split('\n')),
            "functions_detected": [],
            "loops_detected": [],
            "conditionals_detected": [],
            "potential_issues": [],
            "patterns_used": []
        }
        
        # Detect function declarations
        func_patterns = [
            r'function\s+(\w+)\s*\(',  # function name()
            r'const\s+(\w+)\s*=\s*\(.*\)\s*=>',  # const name = () =>
            r'const\s+(\w+)\s*=\s*function',  # const name = function
        ]
        for pattern in func_patterns:
            matches = re.findall(pattern, code)
            analysis["functions_detected"].extend(matches)
        
        # Detect loops
        if 'for' in code:
            for_matches = re.findall(r'for\s*\(', code)
            analysis["loops_detected"].append(f"for loops: {len(for_matches)}")
        if 'while' in code:
            while_matches = re.findall(r'while\s*\(', code)
            analysis["loops_detected"].append(f"while loops: {len(while_matches)}")
        if '.forEach' in code:
            analysis["loops_detected"].append("forEach used")
        if '.map' in code:
            analysis["loops_detected"].append("map used")
            analysis["patterns_used"].append("Functional programming (map)")
        
        # Detect conditionals
        if_matches = re.findall(r'if\s*\(', code)
        if if_matches:
            analysis["conditionals_detected"].append(f"if statements: {len(if_matches)}")
        
        # Detect common patterns
        if 'new Map' in code or '{}' in code:
            analysis["patterns_used"].append("Hash Map / Object for lookup")
        if '.sort(' in code:
            analysis["patterns_used"].append("Sorting")
        if 'new Set' in code:
            analysis["patterns_used"].append("Set for uniqueness")
        if '.reduce(' in code:
            analysis["patterns_used"].append("Reduce for aggregation")
        
        # Detect potential issues
        if 'var ' in code:
            analysis["potential_issues"].append("Uses 'var' - consider 'let' or 'const'")
        if '==' in code and '===' not in code:
            analysis["potential_issues"].append("Uses loose equality '==' - consider strict '==='")
        if 'console.log' in code:
            analysis["potential_issues"].append("Contains console.log - may want to remove for production")
        
        # Check for nested loops (O(n²) potential)
        nested_loop_pattern = r'for.*\{[^}]*for|while.*\{[^}]*while'
        if re.search(nested_loop_pattern, code, re.DOTALL):
            analysis["potential_issues"].append("Nested loops detected - O(n²) time complexity possible")
        
        # Build response
        response = f"""
**Code Analysis Report**
- Lines of Code: {analysis['lines_of_code']}
- Functions: {', '.join(analysis['functions_detected']) if analysis['functions_detected'] else 'None detected'}
- Loops: {', '.join(analysis['loops_detected']) if analysis['loops_detected'] else 'None'}
- Conditionals: {', '.join(analysis['conditionals_detected']) if analysis['conditionals_detected'] else 'None'}
- Patterns Used: {', '.join(analysis['patterns_used']) if analysis['patterns_used'] else 'None identified'}
- Potential Issues: {', '.join(analysis['potential_issues']) if analysis['potential_issues'] else 'None found'}
"""
        return response.strip()

    @kernel_function(
        description="Estimate the time and space complexity of the code",
        name="estimate_complexity"
    )
    def estimate_complexity(
        self,
        code: Annotated[str, "The source code to analyze"],
        problem_type: Annotated[str, "The type of problem (e.g., 'array search', 'sorting', 'graph')"]
    ) -> Annotated[str, "Complexity estimation"]:
        """Estimates Big-O complexity based on code patterns"""
        
        complexity = {
            "time": "O(n)",  # Default assumption
            "space": "O(1)",
            "reasoning": []
        }
        
        # Check for nested loops
        nested_for = len(re.findall(r'for.*for', code, re.DOTALL))
        if nested_for > 0:
            complexity["time"] = "O(n²)"
            complexity["reasoning"].append("Nested loops detected")
        
        # Check for hash map usage (often improves time complexity)
        if 'Map' in code or 'Object' in code or '{}' in code:
            if nested_for == 0:
                complexity["time"] = "O(n)"
                complexity["reasoning"].append("Hash map used for O(1) lookups")
            complexity["space"] = "O(n)"
            complexity["reasoning"].append("Additional data structure stores elements")
        
        # Check for sorting
        if '.sort(' in code:
            if complexity["time"] == "O(n)":
                complexity["time"] = "O(n log n)"
            complexity["reasoning"].append("Sorting operation detected")
        
        # Check for recursion
        func_names = re.findall(r'function\s+(\w+)', code)
        for func_name in func_names:
            if func_name in code.split(func_name, 1)[1]:
                complexity["reasoning"].append(f"Recursive call to {func_name} detected")
        
        return f"""
**Complexity Analysis**
- Time Complexity: {complexity['time']}
- Space Complexity: {complexity['space']}
- Reasoning: {'; '.join(complexity['reasoning']) if complexity['reasoning'] else 'Basic linear scan assumed'}
"""

    @kernel_function(
        description="Check if the code handles common edge cases",
        name="check_edge_cases"
    )
    def check_edge_cases(
        self,
        code: Annotated[str, "The source code to check"],
        problem_id: Annotated[str, "The problem identifier"]
    ) -> Annotated[str, "Edge case coverage analysis"]:
        """Checks for common edge case handling"""
        
        edge_cases = {
            "empty_input": False,
            "single_element": False,
            "negative_numbers": False,
            "duplicates": False,
            "boundary_values": False
        }
        
        # Check for empty array handling
        if 'length === 0' in code or 'length == 0' in code or '!nums' in code or 'nums.length < ' in code:
            edge_cases["empty_input"] = True
        
        # Check for single element
        if 'length === 1' in code or 'length == 1' in code:
            edge_cases["single_element"] = True
        
        # Check for negative number handling
        if '< 0' in code or 'negative' in code.lower():
            edge_cases["negative_numbers"] = True
        
        # Check for duplicate handling
        if 'Set' in code or 'duplicate' in code.lower() or 'seen' in code:
            edge_cases["duplicates"] = True
        
        covered = [k for k, v in edge_cases.items() if v]
        missing = [k for k, v in edge_cases.items() if not v]
        
        return f"""
**Edge Case Analysis**
- Covered: {', '.join(covered) if covered else 'None explicitly handled'}
- Potentially Missing: {', '.join(missing) if missing else 'All common cases appear covered'}

Consider testing with: empty array [], single element [1], negative numbers [-1, -2], and duplicates [1, 1, 2].
"""
