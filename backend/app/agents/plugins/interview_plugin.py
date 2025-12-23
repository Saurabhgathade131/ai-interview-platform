from typing import Annotated
from semantic_kernel.functions import kernel_function

class InterviewerPlugin:
    """
    Tools for the AI Interviewer to assess code and manage the interview flow.
    """

    @kernel_function(
        description="Analyzes the given code for logical errors, complexity, and style issues.",
        name="analyze_code"
    )
    def analyze_code(
        self,
        code: Annotated[str, "The source code written by the candidate"]
    ) -> Annotated[str, "The analysis report of the code"]:
        """
        Analyzes the code complexity and potential bugs.
        In a real scenario, this might call an external linter or a specialized AST analyzer.
        For now, it returns a structured prompt for the LLM to process internally, 
        or we could return static analysis results.
        """
        if not code or code.strip() == "":
            return "No code provided to analyze."
        
        # In a generic plugin, we might just acknowledge the code length or structure.
        # But this function gives the Agent explicit 'permission' to stop and read the code deeply.
        return f"Code Analysis Request Received. Code Length: {len(code)} chars. The Agent should now review the syntax and logic critically."

    @kernel_function(
        description="Generates a helpful hint for the candidate without revealing the solution.",
        name="provide_hint"
    )
    def provide_hint(
        self,
        error_message: Annotated[str, "The error message the user is seeing, if any"],
        problem_type: Annotated[str, "The type of algorithm (e.g. Array, DFS, DP)"]
    ) -> str:
        """
        Generates a hint based on the error.
        """
        return f"Hint Strategy: Focus on {problem_type}. specific error: {error_message}. Suggest looking at edge cases or initialization."

    @kernel_function(
        description="Generates a new test case to challenge the candidate's solution.",
        name="generate_test_case"
    )
    def generate_test_case(
        self,
        edge_case_type: Annotated[str, "Type of edge case (e.g. empty input, max int, negative numbers)"]
    ) -> str:
        return f"Proposed Test Case: A generic test case for {edge_case_type}."
