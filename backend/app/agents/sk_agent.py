"""
Microsoft Semantic Kernel Agent Implementation (v2.0)
Full Agentic AI Interviewer with multiple plugins for intelligent, proactive behavior.
"""
import logging
from typing import Dict, Any, Optional
import semantic_kernel as sk
from semantic_kernel.connectors.ai.open_ai import AzureChatCompletion, OpenAIChatCompletion
from semantic_kernel.contents.chat_history import ChatHistory
from semantic_kernel.functions import KernelArguments
from semantic_kernel.connectors.ai.open_ai.prompt_execution_settings.azure_chat_prompt_execution_settings import AzureChatPromptExecutionSettings
from app.config import settings

# Import all plugins
from app.agents.plugins.interview_plugin import InterviewerPlugin
from app.agents.plugins.code_analysis_plugin import CodeAnalysisPlugin
from app.agents.plugins.hint_and_test_plugin import HintStrategyPlugin, TestGenerationPlugin
from app.agents.plugins.evaluation_plugin import EvaluationPlugin
from app.agents.plugins.problem_generator_plugin import ProblemGeneratorPlugin, InterviewCustomizerPlugin
from app.agents.plugins.code_validator_plugin import CodeValidatorPlugin


class SemanticKernelInterviewerAgent:
    """
    Advanced Agentic AI Interviewer powered by Microsoft Semantic Kernel.
    
    Features:
    - Multi-plugin architecture for specialized capabilities
    - Auto function calling for intelligent tool selection
    - Persistent chat history per session
    - Proactive behavior detection
    """
    
    # Class-level storage for session histories
    _session_histories: Dict[str, ChatHistory] = {}
    
    def __init__(self, session_id: str):
        self.session_id = session_id
        self.kernel = sk.Kernel()
        self.service_id = "azure-openai"
        
        # Setup logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)

        # 1. Configure AI Service
        self._configure_service()

        # 2. Register ALL Plugins for full agentic capabilities
        self._register_plugins()

        # 3. Define Enhanced Persona
        self.system_prompt = """You are a **Proactive Senior Technical Interviewer** conducting a live coding interview.

**Your Tools & Capabilities:**
You have access to the following specialized tools - USE THEM when appropriate:

1. **CodeAnalysis** - Analyze code structure, complexity, and edge cases
   - `analyze_code_structure` - Review code patterns and potential issues
   - `estimate_complexity` - Calculate Big-O time/space complexity
   - `check_edge_cases` - Identify missing edge case handling

2. **Hints** - Progressive hint system (4 levels)
   - `get_progressive_hint` - Provide appropriate hints without giving solutions
   - `assess_hint_level` - Determine how much help the candidate needs
   - `generate_encouragement` - Keep the candidate motivated

3. **TestGenerator** - Challenge the candidate
   - `generate_challenge_test` - Create edge case tests
   - `suggest_next_test` - Guide testing progression

4. **Evaluation** - Real-time scoring
   - `calculate_score` - Multi-dimensional scoring
   - `generate_feedback` - Constructive feedback

**Behavior Rules:**
1. BE PROACTIVE - If the candidate is silent for 30+ seconds, engage them
2. NEVER give full solutions - Guide with hints and questions
3. ANALYZE CODE when asked about it - Use your CodeAnalysis tools
4. SPEAK NATURALLY - As if on a video call (concise, conversational)
5. CHALLENGE when appropriate - Push for optimization and edge cases
6. ENCOURAGE progress - Celebrate small wins

**Response Style:**
- Keep responses concise (2-4 sentences for most replies)
- Use code snippets sparingly - prefer conceptual guidance
- Ask follow-up questions to understand their thinking
- Be warm but professional
"""

        # 4. Initialize or retrieve session history
        self._init_session_history()

    def _configure_service(self):
        """Configure Azure OpenAI service"""
        if settings.AZURE_OPENAI_API_KEY and settings.AZURE_OPENAI_ENDPOINT:
            self.logger.info(f"[{self.session_id}] Initializing Azure OpenAI (Deployment: {settings.AZURE_OPENAI_DEPLOYMENT})")
            service = AzureChatCompletion(
                service_id=self.service_id,
                deployment_name=settings.AZURE_OPENAI_DEPLOYMENT,
                endpoint=settings.AZURE_OPENAI_ENDPOINT,
                api_key=settings.AZURE_OPENAI_API_KEY,
                api_version=settings.AZURE_OPENAI_API_VERSION
            )
        else:
            self.logger.warning(f"[{self.session_id}] No Azure credentials - using Standard OpenAI fallback")
            service = OpenAIChatCompletion(
                service_id=self.service_id,
                ai_model_id="gpt-4",
                api_key=settings.OPENAI_API_KEY or "invalid-key",
            )
        
        self.kernel.add_service(service)

    def _register_plugins(self):
        """Register all agent plugins"""
        # Core interviewer tools
        self.kernel.add_plugin(InterviewerPlugin(), plugin_name="Interviewer")
        
        # Advanced code analysis
        self.kernel.add_plugin(CodeAnalysisPlugin(), plugin_name="CodeAnalysis")
        
        # Progressive hints
        self.kernel.add_plugin(HintStrategyPlugin(), plugin_name="Hints")
        
        # Test generation
        self.kernel.add_plugin(TestGenerationPlugin(), plugin_name="TestGenerator")
        
        # Evaluation & scoring
        self.kernel.add_plugin(EvaluationPlugin(), plugin_name="Evaluation")
        
        # Dynamic problem generation
        self.kernel.add_plugin(ProblemGeneratorPlugin(), plugin_name="ProblemGenerator")
        
        # Interview customization
        self.kernel.add_plugin(InterviewCustomizerPlugin(), plugin_name="InterviewCustomizer")
        
        # Code validation and silent checking
        self.kernel.add_plugin(CodeValidatorPlugin(), plugin_name="CodeValidator")
        
        self.logger.info(f"[{self.session_id}] Registered 8 plugins with {len(list(self.kernel.plugins))} total functions")

    def _init_session_history(self):
        """Initialize or retrieve persistent chat history for this session"""
        if self.session_id not in self._session_histories:
            self._session_histories[self.session_id] = ChatHistory(system_message=self.system_prompt)
            self.logger.info(f"[{self.session_id}] Created new chat history")
        
        self.chat_history = self._session_histories[self.session_id]

    def _build_context_message(self, context: Dict[str, Any]) -> str:
        """Build context string for the AI"""
        return f"""
[Current Interview Context]
- Problem: {context.get('problem_title', 'Unknown')}
- Tests Passed: {context.get('tests_passed', 0)}/{context.get('total_tests', 0)}
- Time Spent: {context.get('time_spent_minutes', 0)} minutes
- Hints Given: {context.get('hints_given', 0)}
- Last Error: {context.get('recent_errors', 'None')}

Current Code:
```javascript
{context.get('current_code', '// No code yet')}
```
"""

    async def send_message(self, user_message: str, context: Dict[str, Any]) -> str:
        """
        Send a message using Semantic Kernel with auto-function calling.
        The AI can automatically invoke plugins based on the conversation.
        """
        try:
            # Create execution settings with auto function calling
            # Note: Use max_completion_tokens for newer Azure OpenAI models
            execution_settings = AzureChatPromptExecutionSettings(
                tool_choice="auto",  # Let the AI decide which tools to use
                temperature=0.7,
                max_completion_tokens=500
            )
            
            # Add context as a system message (updated each turn)
            context_msg = self._build_context_message(context)
            
            # Create a fresh history for this call with context
            call_history = ChatHistory(system_message=self.system_prompt)
            call_history.add_system_message(context_msg)
            
            # Add recent conversation history (last 10 messages)
            for msg in self.chat_history.messages[-10:]:
                if msg.role.value == "user":
                    call_history.add_user_message(str(msg.content))
                elif msg.role.value == "assistant":
                    call_history.add_assistant_message(str(msg.content))
            
            # Add current user message
            call_history.add_user_message(user_message)
            
            # Get chat completion with auto function calling
            chat_service = self.kernel.get_service(service_id=self.service_id)
            
            result = await chat_service.get_chat_message_content(
                chat_history=call_history,
                settings=execution_settings,
                kernel=self.kernel
            )
            
            response = str(result)
            
            # Persist to session history
            self.chat_history.add_user_message(user_message)
            self.chat_history.add_assistant_message(response)
            
            self.logger.info(f"[{self.session_id}] Response generated ({len(response)} chars)")
            return response

        except Exception as e:
            self.logger.error(f"[{self.session_id}] Semantic Kernel Error: {e}")
            
            if "401" in str(e) or "Access Denied" in str(e) or "Unauthorized" in str(e):
                return "⚠️ Configuration Error: Unable to authenticate with Azure OpenAI. Please check your API keys."
            
            if "404" in str(e) or "not found" in str(e).lower():
                return f"⚠️ Deployment '{settings.AZURE_OPENAI_DEPLOYMENT}' not found. Please verify your deployment name."
            
            return f"I'm experiencing a technical issue. Let me try again. ({type(e).__name__})"

    async def analyze_code(self, code: str, context: Dict[str, Any]) -> str:
        """
        Trigger a proactive code analysis.
        Called by the system when it detects the candidate might need guidance.
        """
        analysis_prompt = f"""
The candidate has written the following code. Please analyze it using your CodeAnalysis tools 
and provide constructive feedback. Focus on:
1. What they're doing well
2. Any potential issues
3. Suggestions for improvement (without giving the solution)

Code:
```javascript
{code}
```
"""
        return await self.send_message(analysis_prompt, context)

    async def generate_proactive_prompt(self, context: Dict[str, Any]) -> Optional[str]:
        """
        Generate a proactive message when the candidate seems stuck.
        Returns None if no proactive message is needed.
        """
        consecutive_errors = context.get('consecutive_errors', 0)
        idle_seconds = context.get('idle_seconds', 0)
        
        if consecutive_errors >= 3:
            return await self.send_message(
                "[SYSTEM: Candidate has 3+ consecutive errors. Offer help proactively.]",
                context
            )
        
        if idle_seconds >= 120:  # 2 minutes idle
            return await self.send_message(
                "[SYSTEM: Candidate has been idle for 2+ minutes. Check if they need guidance.]",
                context
            )
        
        return None

    def get_session_stats(self) -> Dict[str, Any]:
        """Get statistics about the current session"""
        return {
            "session_id": self.session_id,
            "message_count": len(self.chat_history.messages),
            "plugins_registered": len(list(self.kernel.plugins))
        }

