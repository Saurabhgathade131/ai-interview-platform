"""
Dynamic Problem Generation Service
Generates coding problems and test cases based on candidate experience using AI
"""
import random
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from app.config import settings


@dataclass
class CodingProblem:
    """Represents a coding problem with test cases"""
    problem_id: str
    title: str
    description: str
    difficulty: str
    initial_code: str
    test_cases: List[Dict[str, Any]]
    examples: List[Dict[str, Any]]
    constraints: List[str]
    hints: List[str]


# Problem templates that can be customized by AI
PROBLEM_TEMPLATES = {
    "two-sum": CodingProblem(
        problem_id="two-sum",
        title="Two Sum",
        difficulty="easy",
        description="Given an array of integers and a target, return indices of two numbers that add up to the target.",
        initial_code="""// Given an array of integers and a target sum,
// return the indices of two numbers that add up to the target.

function twoSum(nums, target) {
    // Your code here
    
}
""",
        test_cases=[
            {"input": {"nums": [2, 7, 11, 15], "target": 9}, "expected": [0, 1]},
            {"input": {"nums": [3, 2, 4], "target": 6}, "expected": [1, 2]},
            {"input": {"nums": [3, 3], "target": 6}, "expected": [0, 1]},
            {"input": {"nums": [1, 5, 3, 7], "target": 12}, "expected": [2, 3]},
            {"input": {"nums": [-1, -2, -3, -4], "target": -6}, "expected": [1, 3]},
        ],
        examples=[
            {"input": "nums = [2, 7, 11, 15], target = 9", "output": "[0, 1]", "explanation": "nums[0] + nums[1] = 2 + 7 = 9"},
        ],
        constraints=["Each input has exactly one solution", "You cannot use the same element twice"],
        hints=["Think about what data structure can help you find a number quickly", "A hash map has O(1) lookup time"]
    ),
    "reverse-string": CodingProblem(
        problem_id="reverse-string",
        title="Reverse String",
        difficulty="easy",
        description="Write a function that reverses a string in-place.",
        initial_code="""// Reverse the input string in-place.
// The input is given as an array of characters.

function reverseString(s) {
    // Your code here
    
}
""",
        test_cases=[
            {"input": {"s": ["h", "e", "l", "l", "o"]}, "expected": ["o", "l", "l", "e", "h"]},
            {"input": {"s": ["H", "a", "n", "n", "a", "h"]}, "expected": ["h", "a", "n", "n", "a", "H"]},
            {"input": {"s": ["a"]}, "expected": ["a"]},
            {"input": {"s": ["a", "b"]}, "expected": ["b", "a"]},
        ],
        examples=[
            {"input": 's = ["h","e","l","l","o"]', "output": '["o","l","l","e","h"]', "explanation": "Reverse the characters"},
        ],
        constraints=["Do it in-place with O(1) extra memory"],
        hints=["Use two pointers, one at start and one at end", "Swap characters and move pointers towards center"]
    ),
    "valid-palindrome": CodingProblem(
        problem_id="valid-palindrome",
        title="Valid Palindrome",
        difficulty="easy",
        description="Determine if a string is a palindrome, considering only alphanumeric characters and ignoring cases.",
        initial_code="""// Check if the input string is a valid palindrome.
// Consider only alphanumeric characters and ignore case.

function isPalindrome(s) {
    // Your code here
    
}
""",
        test_cases=[
            {"input": {"s": "A man, a plan, a canal: Panama"}, "expected": True},
            {"input": {"s": "race a car"}, "expected": False},
            {"input": {"s": " "}, "expected": True},
            {"input": {"s": "ab_a"}, "expected": True},
        ],
        examples=[
            {"input": 's = "A man, a plan, a canal: Panama"', "output": "true", "explanation": "After removing non-alphanumeric and lowercasing: 'amanaplanacanalpanama' is a palindrome"},
        ],
        constraints=["Only consider alphanumeric characters", "Ignore letter case"],
        hints=["First clean the string by removing non-alphanumeric characters", "Compare characters from both ends"]
    ),
    "maximum-subarray": CodingProblem(
        problem_id="maximum-subarray",
        title="Maximum Subarray",
        difficulty="medium",
        description="Find the contiguous subarray with the largest sum and return the sum.",
        initial_code="""// Find the contiguous subarray with the largest sum.
// Return the maximum sum.

function maxSubArray(nums) {
    // Your code here
    
}
""",
        test_cases=[
            {"input": {"nums": [-2, 1, -3, 4, -1, 2, 1, -5, 4]}, "expected": 6},
            {"input": {"nums": [1]}, "expected": 1},
            {"input": {"nums": [5, 4, -1, 7, 8]}, "expected": 23},
            {"input": {"nums": [-1]}, "expected": -1},
            {"input": {"nums": [-2, -1]}, "expected": -1},
        ],
        examples=[
            {"input": "nums = [-2,1,-3,4,-1,2,1,-5,4]", "output": "6", "explanation": "The subarray [4,-1,2,1] has the largest sum = 6"},
        ],
        constraints=["Array has at least one element"],
        hints=["Think about Kadane's algorithm", "Track current sum and max sum seen so far"]
    ),
    "merge-sorted-arrays": CodingProblem(
        problem_id="merge-sorted-arrays",
        title="Merge Sorted Arrays",
        difficulty="easy",
        description="Merge two sorted arrays into one sorted array.",
        initial_code="""// Merge two sorted arrays nums1 and nums2.
// nums1 has enough space at the end to hold nums2.
// m and n are the number of elements in nums1 and nums2.

function merge(nums1, m, nums2, n) {
    // Your code here - modify nums1 in-place
    
}
""",
        test_cases=[
            {"input": {"nums1": [1, 2, 3, 0, 0, 0], "m": 3, "nums2": [2, 5, 6], "n": 3}, "expected": [1, 2, 2, 3, 5, 6]},
            {"input": {"nums1": [1], "m": 1, "nums2": [], "n": 0}, "expected": [1]},
            {"input": {"nums1": [0], "m": 0, "nums2": [1], "n": 1}, "expected": [1]},
        ],
        examples=[
            {"input": "nums1 = [1,2,3,0,0,0], m = 3, nums2 = [2,5,6], n = 3", "output": "[1,2,2,3,5,6]", "explanation": "Merge and sort"},
        ],
        constraints=["nums1 length = m + n", "Modify nums1 in-place"],
        hints=["Start from the end of both arrays", "Fill nums1 from the back"]
    ),
}

