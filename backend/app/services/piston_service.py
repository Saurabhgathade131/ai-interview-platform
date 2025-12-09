"""
Piston API service for executing code
Works on Windows - no cgroups needed!
"""
import aiohttp
import asyncio
from typing import Dict, Any
from app.models.session import CodeExecution

# Test cases for different problems
PROBLEM_TESTS = {
    "two-sum": """
const { twoSum } = require('./solution.js');

const testCases = [
    { nums: [2, 7, 11, 15], target: 9, expected: [0, 1] },
    { nums: [3, 2, 4], target: 6, expected: [1, 2] },
    { nums: [3, 3], target: 6, expected: [0, 1] },
    { nums: [1, 5, 3, 7, 9], target: 12, expected: [2, 4] },
    { nums: [-1, -2, -3, -4, -5], target: -8, expected: [2, 4] }
];

let passed = 0;
let failed = 0;

testCases.forEach((test, i) => {
    try {
        const result = twoSum(test.nums, test.target);
        
        const isCorrect = (
            result.length === 2 &&
            test.nums[result[0]] + test.nums[result[1]] === test.target &&
            result[0] !== result[1]
        );
        
        if (isCorrect) {
            console.log(`✓ Test ${i + 1} passed`);
            passed++;
        } else {
            console.error(`✗ Test ${i + 1} failed: Expected indices where nums[i] + nums[j] = ${test.target}, got [${result}]`);
            failed++;
        }
    } catch (error) {
        console.error(`✗ Test ${i + 1} failed with error: ${error.message}`);
        failed++;
    }
});

console.log(`\\n${passed}/${testCases.length} tests passed`);

if (failed > 0) {
    process.exit(1);
}
"""
}

class PistonService:
    """Service for executing code via Piston API"""
    
    def __init__(self, base_url: str = "http://localhost:2000"):
        self.base_url = base_url
    
    async def execute_code(self, source_code: str, problem_id: str) -> CodeExecution:
        """
        Execute JavaScript code with test cases using Piston
        """
        
        # Get test cases for the problem
        test_code = PROBLEM_TESTS.get(problem_id, "")
        
        if not test_code:
            return CodeExecution(
                status="error",
                stderr="No test cases found for this problem",
                test_passed=False,
                test_total=0
            )
        
        # Wrap source code with module.exports
        wrapped_code = f"{source_code}\\n\\nmodule.exports = {{ twoSum }};"
        
        # Prepare Piston request
        payload = {
            "language": "javascript",
            "version": "18.15.0",
            "files": [
                {
                    "name": "solution.js",
                    "content": wrapped_code
                },
                {
                    "name": "test.js",
                    "content": test_code
                }
            ],
            "stdin": "",
            "args": [],
            "compile_timeout": 10000,
            "run_timeout": 3000,
            "compile_memory_limit": -1,
            "run_memory_limit": -1
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.base_url}/api/v2/execute",
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as response:
                    
                    if response.status != 200:
                        error_text = await response.text()
                        return CodeExecution(
                            status="error",
                            stderr=f"Execution failed: {error_text}",
                            test_passed=False,
                            test_total=0
                        )
                    
                    result = await response.json()
                    
                    # Extract outputs
                    stdout = result.get("run", {}).get("stdout", "")
                    stderr = result.get("run", {}).get("stderr", "")
                    compile_output = result.get("compile", {}).get("output", "")
                    
                    # Parse test results
                    test_passed = False
                    test_total = 5
                    
                    if stdout:
                        # Count passed tests from output
                        lines = stdout.split('\\n')
                        for line in lines:
                            if '/' in line and 'tests passed' in line:
                                parts = line.split('/')
                                if len(parts) == 2:
                                    try:
                                        passed = int(parts[0].strip())
                                        total = int(parts[1].split()[0].strip())
                                        test_passed = (passed == total)
                                        test_total = total
                                    except:
                                        pass
                    
                    # Check exit code
                    exit_code = result.get("run", {}).get("code", 1)
                    if exit_code == 0:
                        test_passed = True
                    
                    return CodeExecution(
                        stdout=stdout,
                        stderr=stderr,
                        compile_output=compile_output,
                        status="Accepted" if exit_code == 0 else "Runtime Error",
                        time=None,
                        memory=None,
                        test_passed=test_passed,
                        test_total=test_total
                    )
                    
        except asyncio.TimeoutError:
            return CodeExecution(
                status="timeout",
                stderr="Execution timed out after 30 seconds",
                test_passed=False,
                test_total=0
            )
        except Exception as e:
            print(f"Piston execution error: {str(e)}")
            return CodeExecution(
                status="error",
                stderr=f"Execution error: {str(e)}",
                test_passed=False,
                test_total=0
            )
