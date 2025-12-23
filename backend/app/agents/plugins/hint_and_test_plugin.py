"""
Hint Strategy Plugin for Semantic Kernel
Provides progressive hint system for the AI interviewer
"""
from typing import Annotated
from semantic_kernel.functions import kernel_function


class HintStrategyPlugin:
    """
    Progressive hint system that provides increasingly detailed hints
    without giving away the complete solution.
    """
    
    # Hint templates by problem type and level
    HINT_TEMPLATES = {
        "two-sum": {
            1: "Think about what data structure could help you find a number quickly. What has O(1) lookup time?",
            2: "A Hash Map (Object in JavaScript) can store numbers you've seen. For each number, what would you need to find?",
            3: "For each number `num`, you need to find `target - num`. If you store seen numbers in a map, you can check if the complement exists in O(1).",
            4: "Here's the approach: Loop through array, for each num check if (target - num) exists in your map. If yes, return indices. If no, add current num to map."
        },
        "default": {
            1: "Take a step back and think about the problem requirements. What's the simplest case?",
            2: "Consider what data structures might help optimize your solution.",
            3: "Think about breaking the problem into smaller sub-problems.",
            4: "Try writing out the steps in plain English before coding."
        }
    }

    @kernel_function(
        description="Get a progressive hint based on the candidate's current progress level",
        name="get_progressive_hint"
    )
    def get_progressive_hint(
        self,
        hint_level: Annotated[int, "The hint level (1-4, where 1 is subtle and 4 is very direct)"],
        problem_id: Annotated[str, "The problem identifier (e.g., 'two-sum')"],
        current_error: Annotated[str, "The current error message if any"] = ""
    ) -> Annotated[str, "A helpful hint for the candidate"]:
        """Returns a hint appropriate for the given level"""
        
        # Clamp hint level
        level = max(1, min(4, hint_level))
        
        # Get hints for this problem
        hints = self.HINT_TEMPLATES.get(problem_id, self.HINT_TEMPLATES["default"])
        
        hint = hints.get(level, hints[1])
        
        # Add error-specific guidance if available
        if current_error:
            if "undefined" in current_error.lower():
                hint += "\n\n💡 Your error mentions 'undefined' - check that all variables are initialized before use."
            elif "not a function" in current_error.lower():
                hint += "\n\n💡 'Not a function' errors often mean you're calling a method on the wrong type."
            elif "cannot read property" in current_error.lower():
                hint += "\n\n💡 This error usually means you're accessing a property on null/undefined."
        
        return f"**Hint (Level {level}/4):** {hint}"

    @kernel_function(
        description="Determine the appropriate hint level based on candidate's struggle pattern",
        name="assess_hint_level"
    )
    def assess_hint_level(
        self,
        consecutive_errors: Annotated[int, "Number of consecutive errors"],
        time_spent_minutes: Annotated[int, "Minutes spent on the problem"],
        hints_already_given: Annotated[int, "Number of hints already provided"]
    ) -> Annotated[int, "Recommended hint level (1-4)"]:
        """Determines the appropriate hint level based on struggle indicators"""
        
        base_level = hints_already_given + 1
        
        # Escalate based on errors
        if consecutive_errors >= 5:
            base_level += 1
        
        # Escalate based on time
        if time_spent_minutes >= 15:
            base_level += 1
        elif time_spent_minutes >= 30:
            base_level += 2
        
        return max(1, min(4, base_level))

    @kernel_function(
        description="Generate encouragement message based on candidate progress",
        name="generate_encouragement"
    )
    def generate_encouragement(
        self,
        tests_passed: Annotated[int, "Number of tests passed"],
        total_tests: Annotated[int, "Total number of tests"],
        recent_improvement: Annotated[bool, "Whether the candidate improved since last run"]
    ) -> Annotated[str, "Encouraging message"]:
        """Generates contextual encouragement"""
        
        if tests_passed == total_tests:
            return "🎉 Excellent work! All tests passing! Let's discuss your approach and possible optimizations."
        
        if recent_improvement:
            progress_pct = (tests_passed / total_tests) * 100 if total_tests > 0 else 0
            return f"✨ Nice progress! You're now passing {tests_passed}/{total_tests} tests ({progress_pct:.0f}%). Keep going!"
        
        if tests_passed > 0:
            return f"👍 You've got {tests_passed} test(s) passing. Let's focus on the failing cases. What do they have in common?"
        
        return "💪 Don't worry, getting started is often the hardest part. Would you like to talk through your approach?"


class TestGenerationPlugin:
    """
    Dynamic test case generation for challenging the candidate's solution.
    """
    
    # Test case templates by problem
    TEST_CASES = {
        "two-sum": {
            "basic": {"input": "[2, 7, 11, 15], 9", "expected": "[0, 1]", "description": "Basic case"},
            "negative": {"input": "[-1, -2, -3, -4, -5], -8", "expected": "[2, 4]", "description": "Negative numbers"},
            "duplicates": {"input": "[3, 3], 6", "expected": "[0, 1]", "description": "Duplicate values"},
            "large": {"input": "[1, 2, 3, ..., 1000], 1999", "expected": "[998, 999]", "description": "Large array"},
            "unsorted": {"input": "[15, 2, 11, 7], 9", "expected": "[1, 3]", "description": "Unsorted array"},
        }
    }

    @kernel_function(
        description="Generate a new test case to challenge the candidate's solution",
        name="generate_challenge_test"
    )
    def generate_challenge_test(
        self,
        problem_id: Annotated[str, "The problem identifier"],
        edge_case_type: Annotated[str, "Type of edge case: 'basic', 'negative', 'duplicates', 'large', 'unsorted'"]
    ) -> Annotated[str, "A test case for the candidate"]:
        """Generates a specific test case"""
        
        tests = self.TEST_CASES.get(problem_id, {})
        test = tests.get(edge_case_type, None)
        
        if test:
            return f"""
**Challenge Test Case ({test['description']})**
- Input: `{test['input']}`
- Expected Output: `{test['expected']}`

Try running your solution with this input!
"""
        return f"Here's a challenge: try your solution with an edge case like {edge_case_type}."

    @kernel_function(
        description="Suggest the next test case based on what the candidate has passed",
        name="suggest_next_test"
    )
    def suggest_next_test(
        self,
        problem_id: Annotated[str, "The problem identifier"],
        passed_test_types: Annotated[str, "Comma-separated list of passed test types"]
    ) -> Annotated[str, "Suggestion for next test to try"]:
        """Suggests what test to try next"""
        
        passed = set(passed_test_types.split(',')) if passed_test_types else set()
        priority_order = ["basic", "negative", "duplicates", "unsorted", "large"]
        
        for test_type in priority_order:
            if test_type not in passed:
                return f"Next, try testing with a **{test_type}** case to verify your solution handles it correctly."
        
        return "Great! You've covered the main test categories. Consider time/space optimization next."
