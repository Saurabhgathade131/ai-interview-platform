"""
Judge0 service for executing JavaScript code
Handles submission, polling, and result parsing
"""
import aiohttp
import asyncio
import base64
from typing import Dict, Any
from app.config import settings
from app.models.session import CodeExecution


class Judge0Service:
    """Service for executing code via Judge0 API"""
    
    def __init__(self):
        self.base_url = settings.JUDGE0_ENDPOINT
        self.api_key = settings.JUDGE0_API_KEY
        
        self.headers = {
            "content-type": "application/json"
        }
        
        # Only add RapidAPI headers if using the cloud version
        if self.api_key:
            self.headers["X-RapidAPI-Key"] = self.api_key
            self.headers["X-RapidAPI-Host"] = "judge0-ce.p.rapidapi.com"
    
    def _get_test_code_for_problem(self, problem_id: str) -> str:
        """Get test code for a problem from the problem service"""
        from app.services.problem_service import get_problem_service
        
        problem_service = get_problem_service()
        problem = problem_service.get_problem(problem_id)
        
        if problem:
            return problem_service.generate_test_code(problem)
        
        return ""
    
    def _get_export_name(self, problem_id: str) -> str:
        """Get the function name to export based on problem ID"""
        export_names = {
            "two-sum": "twoSum",
            "reverse-string": "reverseString",
            "valid-palindrome": "isPalindrome",
            "maximum-subarray": "maxSubArray",
            "merge-sorted-arrays": "merge",
        }
        return export_names.get(problem_id, problem_id.replace("-", ""))
    
    async def execute_code(self, source_code: str, problem_id: str) -> CodeExecution:
        """
        Execute JavaScript code with test cases
        
        Args:
            source_code: The candidate's solution code
            problem_id: Problem identifier to get test cases
            
        Returns:
            CodeExecution model with results
        """
        
        # Get test cases dynamically from problem service
        test_code = self._get_test_code_for_problem(problem_id)
        
        if not test_code:
            return CodeExecution(
                status="error",
                stderr=f"No test cases found for problem: {problem_id}",
                test_passed=False,
                test_total=0
            )
        
        # Get the correct export name for this problem
        export_name = self._get_export_name(problem_id)
        
        # Combine solution code with test code
        # Remove the require statement from test code since we're combining them
        test_code_inline = test_code.replace(f"const {{ {export_name} }} = require('./solution.js');", "")
        
        # Create full code: solution + test
        full_code = f"""// Solution
{source_code}

// Tests
{test_code_inline}
"""
        
        # Prepare submission - combine everything into source_code
        submission_data = {
            "language_id": 63,  # JavaScript (Node.js)
            "source_code": base64.b64encode(full_code.encode()).decode(),
            "stdin": "",
            "expected_output": ""
        }
        
        last_error = None
        # Aggressive retry: 10 attempts (wait up to 15s total)
        for attempt in range(10):
            try:
                async with aiohttp.ClientSession() as session:
                    # Submit code
                    if attempt > 0:
                        print(f"Submitting to: {self.base_url}/submissions (Attempt {attempt+1})")
                        
                    async with session.post(
                        f"{self.base_url}/submissions",
                        json=submission_data,
                        headers=self.headers,
                        params={"base64_encoded": "true", "wait": "false"},
                        ssl=False
                    ) as response:
                        
                        if response.status != 201:
                            error_text = await response.text()
                            # If it's a 500/502/503/504, retry
                            if response.status >= 500:
                                last_error = f"Server Error {response.status}: {error_text}"
                                await asyncio.sleep(1.5) # Wait longer
                                continue
                                
                            return CodeExecution(
                                status="error",
                                stderr=f"Submission failed: {error_text}",
                                test_passed=False,
                                test_total=0
                            )
                        
                        result = await response.json()
                        token = result.get("token")
                    
                    # Poll for result (if submission succeeded)
                    if token:
                        return await self._poll_result(session, token)
                        
            except (aiohttp.ClientConnectorError, aiohttp.ServerDisconnectedError, aiohttp.ClientOSError, aiohttp.ClientPayloadError) as e:
                print(f"Connection error to Judge0 on submit: {e}")
                last_error = str(e)
                await asyncio.sleep(2) # Wait 2s for server restart
                continue
            except Exception as e:
                return CodeExecution(
                    status="error",
                    stderr=f"Execution error: {str(e)}",
                    test_passed=False,
                    test_total=0
                )
                
        # If all retries failed
        return CodeExecution(
            status="error",
            stderr=f"Execution error: Failed to connect to execution server after 10 attempts (Server unstable). ({last_error})",
            test_passed=False,
            test_total=0
        )
    
    async def _poll_result(self, session: aiohttp.ClientSession, token: str, max_attempts: int = 30) -> CodeExecution:
        """
        Poll Judge0 for execution result
        
        Args:
            session: aiohttp session
            token: Submission token
            max_attempts: Maximum polling attempts (30 = 30 seconds)
            
        Returns:
            CodeExecution model
        """
        
        # Adaptive polling (Backoff strategy)
        # Start fast, then slow down to save resources
        wait_times = [0.25, 0.25, 0.5, 0.5, 1.0, 1.0, 2.0, 2.0] # ... and then 2.0s constant
        
        for attempt in range(max_attempts):
            # Determine wait time
            wait = wait_times[attempt] if attempt < len(wait_times) else 2.0
            await asyncio.sleep(wait)
            
            try:
                async with session.get(
                    f"{self.base_url}/submissions/{token}",
                    headers=self.headers,
                    params={"base64_encoded": "true"},
                    ssl=False
                ) as response:
                    
                    if response.status != 200:
                        continue
                    
                    result = await response.json()
                    status_id = result.get("status", {}).get("id")
                    
                    # Status 1 = In Queue, 2 = Processing
                    if status_id in [1, 2]:
                        continue
                    
                    # Decode outputs
                    stdout = self._decode_base64(result.get("stdout"))
                    stderr = self._decode_base64(result.get("stderr"))
                    compile_output = self._decode_base64(result.get("compile_output"))
                    
                    # Parse test results
                    test_passed = False
                    test_total = 0
                    
                    if stdout:
                        # Count passed tests from output
                        lines = stdout.split('\n')
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
                    if status_id == 3:  # Accepted
                        test_passed = True
                    
                    return CodeExecution(
                        stdout=stdout,
                        stderr=stderr,
                        compile_output=compile_output,
                        status=result.get("status", {}).get("description", "Unknown"),
                        time=result.get("time"),
                        memory=result.get("memory"),
                        test_passed=test_passed and status_id == 3,
                        test_total=test_total if test_total > 0 else 5
                    )
            
            except (aiohttp.ClientConnectorError, aiohttp.ServerDisconnectedError) as e:
                # Catch specific connection errors to retry safely
                print(f"Connection error to Judge0 (attempt {attempt+1}): {e}")
                continue
            except Exception as e:
                print(f"Polling error: {str(e)}")
                continue
        
        # Timeout
        return CodeExecution(
            status="timeout",
            stderr="Execution timed out after 30 seconds",
            test_passed=False,
            test_total=0
        )
    
    def _decode_base64(self, encoded: str) -> str:
        """Decode base64 string"""
        if not encoded:
            return ""
        try:
            return base64.b64decode(encoded).decode('utf-8')
        except:
            return encoded
