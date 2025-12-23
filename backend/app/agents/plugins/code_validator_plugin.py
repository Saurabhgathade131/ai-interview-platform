"""
Code Validation Plugin for Semantic Kernel
Silently validates candidate code and provides hints based on errors
"""
from typing import Annotated, Dict, Any, Optional
from semantic_kernel.functions import kernel_function


class CodeValidatorPlugin:
    """
    Background code validation tools.
    Silently executes code and analyzes errors to provide helpful hints.
    """

    @kernel_function(
        description="Analyze code execution results and suggest hints based on errors",
        name="analyze_execution_result"
    )
    def analyze_execution_result(
        self,
        stdout: Annotated[str, "Standard output from code execution"],
        stderr: Annotated[str, "Standard error from code execution"],
        tests_passed: Annotated[int, "Number of tests passed"],
        tests_total: Annotated[int, "Total number of tests"]
    ) -> Annotated[str, "Analysis and hints based on execution result"]:
        """Analyze execution results and suggest next steps"""
        
        if tests_passed == tests_total and tests_total > 0:
            return "ALL_PASSED: Candidate's solution passed all tests! Consider asking follow-up questions about optimization."
        
        hints = []
        
        # Analyze stderr for common errors
        if stderr:
            stderr_lower = stderr.lower()
            
            if "is not defined" in stderr_lower:
                hints.append("Variable or function is not defined - check for typos in variable names")
            
            if "is not a function" in stderr_lower:
                hints.append("Trying to call something that isn't a function - check the data types")
            
            if "cannot read property" in stderr_lower or "undefined" in stderr_lower:
                hints.append("Accessing a property on null/undefined - add null checks or verify array bounds")
            
            if "syntax error" in stderr_lower:
                hints.append("Syntax error in code - check for missing brackets, semicolons, or typos")
            
            if "maximum call stack" in stderr_lower:
                hints.append("Infinite recursion detected - check your base case")
        
        # Analyze stdout for test failures
        if stdout:
            failed_tests = stdout.count("✗ Test")
            if failed_tests > 0:
                hints.append(f"{failed_tests} test(s) failing - check edge cases")
                
                if "expected" in stdout.lower():
                    hints.append("Output doesn't match expected - verify your logic")
        
        if not hints:
            hints.append("General suggestion: trace through your code with a simple example")
        
        return f"NEEDS_HELP: {'; '.join(hints)}"

    @kernel_function(
        description="Generate a proactive hint based on common mistakes for a problem type",
        name="get_proactive_hint"
    )
    def get_proactive_hint(
        self,
        problem_id: Annotated[str, "The problem identifier"],
        error_pattern: Annotated[str, "The type of error: 'undefined', 'wrong_output', 'timeout', 'syntax'"]
    ) -> Annotated[str, "A helpful hint without giving away the solution"]:
        """Generate context-aware hints based on error patterns"""
        
        hints = {
            "two-sum": {
                "undefined": "Make sure you're returning an array of indices, not the values themselves.",
                "wrong_output": "Remember: you need to return the INDICES of the two numbers, not the numbers. Also check if the order matters.",
                "timeout": "A nested loop gives O(n²). Can you use a hash map to achieve O(n)?",
                "syntax": "Check that your function is named 'twoSum' exactly as specified."
            },
            "reverse-string": {
                "undefined": "Are you modifying the array in-place? Remember not to create a new array.",
                "wrong_output": "The function should modify the input array directly. Use two pointers from both ends.",
                "timeout": "The two-pointer approach should be O(n). Make sure your loop condition is correct.",
                "syntax": "The function should be named 'reverseString' and take one parameter."
            },
            "valid-palindrome": {
                "undefined": "Did you handle the case-insensitive comparison?",
                "wrong_output": "Remember to ignore non-alphanumeric characters and compare case-insensitively.",
                "timeout": "You can solve this in O(n) with two pointers.",
                "syntax": "The function should return a boolean (true/false)."
            },
            "maximum-subarray": {
                "undefined": "Are you tracking both the current sum and the maximum sum seen so far?",
                "wrong_output": "Consider Kadane's algorithm: reset current sum when it goes negative.",
                "timeout": "This can be solved in O(n) time with Kadane's algorithm.",
                "syntax": "The function should return a single number, not an array."
            },
            "merge-sorted-arrays": {
                "undefined": "Remember to modify nums1 in-place. Work from the end of both arrays.",
                "wrong_output": "Start filling nums1 from the end (position m+n-1) to avoid overwriting.",
                "timeout": "This should be O(m+n) using the three-pointer technique.",
                "syntax": "The function doesn't return anything - it modifies nums1 in-place."
            }
        }
        
        problem_hints = hints.get(problem_id, {})
        return problem_hints.get(error_pattern, "Take a step back and trace through your code with a simple example.")

    @kernel_function(
        description="Determine if the AI should offer help based on candidate's struggle indicators",
        name="should_offer_help"
    )
    def should_offer_help(
        self,
        consecutive_errors: Annotated[int, "Number of consecutive failed runs"],
        time_since_last_success_minutes: Annotated[int, "Minutes since last successful test"],
        total_attempts: Annotated[int, "Total number of code runs"]
    ) -> Annotated[str, "YES/NO and reason"]:
        """Decide if the AI should proactively offer assistance"""
        
        # Very stuck - 5+ consecutive errors
        if consecutive_errors >= 5:
            return "YES: Candidate has had 5+ consecutive errors. Offer a targeted hint."
        
        # Stuck for a while with attempts
        if time_since_last_success_minutes >= 10 and total_attempts >= 3:
            return "YES: Candidate has been struggling for 10+ minutes. Check if they need guidance."
        
        # Just started struggling
        if consecutive_errors >= 3:
            return "MAYBE: 3 consecutive errors. Consider asking if they'd like a hint."
        
        # Making progress
        return "NO: Candidate appears to be making progress. Let them continue."

    @kernel_function(
        description="Classify the type of error from stderr/stdout",
        name="classify_error"
    )
    def classify_error(
        self,
        stderr: Annotated[str, "Standard error output"],
        stdout: Annotated[str, "Standard output"]
    ) -> Annotated[str, "Error classification: syntax, runtime, logic, timeout, or none"]:
        """Classify the error type to provide appropriate hints"""
        
        if not stderr and not stdout:
            return "none"
        
        combined = (stderr + stdout).lower()
        
        if "syntax" in combined:
            return "syntax"
        
        if "maximum call stack" in combined or "timeout" in combined:
            return "timeout"
        
        if any(err in combined for err in ["undefined", "is not a function", "cannot read property", "typeerror", "referenceerror"]):
            return "runtime"
        
        if "✗ test" in combined or "failed" in combined:
            return "logic"
        
        return "none"