# Difficulty levels mapped to experience
DIFFICULTY_BY_EXPERIENCE = {
    "junior": ["easy"],
    "mid": ["easy", "medium"],
    "senior": ["medium", "hard"],
}


class ProblemService:
    """Service for generating and managing coding problems"""
    
    def __init__(self):
        self.problems = PROBLEM_TEMPLATES
    
    def get_problem(self, problem_id: str) -> Optional[CodingProblem]:
        """Get a specific problem by ID"""
        return self.problems.get(problem_id)
    
    def get_random_problem(self, experience_years: int = 0, focus_area: str = "") -> CodingProblem:
        """Get a random problem appropriate for the experience level"""
        
        # Determine difficulty level
        if experience_years <= 2:
            level = "junior"
        elif experience_years <= 5:
            level = "mid"
        else:
            level = "senior"
        
        allowed_difficulties = DIFFICULTY_BY_EXPERIENCE.get(level, ["easy"])
        
        # Filter problems by difficulty
        eligible_problems = [
            p for p in self.problems.values()
            if p.difficulty in allowed_difficulties
        ]
        
        if not eligible_problems:
            eligible_problems = list(self.problems.values())
        
        return random.choice(eligible_problems)
    
    def format_problem_for_chat(self, problem: CodingProblem, candidate_name: str = "Candidate") -> str:
        """Format a problem description for the chat welcome message"""
        
        examples_text = "\n".join([
            f"- Input: {ex['input']}\n  Output: {ex['output']}\n  ({ex['explanation']})"
            for ex in problem.examples
        ])
        
        constraints_text = "\n".join([f"- {c}" for c in problem.constraints])
        
        return f"""Hello {candidate_name}! 👋

Welcome to your technical interview! I'm your AI Interviewer today, powered by advanced AI technology. I'm here to assess your problem-solving skills and help guide you through this coding challenge.

Before we begin with the coding problem, I'd love to hear a bit about yourself. **Please take a moment to introduce yourself** - your background, experience, and what you're excited about in software development. You can speak or type your response.

---

Once you're ready, here's your coding challenge:

**{problem.title}** ({problem.difficulty.capitalize()})

{problem.description}

**Examples:**
{examples_text}

**Constraints:**
{constraints_text}

Feel free to ask me any clarifying questions! When you're ready, write your solution in the editor and click "Run Code" to test it.

Good luck! 🚀"""

    def generate_test_code(self, problem: CodingProblem) -> str:
        """Generate JavaScript test code for Judge0 execution"""
        
        # Problem-specific test code generators
        if problem.problem_id == "two-sum":
            return self._generate_two_sum_tests(problem)
        elif problem.problem_id == "reverse-string":
            return self._generate_reverse_string_tests(problem)
        elif problem.problem_id == "valid-palindrome":
            return self._generate_palindrome_tests(problem)
        elif problem.problem_id == "maximum-subarray":
            return self._generate_max_subarray_tests(problem)
        elif problem.problem_id == "merge-sorted-arrays":
            return self._generate_merge_arrays_tests(problem)
        
        return ""
    
    def _generate_two_sum_tests(self, problem: CodingProblem) -> str:
        return """const { twoSum } = require('./solution.js');

const testCases = [
    { nums: [2, 7, 11, 15], target: 9 },
    { nums: [3, 2, 4], target: 6 },
    { nums: [3, 3], target: 6 },
    { nums: [1, 5, 3, 7], target: 12 },
    { nums: [-1, -2, -3, -4], target: -6 }
];

let passed = 0;
let failed = 0;

testCases.forEach((test, i) => {
    try {
        const result = twoSum(test.nums, test.target);
        const isCorrect = (
            Array.isArray(result) &&
            result.length === 2 &&
            test.nums[result[0]] + test.nums[result[1]] === test.target &&
            result[0] !== result[1]
        );
        
        if (isCorrect) {
            console.log(`✓ Test ${i + 1} passed`);
            passed++;
        } else {
            console.error(`✗ Test ${i + 1} failed: got [${result}]`);
            failed++;
        }
    } catch (error) {
        console.error(`✗ Test ${i + 1} failed: ${error.message}`);
        failed++;
    }
});

console.log(`\\n${passed}/${testCases.length} tests passed`);
if (failed > 0) process.exit(1);
"""
    
    def _generate_reverse_string_tests(self, problem: CodingProblem) -> str:
        return """const { reverseString } = require('./solution.js');

const testCases = [
    { input: ["h", "e", "l", "l", "o"], expected: ["o", "l", "l", "e", "h"] },
    { input: ["H", "a", "n", "n", "a", "h"], expected: ["h", "a", "n", "n", "a", "H"] },
    { input: ["a"], expected: ["a"] },
    { input: ["a", "b"], expected: ["b", "a"] }
];

let passed = 0;
let failed = 0;

testCases.forEach((test, i) => {
    try {
        const arr = [...test.input];
        reverseString(arr);
        const isCorrect = JSON.stringify(arr) === JSON.stringify(test.expected);
        
        if (isCorrect) {
            console.log(`✓ Test ${i + 1} passed`);
            passed++;
        } else {
            console.error(`✗ Test ${i + 1} failed: expected ${JSON.stringify(test.expected)}, got ${JSON.stringify(arr)}`);
            failed++;
        }
    } catch (error) {
        console.error(`✗ Test ${i + 1} failed: ${error.message}`);
        failed++;
    }
});

console.log(`\\n${passed}/${testCases.length} tests passed`);
if (failed > 0) process.exit(1);
"""
    
    def _generate_palindrome_tests(self, problem: CodingProblem) -> str:
        return """const { isPalindrome } = require('./solution.js');

const testCases = [
    { input: "A man, a plan, a canal: Panama", expected: true },
    { input: "race a car", expected: false },
    { input: " ", expected: true },
    { input: "ab_a", expected: true }
];

let passed = 0;
let failed = 0;

testCases.forEach((test, i) => {
    try {
        const result = isPalindrome(test.input);
        const isCorrect = result === test.expected;
        
        if (isCorrect) {
            console.log(`✓ Test ${i + 1} passed`);
            passed++;
        } else {
            console.error(`✗ Test ${i + 1} failed: expected ${test.expected}, got ${result}`);
            failed++;
        }
    } catch (error) {
        console.error(`✗ Test ${i + 1} failed: ${error.message}`);
        failed++;
    }
});

console.log(`\\n${passed}/${testCases.length} tests passed`);
if (failed > 0) process.exit(1);
"""
    
    def _generate_max_subarray_tests(self, problem: CodingProblem) -> str:
        return """const { maxSubArray } = require('./solution.js');

const testCases = [
    { nums: [-2, 1, -3, 4, -1, 2, 1, -5, 4], expected: 6 },
    { nums: [1], expected: 1 },
    { nums: [5, 4, -1, 7, 8], expected: 23 },
    { nums: [-1], expected: -1 },
    { nums: [-2, -1], expected: -1 }
];

let passed = 0;
let failed = 0;

testCases.forEach((test, i) => {
    try {
        const result = maxSubArray(test.nums);
        const isCorrect = result === test.expected;
        
        if (isCorrect) {
            console.log(`✓ Test ${i + 1} passed`);
            passed++;
        } else {
            console.error(`✗ Test ${i + 1} failed: expected ${test.expected}, got ${result}`);
            failed++;
        }
    } catch (error) {
        console.error(`✗ Test ${i + 1} failed: ${error.message}`);
        failed++;
    }
});

console.log(`\\n${passed}/${testCases.length} tests passed`);
if (failed > 0) process.exit(1);
"""
    
    def _generate_merge_arrays_tests(self, problem: CodingProblem) -> str:
        return """const { merge } = require('./solution.js');

const testCases = [
    { nums1: [1, 2, 3, 0, 0, 0], m: 3, nums2: [2, 5, 6], n: 3, expected: [1, 2, 2, 3, 5, 6] },
    { nums1: [1], m: 1, nums2: [], n: 0, expected: [1] },
    { nums1: [0], m: 0, nums2: [1], n: 1, expected: [1] }
];

let passed = 0;
let failed = 0;

testCases.forEach((test, i) => {
    try {
        const arr = [...test.nums1];
        merge(arr, test.m, test.nums2, test.n);
        const isCorrect = JSON.stringify(arr) === JSON.stringify(test.expected);
        
        if (isCorrect) {
            console.log(`✓ Test ${i + 1} passed`);
            passed++;
        } else {
            console.error(`✗ Test ${i + 1} failed: expected ${JSON.stringify(test.expected)}, got ${JSON.stringify(arr)}`);
            failed++;
        }
    } catch (error) {
        console.error(`✗ Test ${i + 1} failed: ${error.message}`);
        failed++;
    }
});

console.log(`\\n${passed}/${testCases.length} tests passed`);
if (failed > 0) process.exit(1);
"""

    def _format_js_value(self, value: Any) -> str:
        """Format a Python value as JavaScript"""
        import json
        if isinstance(value, bool):
            return "true" if value else "false"
        return json.dumps(value)


# Singleton instance
_problem_service: Optional[ProblemService] = None

def get_problem_service() -> ProblemService:
    """Get or create the ProblemService singleton"""
    global _problem_service
    if _problem_service is None:
        _problem_service = ProblemService()
    return _problem_service
