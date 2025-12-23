"""
Dynamic Problem Generation Plugin for Semantic Kernel
Generates coding problems, questions, and test cases based on candidate profile
"""
from typing import Annotated, List, Dict, Any
from semantic_kernel.functions import kernel_function


class ProblemGeneratorPlugin:
    """
    Dynamically generates interview problems, questions, and test cases
    based on candidate experience level and target role.
    """
    
    # Problem templates by difficulty
    PROBLEM_CATEGORIES = {
        "arrays": ["Two Sum", "Maximum Subarray", "Merge Sorted Arrays", "Find Duplicates"],
        "strings": ["Reverse String", "Valid Palindrome", "Longest Substring", "String Compression"],
        "linked_lists": ["Reverse Linked List", "Detect Cycle", "Merge Two Lists"],
        "trees": ["Binary Tree Traversal", "Validate BST", "Lowest Common Ancestor"],
        "dynamic_programming": ["Fibonacci", "Climbing Stairs", "Coin Change", "Longest Increasing Subsequence"],
        "graphs": ["BFS/DFS Traversal", "Number of Islands", "Shortest Path"],
    }
    
    DIFFICULTY_MAP = {
        "junior": ["arrays", "strings"],
        "mid": ["arrays", "strings", "linked_lists", "trees"],
        "senior": ["arrays", "strings", "linked_lists", "trees", "dynamic_programming", "graphs"],
    }

    @kernel_function(
        description="Generate a coding problem tailored to the candidate's experience level",
        name="generate_problem"
    )
    def generate_problem(
        self,
        experience_years: Annotated[int, "Years of experience (0-15+)"],
        target_role: Annotated[str, "Target role (frontend, backend, fullstack, data)"],
        focus_area: Annotated[str, "Optional focus area like 'arrays' or 'algorithms'"] = ""
    ) -> Annotated[str, "A problem description with requirements"]:
        """Generate a problem suitable for the candidate's level"""
        
        # Determine difficulty
        if experience_years <= 2:
            level = "junior"
            complexity = "O(n) or O(n log n)"
            time_limit = "30 minutes"
        elif experience_years <= 5:
            level = "mid"
            complexity = "O(n) to O(n²)"
            time_limit = "25 minutes"
        else:
            level = "senior"
            complexity = "optimal solution expected"
            time_limit = "20 minutes"
        
        # Select category
        available_categories = self.DIFFICULTY_MAP.get(level, ["arrays"])
        category = focus_area if focus_area in available_categories else available_categories[0]
        
        return f"""
**Generated Problem for {level.title()} {target_role.title()} Candidate**

**Category:** {category.replace('_', ' ').title()}
**Expected Complexity:** {complexity}
**Time Limit:** {time_limit}

Please generate a specific coding problem in this category that:
1. Matches the {level} difficulty level
2. Is relevant to {target_role} work
3. Has clear input/output requirements
4. Includes 3-5 example test cases
"""

    @kernel_function(
        description="Generate test cases for a given problem based on the problem description",
        name="generate_test_cases"
    )
    def generate_test_cases(
        self,
        problem_description: Annotated[str, "The problem statement"],
        difficulty_level: Annotated[str, "junior, mid, or senior"],
        num_cases: Annotated[int, "Number of test cases to generate (3-10)"] = 5
    ) -> Annotated[str, "Generated test cases with inputs and expected outputs"]:
        """Generate appropriate test cases for the problem"""
        
        edge_cases = {
            "junior": ["basic case", "empty input", "single element"],
            "mid": ["basic case", "empty input", "single element", "large input", "negative numbers"],
            "senior": ["basic case", "empty input", "edge boundaries", "large input (10^6)", "negative numbers", "duplicate values", "sorted input", "reverse sorted"],
        }
        
        cases_to_cover = edge_cases.get(difficulty_level, edge_cases["junior"])[:num_cases]
        
        return f"""
**Test Case Generation Request**

For the given problem, generate {num_cases} test cases covering:
{chr(10).join(f'- {case}' for case in cases_to_cover)}

Each test case should include:
1. **Input**: The exact input values
2. **Expected Output**: The correct result
3. **Explanation**: Why this output is expected

Format each test case as:
```
Test {n}: {case_type}
Input: <value>
Expected: <value>
Explanation: <brief explanation>
```
"""

    @kernel_function(
        description="Generate follow-up questions based on the candidate's solution",
        name="generate_followup_questions"
    )
    def generate_followup_questions(
        self,
        solution_code: Annotated[str, "The candidate's submitted code"],
        time_complexity: Annotated[str, "The time complexity of their solution"],
        experience_level: Annotated[str, "junior, mid, or senior"]
    ) -> Annotated[str, "Follow-up questions to ask the candidate"]:
        """Generate relevant follow-up questions"""
        
        questions = {
            "junior": [
                "Can you walk me through your approach step by step?",
                "What's the time complexity of your solution?",
                "How would you test this code?",
            ],
            "mid": [
                "Can you optimize this further?",
                "What's the space complexity? Can it be reduced?",
                "How would this scale with 1 million inputs?",
                "What edge cases might break your solution?",
            ],
            "senior": [
                "What trade-offs did you consider?",
                "How would you parallelize this?",
                "Can you achieve O(1) space complexity?",
                "How would you design this for a distributed system?",
                "What's your testing strategy for production?",
            ],
        }
        
        level_questions = questions.get(experience_level, questions["junior"])
        
        return f"""
**Suggested Follow-up Questions for {experience_level.title()} Candidate:**

{chr(10).join(f'{i+1}. {q}' for i, q in enumerate(level_questions))}

Based on their {time_complexity} solution, also consider asking about:
- Alternative approaches they considered
- How they would handle concurrent access
- Error handling strategies
"""

    @kernel_function(
        description="Assess the candidate's experience level based on their profile",
        name="assess_experience_level"
    )
    def assess_experience_level(
        self,
        years_experience: Annotated[int, "Years of professional experience"],
        skills: Annotated[str, "Comma-separated list of skills"],
        education: Annotated[str, "Highest education level"]
    ) -> Annotated[str, "Assessment of candidate level and recommended problem difficulty"]:
        """Assess candidate level for appropriate problem selection"""
        
        # Parse skills
        skill_list = [s.strip().lower() for s in skills.split(',')]
        
        # Score based on various factors
        score = 0
        
        # Experience points
        score += min(years_experience * 2, 10)
        
        # Advanced skills
        advanced_skills = ['distributed systems', 'system design', 'kubernetes', 'microservices', 'ml', 'ai']
        intermediate_skills = ['react', 'node', 'python', 'java', 'sql', 'docker', 'aws', 'azure']
        
        for skill in skill_list:
            if any(adv in skill for adv in advanced_skills):
                score += 2
            elif any(mid in skill for mid in intermediate_skills):
                score += 1
        
        # Determine level
        if score >= 15:
            level = "senior"
            problems = "Graph algorithms, DP, System Design discussions"
        elif score >= 8:
            level = "mid"
            problems = "Trees, Linked Lists, moderate array problems"
        else:
            level = "junior"
            problems = "Array manipulation, String processing, basic algorithms"
        
        return f"""
**Candidate Assessment**

- **Assessed Level:** {level.title()}
- **Score:** {score}/20
- **Recommended Problems:** {problems}

**Interview Strategy:**
- Start with a {level}-appropriate problem
- Adjust difficulty based on their performance
- Focus on problem-solving process, not just correctness
"""


