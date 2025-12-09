"""
Microsoft Semantic Kernel Agent Implementation
Integrates with Azure OpenAI to provide an intelligent interviewer persona.
"""
import asyncio
from typing import Dict, Any, AsyncGenerator
import semantic_kernel as sk
from semantic_kernel.connectors.ai.open_ai import AzureChatCompletion, OpenAIChatCompletion
from semantic_kernel.contents.chat_history import ChatHistory
from app.config import settings

class SemanticKernelInterviewerAgent:
    def __init__(self, session_id: str):
        self.session_id = session_id
        self.kernel = sk.Kernel()
        self.service_id = "default"

        # Configure AI Service (Azure or OpenAI)
        if settings.AZURE_OPENAI_API_KEY and settings.AZURE_OPENAI_ENDPOINT:
            print(" Using Azure OpenAI with Semantic Kernel")
            service = AzureChatCompletion(
                service_id=self.service_id,
                deployment_name=settings.AZURE_OPENAI_DEPLOYMENT,
                endpoint=settings.AZURE_OPENAI_ENDPOINT,
                api_key=settings.AZURE_OPENAI_API_KEY,
            )
        else:
            print(" Using Standard OpenAI with Semantic Kernel")
            service = OpenAIChatCompletion(
                service_id=self.service_id,
                ai_model_id="gpt-3.5-turbo",
                api_key=settings.OPENAI_API_KEY,
            )

        self.kernel.add_service(service)

        # System Persona
        self.system_prompt = """You are a Senior Technical Interviewer and Subject Matter Expert (SME).
Your Goal: Assess the candidate's problem-solving skills while providing a supportive, interactive experience.

**Persona & Voice:**
- **Tone**: Professional, encouraging, conversational.
- **Style**: "Senior Engineer to Junior Engineer" mentorship.
- **Constraints**: 
    - Keep responses concise (spokens style).
    - Do NOT read code character-by-character.
    - Ask follow-up questions to guide the candidate.

**Responsibilities:**
1. Guide, Don't Solve: Give conceptual hints if stuck.
2. Deepen Discussion: Ask about complexity (Big O) or edge cases.
3. Be Responsive: Answer their specific questions directly.
"""

    def _build_context_message(self, context: Dict[str, Any]) -> str:
        """Construct a context-aware system message or user preamble"""
        msg = f"Current context:\n"
        if context.get('current_code'):
            msg += f"Candidate's Code:\n```javascript\n{context['current_code']}\n```\n"
        if context.get('recent_errors'):
            msg += f"Last Error:\n{context['recent_errors']}\n"
        if context.get('problem_title'):
            msg += f"Problem: {context['problem_title']}\n"
        return msg

    async def send_message(self, user_message: str, context: Dict[str, Any]) -> str:
        """
        Send a message using Semantic Kernel invocation
        """
        try:
            # Create a chat history object
            history = ChatHistory()
            history.add_system_message(self.system_prompt)
            
            # Add context as a user message (invisible thought) or system info
            context_msg = self._build_context_message(context)
            history.add_system_message(context_msg)
            
            # Add user query
            history.add_user_message(user_message)

            # Get Chat Completion Service
            chat_service = self.kernel.get_service(service_id=self.service_id)
            
            # Invoke
            response = await chat_service.get_chat_message_content(
                chat_history=history,
                settings=None # default settings
            )
            
            return str(response)

        except Exception as e:
            print(f"Semantic Kernel Error: {e}")
            return f"I apologize, I'm having trouble connecting to my cognitive services ({str(e)})."
