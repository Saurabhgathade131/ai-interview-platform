import asyncio
import os
from dotenv import load_dotenv

# Force load .env
load_dotenv(".env")
print("OPENAI_KEY:", os.getenv("OPENAI_API_KEY")[:10] + "...")

from app.agents.interviewer_agent import InterviewerAgent

async def test_agent():
    print("Testing Interviewer Agent...")
    try:
        agent = InterviewerAgent("test-session")
        print(f"Agent initialized with client type: {type(agent.client)}")
        
        response = await agent.send_message("Hello, how are you?", {
            "current_code": "console.log('hello')",
            "problem_title": "Test Problem",
            "recent_errors": None
        })
        print("\n--- AI Response ---")
        print(response)
        print("-------------------")
        print("✅ SUCCESS!")
        
    except Exception as e:
        print("\n❌ FAILED with error:")
        print(str(e))
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_agent())
