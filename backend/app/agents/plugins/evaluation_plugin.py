"""
Evaluation Plugin for Semantic Kernel
Provides real-time candidate evaluation and scoring
"""
from typing import Annotated
from semantic_kernel.functions import kernel_function
import re


class EvaluationPlugin:
    """
    Candidate evaluation tools for the AI interviewer.
    Scores candidates on multiple dimensions in real-time.
    """

    @kernel_function(
        description="Calculate a comprehensive score for the candidate's solution",
        name="calculate_score"
    )
    def calculate_score(
        self,
        code: Annotated[str, "The candidate's code submission"],
        tests_passed: Annotated[int, "Number of tests passed"],
        total_tests: Annotated[int, "Total number of tests"],
        time_spent_minutes: Annotated[int, "Time spent in minutes"],
        hints_used: Annotated[int, "Number of hints requested"]
    ) -> Annotated[str, "Scoring breakdown"]:
        """Calculates a multi-dimensional score"""
        
        scores = {
            "correctness": 0,
            "efficiency": 0,
            "code_quality": 0,
            "problem_solving": 0,
            "communication": 0  # Would need chat analysis for real scoring
        }
        
        # Correctness (40 points max)
        if total_tests > 0:
            correctness_pct = tests_passed / total_tests
            scores["correctness"] = int(correctness_pct * 40)
        
        # Efficiency (20 points max) - based on time and approach
        if time_spent_minutes <= 15:
            scores["efficiency"] = 20
        elif time_spent_minutes <= 25:
            scores["efficiency"] = 15
        elif time_spent_minutes <= 40:
            scores["efficiency"] = 10
        else:
            scores["efficiency"] = 5
        
        # Code Quality (20 points max)
        quality_score = 20
        if 'var ' in code:
            quality_score -= 3
        if not re.search(r'//|/\*', code):  # No comments
            quality_score -= 2
        if code.count('\n') < 3:  # Too compact
            quality_score -= 2
        if 'console.log' in code:
            quality_score -= 1
        scores["code_quality"] = max(0, quality_score)
        
        # Problem Solving (20 points max) - reduced by hints used
        base_problem_solving = 20
        hint_penalty = hints_used * 3
        scores["problem_solving"] = max(0, base_problem_solving - hint_penalty)
        
        # Total
        total = sum(scores.values())
        
        return f"""
**Evaluation Score: {total}/100**

| Dimension | Score | Notes |
|-----------|-------|-------|
| Correctness | {scores['correctness']}/40 | {tests_passed}/{total_tests} tests passed |
| Efficiency | {scores['efficiency']}/20 | Completed in {time_spent_minutes} min |
| Code Quality | {scores['code_quality']}/20 | Style and readability |
| Problem Solving | {scores['problem_solving']}/20 | {hints_used} hints used |

**Grade:** {'Excellent' if total >= 85 else 'Good' if total >= 70 else 'Satisfactory' if total >= 55 else 'Needs Improvement'}
"""

    @kernel_function(
        description="Generate feedback for the candidate based on their performance",
        name="generate_feedback"
    )
    def generate_feedback(
        self,
        code: Annotated[str, "The candidate's code"],
        total_score: Annotated[int, "The candidate's total score"],
        main_weakness: Annotated[str, "The main area needing improvement"]
    ) -> Annotated[str, "Constructive feedback for the candidate"]:
        """Generates personalized feedback"""
        
        strengths = []
        improvements = []
        
        # Analyze code for feedback
        if '.map(' in code or '.filter(' in code or '.reduce(' in code:
            strengths.append("Good use of functional programming methods")
        
        if 'const ' in code and 'let ' in code:
            strengths.append("Proper use of const/let for variable declarations")
        
        if re.search(r'//.*\n|/\*[\s\S]*?\*/', code):
            strengths.append("Code includes helpful comments")
        
        if 'Map' in code or '{}' in code:
            strengths.append("Efficient use of hash map for lookups")
        
        # Improvements based on score
        if total_score < 70:
            improvements.append("Practice more algorithm problems to improve speed")
        
        if main_weakness == "correctness":
            improvements.append("Focus on edge cases and test your solution thoroughly")
        elif main_weakness == "efficiency":
            improvements.append("Study time complexity and optimize your initial approach before coding")
        elif main_weakness == "code_quality":
            improvements.append("Add comments and use meaningful variable names")
        
        return f"""
**Performance Feedback**

✅ **Strengths:**
{chr(10).join(f'  - {s}' for s in strengths) if strengths else '  - Keep practicing!'}

📈 **Areas for Improvement:**
{chr(10).join(f'  - {i}' for i in improvements) if improvements else '  - Great job overall!'}
"""

    @kernel_function(
        description="Determine if the candidate should receive a follow-up challenge",
        name="should_give_followup"
    )
    def should_give_followup(
        self,
        tests_passed: Annotated[int, "Number of tests passed"],
        total_tests: Annotated[int, "Total number of tests"],
        time_remaining_minutes: Annotated[int, "Time remaining in the interview"]
    ) -> Annotated[str, "Whether to give a follow-up and why"]:
        """Decides if a follow-up challenge is appropriate"""
        
        all_passed = tests_passed == total_tests
        has_time = time_remaining_minutes >= 10
        
        if all_passed and has_time:
            return "YES - Candidate solved the problem with time remaining. Suggest discussing optimization or a follow-up variation."
        elif all_passed:
            return "DISCUSS - All tests passed. Use remaining time to discuss the approach and complexity."
        else:
            return "NO - Focus on completing the current problem first."