class InterviewCustomizerPlugin:
    """
    Customizes the entire interview experience based on candidate and role requirements.
    """

    @kernel_function(
        description="Generate a personalized interview introduction based on candidate profile",
        name="generate_introduction"
    )
    def generate_introduction(
        self,
        candidate_name: Annotated[str, "Candidate's name"],
        target_role: Annotated[str, "The role they're applying for"],
        experience_years: Annotated[int, "Years of experience"],
        company_context: Annotated[str, "Brief context about what the company does"] = ""
    ) -> Annotated[str, "Personalized introduction for the interview"]:
        """Generate a warm, personalized introduction"""
        
        level_greeting = {
            0: "Welcome! I'm excited to help you showcase your potential.",
            1: "Great to meet you! Let's explore your coding skills together.",
            2: "Looking forward to our technical discussion today.",
            5: "I appreciate you taking the time. Let's dive into some interesting problems.",
            10: "Thanks for joining. I'm looking forward to a great technical discussion.",
        }
        
        for years, greeting in sorted(level_greeting.items(), reverse=True):
            if experience_years >= years:
                selected_greeting = greeting
                break
        
        return f"""
Hello {candidate_name}! 👋

{selected_greeting}

Today we'll be working on a coding challenge relevant to the **{target_role}** position.
{f"This role involves {company_context}." if company_context else ""}

**How this works:**
1. I'll present a problem and you can ask any clarifying questions
2. Think out loud as you work - I'm interested in your thought process
3. You can run your code anytime to test it
4. Feel free to ask for hints if you get stuck

There's no trick questions here - I'm genuinely here to help you succeed!

Ready when you are. 🚀
"""

    @kernel_function(
        description="Adapt interview pacing based on candidate performance",
        name="adapt_pacing"
    )
    def adapt_pacing(
        self,
        time_spent_minutes: Annotated[int, "Minutes spent so far"],
        tests_passed: Annotated[int, "Number of tests passed"],
        total_tests: Annotated[int, "Total number of tests"],
        hints_used: Annotated[int, "Number of hints used"]
    ) -> Annotated[str, "Recommendation for interview pacing"]:
        """Determine if pacing should be adjusted"""
        
        completion_pct = (tests_passed / total_tests * 100) if total_tests > 0 else 0
        
        # Fast solver
        if completion_pct == 100 and time_spent_minutes < 15:
            return "SPEED_UP: Candidate solved quickly. Move to follow-up questions or harder variation."
        
        # Struggling
        if time_spent_minutes > 20 and completion_pct < 50:
            if hints_used < 2:
                return "OFFER_HELP: Candidate may be stuck. Proactively offer a hint."
            else:
                return "SIMPLIFY: Consider simplifying the problem or focusing on partial solution."
        
        # On track
        if completion_pct > 50:
            return "ON_TRACK: Good progress. Let them continue."
        
        return "MONITOR: Continue observing. Check in after 5 more minutes."
