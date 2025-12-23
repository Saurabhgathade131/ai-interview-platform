"""
AI Interviewer Agent using Azure OpenAI
Provides contextual help, hints, and maintains conversation
"""
from typing import Dict, Any, List, AsyncGenerator
from datetime import datetime
from openai import AsyncAzureOpenAI, AsyncOpenAI
from app.config import settings

class InterviewerAgent:
    """
    AI Interviewer that helps candidates during coding interviews
    Uses Azure OpenAI or Standard OpenAI for natural language understanding
    """
    
    def __init__(self, session_id: str):
        self.session_id = session_id
        
        # Check if we should use Azure, Local LLM, or Standard OpenAI
        if settings.AZURE_OPENAI_API_KEY and settings.AZURE_OPENAI_ENDPOINT:
            print(" Using Azure OpenAI")
            self.client = AsyncAzureOpenAI(
                api_key=settings.AZURE_OPENAI_API_KEY,
                api_version=settings.AZURE_OPENAI_API_VERSION,
                azure_endpoint=settings.AZURE_OPENAI_ENDPOINT
            )
            self.deployment = settings.AZURE_OPENAI_DEPLOYMENT
            
        elif settings.USE_LOCAL_LLM:
            print(f" Using Local LLM (Ollama): {settings.OLLAMA_MODEL}")
            self.client = AsyncOpenAI(
                base_url=settings.OLLAMA_BASE_URL,
                api_key="ollama" # Required but ignored
            )
            self.deployment = settings.OLLAMA_MODEL
            
        else:
            print(" Using Standard OpenAI")
            if not settings.OPENAI_API_KEY:
                print("⚠️ WARNING: No OPENAI_API_KEY found in settings!")
                
            self.client = AsyncOpenAI(
                api_key=settings.OPENAI_API_KEY
            )
            # Use gpt-3.5-turbo (accessible to all)
            self.deployment = "gpt-3.5-turbo"
        
        # System prompt for the interviewer
        self.system_prompt = """You are a Senior Technical Interviewer and Subject Matter Expert (SME) conducting a live coding interview.

Your Goal: Assess the candidate's problem-solving skills while providing a supportive, interactive experience.

**Persona & Voice:**
- **Tone**: Professional, encouraging, conversational, and "Senior Engineer to Junior Engineer."
- **Speech-Friendly**: Write as if you are speaking. Use short sentences. Avoid long bulleted lists. Avoid reading out large blocks of code.
- **Interactive**: Ask follow-up questions. "Does that make sense?" or "How would you handle X?"

**Responsibilities:**
1. **Guide, Don't Solve**: If they are stuck, give a conceptual hint (e.g., "Have you considered using a hash map here?"). NEVER write the full solution.
2. **Deepen the Discussion**: If they solve it quickly, ask about time complexity, edge cases, or optimizations.
3. **Be Responsive**: Acknowledge their specific questions directy.
4. **Code Reviews**: When analyzing their code, point out best practices (naming, modularity) like a real mentor.

**Critical Rules for Voice Output:**
- Do NOT output long markdown lists.
- Do NOT read code character-by-character. Instead say: "I see your code using a loop..."
- Keep responses concise (1-3 sentences) when in a back-and-forth dialogue.
"""
    
    def _build_prompt(self, user_message: str, context: Dict[str, Any]) -> str:
        """Helper to construct the prompt with context"""
        prompt = f"Candidate says: {user_message}\n\nContext:\n"
        
        if context.get('current_code'):
            prompt += f"Current Code:\n```javascript\n{context['current_code']}\n```\n"
            
        if context.get('recent_errors'):
            prompt += f"Recent Execution Error: {context['recent_errors']}\n"
            
        if context.get('problem_title'):
             prompt = f"Current Problem: {context.get('problem_title')}\n" + prompt

        return prompt

    async def send_message_stream(self, user_message: str, context: Dict[str, Any]) -> AsyncGenerator[str, None]:
        """
        Send message to AI and yield streaming chunks
        """
        try:
            # Build context-aware prompt
            messages = [
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": self._build_prompt(user_message, context)}
            ]
            
            print(f"DEBUG: Streaming request to {self.deployment}...")
            stream = await self.client.chat.completions.create(
                model=self.deployment,
                messages=messages,
                temperature=0.7,
                max_completion_tokens=500,
                stream=True  # Enable streaming
            )
            
            async for chunk in stream:
                if chunk.choices and len(chunk.choices) > 0:
                    delta = chunk.choices[0].delta
                    if delta.content is not None:
                        yield delta.content
        except Exception as e:
            print(f"AI Stream Error ({type(e).__name__}): {str(e)}")
            # Fallback to Mock Response (sent as a single chunk)
            mock_resp = self._get_mock_response(user_message, context, error=str(e))
            yield mock_resp
            
            # Optional: Add small delay to simulate thinking if needed
            # import asyncio
            # await asyncio.sleep(0.5)

    async def send_message(self, user_message: str, context: Dict[str, Any]) -> str:
        """
        Send a message to the AI interviewer and get a full response
        Falls back to Mock AI if connection fails
        """
        try:
            messages = [
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": self._build_prompt(user_message, context)}
            ]
            
            response = await self.client.chat.completions.create(
                model=self.deployment,
                messages=messages,
                temperature=0.7,
                max_completion_tokens=500
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            print(f"AI Agent error: {str(e)}")
            # Graceful Fallback (Mock AI)
            return self._get_mock_response(user_message, context, error=str(e))

    def _get_mock_response(self, user_message: str, context: Dict[str, Any], error: str = "") -> str:
        """
        Provide a simulated response when AI is offline
        """
        msg = user_message.lower()
        
        # 1. Hint Request
        if "hint" in msg or "stuck" in msg or "help" in msg:
            if context.get('recent_errors'):
                return f"I see you're encountering an error: `{context['recent_errors']}`. \n\n**Hint:** Try checking your logic around that line. Usually, this happens when you access an index out of bounds or mistype a variable name."
            return "Sure! **Hint:** For the Two Sum problem, consider using a Hash Map (Object in JS) to store numbers you've already seen. This allows you to look up the complement in O(1) time."
            
        # 2. Solution/Code related
        if "solution" in msg or "code" in msg:
            return "I'd love to help, but I can't write the code for you! Try starting with a loop to iterate through the array. What would you do inside the loop?"
            
        # 3. Connection Error Explanation
        if "connection" in msg or "why" in msg:
            return f"I'm operating in **Offline Mode** right now because I couldn't connect to the AI model. \n*(Error: {error})*\n\nPlease make sure Ollama is running (`ollama run llama3.2`) or your API keys are set in `.env`."
            
        # 4. Default Chat functionality
        return "That's a great question. Since I'm currently running in **Offline Mode** (AI connection failed), I can only give basic hints. \n\nTry asking for a **hint** about the Two Sum problem!"
    
    async def proactive_hint(self, context: Dict[str, Any]) -> str:
        """
        Generate a proactive hint when the candidate is stuck
Provide a brief, helpful hint (2-3 sentences) that guides them toward fixing the issue WITHOUT giving away the solution. Focus on:
1. What might be causing the error
2. A general approach to fix it
3. Encouragement

Keep it concise and supportive!"""
        
        messages = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": hint_prompt}
        ]
        
        try:
            response = await self.client.chat.completions.create(
                model=self.deployment,
                messages=messages,
                temperature=0.7,
                max_completion_tokens=200
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            print(f"Hint generation error: {str(e)}")
            return "I notice you're encountering the same error repeatedly. Try reviewing your logic step by step, and consider testing with a simple example first. You're on the right track!"
    
    async def analyze_code(self, code: str, problem_id: str) -> Dict[str, Any]:
        """
        Analyze the final code submission for the report
3. **Code Quality Score**: Rate 1-10 based on readability, correctness, and efficiency
4. **Strengths**: 2-3 positive aspects of the solution
5. **Areas for Improvement**: 2-3 constructive suggestions

Format your response as JSON with keys: time_complexity, space_complexity, quality_score, strengths (array), improvements (array)"""
        
        messages = [
            {"role": "system", "content": "You are a technical interviewer analyzing code submissions."},
            {"role": "user", "content": analysis_prompt}
        ]
        
        try:
            response = await self.client.chat.completions.create(
                model=self.deployment,
                messages=messages,
                temperature=0.3,  # Lower temperature for more consistent analysis
                max_completion_tokens=600
            )
            
            # Try to parse JSON response
            import json
            content = response.choices[0].message.content
            
            # Extract JSON from markdown code blocks if present
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                content = content.split("```")[1].split("```")[0].strip()
            
            return json.loads(content)
            
        except Exception as e:
            print(f"Code analysis error: {str(e)}")
            # Return default analysis
            return {
                "time_complexity": "Unable to analyze",
                "space_complexity": "Unable to analyze",
                "quality_score": 5,
                "strengths": ["Code submitted"],
                "improvements": ["Analysis unavailable"]
            }
