"""
Simple Node.js execution service using subprocess
WORKS ON WINDOWS - No Docker needed!
"""
import asyncio
import sys
import os
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

class SimpleNodeService:
    """Execute JavaScript using local Node.js - Works on Windows!"""
    
    async def execute_code(self, source_code: str, problem_id: str) -> CodeExecution:
        """
        Execute JavaScript code with test cases using local Node.js
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
        
        try:
            # Create temp directory for this execution
            import tempfile
            import time
            
            with tempfile.TemporaryDirectory() as tmpdir:
                # Write files
                solution_path = os.path.join(tmpdir, "solution.js")
                test_path = os.path.join(tmpdir, "test.js")
                
                with open(solution_path, 'w', encoding='utf-8') as f:
                    f.write(wrapped_code)
                
                with open(test_path, 'w', encoding='utf-8') as f:
                    f.write(test_code)
                
                # Execute with Node.js
                start_time = time.time()
                
                process = await asyncio.create_subprocess_exec(
                    'node', test_path,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                    cwd=tmpdir
                )
                
                try:
                    stdout, stderr = await asyncio.wait_for(
                        process.communicate(), 
                        timeout=5.0
                    )
                    execution_time = time.time() - start_time
                    
                    stdout_text = stdout.decode('utf-8', errors='ignore')
                    stderr_text = stderr.decode('utf-8', errors='ignore')
                    
                    # Parse test results
                    test_passed = False
                    test_total = 5
                    
                    if stdout_text:
                        lines = stdout_text.split('\\n')
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
                    if process.returncode == 0:
                        test_passed = True
                    
                    return CodeExecution(
                        stdout=stdout_text,
                        stderr=stderr_text,
                        compile_output="",
                        status="Accepted" if process.returncode == 0 else "Runtime Error",
                        time=round(execution_time, 2),
                        memory=None,
                        test_passed=test_passed,
                        test_total=test_total
                    )
                    
                except asyncio.TimeoutError:
                    process.kill()
                    return CodeExecution(
                        status="timeout",
                        stderr="Execution timed out after 5 seconds",
                        test_passed=False,
                        test_total=0
                    )
                    
        except FileNotFoundError:
            return CodeExecution(
                status="error",
                stderr="Node.js is not installed. Please install Node.js from nodejs.org",
                test_passed=False,
                test_total=0
            )
        except Exception as e:
            print(f"Simple Node execution error: {str(e)}")
            return CodeExecution(
                status="error",
                stderr=f"Execution error: {str(e)}",
                test_passed=False,
                test_total=0
            )
