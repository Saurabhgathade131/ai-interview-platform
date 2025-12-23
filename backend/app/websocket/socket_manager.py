"""
WebSocket manager using Socket.io for real-time communication
Handles all bidirectional events between frontend and backend
"""
import socketio
import asyncio
from datetime import datetime
from typing import Dict
from app.models.session import (
    InterviewSession, 
    SessionStatus, 
    ChatMessage,
    ProctoringEvent,
    ProctoringEventType
)
from app.config import settings

# Create Socket.io server - Allow all origins for development
sio = socketio.AsyncServer(
    async_mode='asgi',
    cors_allowed_origins="*",  # Allow all origins
    logger=True,
    engineio_logger=True
)

# In-memory session storage (replace with database in production)
active_sessions: Dict[str, InterviewSession] = {}
# Map socket IDs to session IDs
socket_to_session: Dict[str, str] = {}

@sio.event
async def connect(sid, environ):
    """Handle client connection"""
    print(f"Client connected: {sid}")
    await sio.emit('connection_established', {'sid': sid}, room=sid)

@sio.event
async def disconnect(sid):
    """Handle client disconnection"""
    print(f"Client disconnected: {sid}")
    
    # Clean up session mapping
    if sid in socket_to_session:
        session_id = socket_to_session[sid]
        del socket_to_session[sid]
        print(f"Removed session mapping for {session_id}")

@sio.event
async def join_session(sid, data):
    """
    Join an interview session
    Expected data: { session_id: str, candidate_name?: str, experience_years?: int }
    """
    session_id = data.get('session_id')
    candidate_name = data.get('candidate_name', 'Candidate')
    experience_years = data.get('experience_years', 2)  # Default to junior level
    
    print(f"Client {sid} joining session {session_id}")
    
    # Create or retrieve session
    if session_id not in active_sessions:
        # Get dynamic problem based on experience level
        from app.services.problem_service import get_problem_service
        problem_service = get_problem_service()
        
        # Select a random problem appropriate for the candidate's level
        problem = problem_service.get_random_problem(experience_years=experience_years)
        
        # Generate the welcome message with problem description
        welcome_content = problem_service.format_problem_for_chat(problem, candidate_name)
        
        # Initialize new session with the selected problem
        active_sessions[session_id] = InterviewSession(
            session_id=session_id,
            candidate_name=candidate_name,
            problem_id=problem.problem_id,
            problem_title=problem.title,
            status=SessionStatus.IN_PROGRESS,
            started_at=datetime.utcnow(),
            current_code=problem.initial_code
        )
        
        # Store the problem reference for test generation
        active_sessions[session_id].problem = problem
        
        # Add welcome message from AI interviewer
        welcome_message = ChatMessage(
            role="assistant",
            content=welcome_content,
            timestamp=datetime.utcnow()
        )
        active_sessions[session_id].chat_history.append(welcome_message)
    
    # Map socket to session
    socket_to_session[sid] = session_id
    
    # Join socket.io room
    await sio.enter_room(sid, session_id)
    
    # Send current session state to client
    session = active_sessions[session_id]
    await sio.emit('session_joined', {
        'session_id': session_id,
        'problem_title': session.problem_title,
        'initial_code': session.current_code,
        'chat_history': [
            {
                'role': msg.role,
                'content': msg.content,
                'timestamp': msg.timestamp.isoformat(),
                'speak': True  # Enable TTS for welcome message
            }
            for msg in session.chat_history
        ],
        'status': session.status,
        'speak_welcome': True  # Flag to auto-speak welcome message
    }, room=sid)

@sio.event
async def code_update(sid, data):
    """
    Handle code updates from the editor (debounced on frontend)
    Expected data: { code: str }
    """
    if sid not in socket_to_session:
        return
    
    session_id = socket_to_session[sid]
    session = active_sessions.get(session_id)
    
    if not session:
        return
    
    # Update code in session
    session.current_code = data.get('code', '')
    session.last_code_update = datetime.utcnow()
    
    print(f"Code updated for session {session_id} (length: {len(session.current_code)})")
    
    # TODO: Analyze for stuck detection patterns
    # This will be implemented in the agent service

@sio.event
async def run_code(sid, data):
    """
    Execute code using Judge0
    Expected data: { code: str }
    """
    if sid not in socket_to_session:
        await sio.emit('execution_error', {
            'error': 'Not in a session'
        }, room=sid)
        return
    
    session_id = socket_to_session[sid]
    session = active_sessions.get(session_id)
    
    if not session:
        await sio.emit('execution_error', {
            'error': 'Session not found'
        }, room=sid)
        return
    
    code = data.get('code', session.current_code)
    
    # Emit execution started
    await sio.emit('execution_started', {}, room=sid)
    
    try:
        # Use Judge0 with working API key
        from app.services.judge0_service import Judge0Service
        
        judge0 = Judge0Service()
        result = await judge0.execute_code(code, session.problem_id)
        
        # Store execution result
        session.executions.append(result)
        session.last_execution = result
        
        # Check for repeated errors (stuck detection)
        if result.stderr or not result.test_passed:
            error_msg = result.stderr or "Tests failed"
            
            if session.last_error_message == error_msg:
                session.consecutive_errors += 1
            else:
                session.consecutive_errors = 1
                session.last_error_message = error_msg
            
            # Trigger hint if stuck
            if session.consecutive_errors >= settings.STUCK_ERROR_THRESHOLD and not session.hint_given:
                await trigger_stuck_hint(sid, session_id, session)
        else:
            # Reset error tracking on success
            session.consecutive_errors = 0
            session.last_error_message = None
            session.hint_given = False
        
        # Send result to client
        await sio.emit('execution_complete', {
            'stdout': result.stdout,
            'stderr': result.stderr,
            'status': result.status,
            'test_passed': result.test_passed,
            'test_total': result.test_total,
            'time': result.time,
            'memory': result.memory
        }, room=sid)
        
        # AI Interviewer responds naturally based on execution result
        await send_ai_execution_feedback(sid, session, result, code)
        
    except Exception as e:
        print(f"Execution error: {str(e)}")
        await sio.emit('execution_error', {
            'error': str(e)
        }, room=sid)


async def send_ai_execution_feedback(sid: str, session, result, code: str):
    """Send natural AI interviewer response based on code execution results"""
    try:
        # Build context for AI
        context = {
            "problem_id": session.problem_id,
            "problem_title": session.problem_title,
            "current_code": code,
            "test_passed": result.test_passed,
            "test_total": result.test_total,
            "stdout": result.stdout or "",
            "stderr": result.stderr or "",
            "consecutive_errors": session.consecutive_errors,
            "execution_time": result.time
        }
        
        # Construct the prompt for AI based on result
        if result.test_passed:
            # All tests passed - congratulate!
            prompt = f"""The candidate just ran their code for {session.problem_title} and ALL TESTS PASSED! 🎉

Respond like a real interviewer would:
1. Congratulate them briefly
2. Ask 1-2 follow-up questions about:
   - Time/space complexity of their solution
   - Alternative approaches they considered
   - How they would handle edge cases

Keep response conversational and under 100 words. Be encouraging!"""
        else:
            # Tests failed - provide helpful feedback
            error_info = result.stderr if result.stderr else result.stdout
            prompt = f"""The candidate just ran their code for {session.problem_title} and got errors.

Error output: {error_info[:500] if error_info else "Tests failed"}

Consecutive errors: {session.consecutive_errors}

Respond like a supportive interviewer:
1. Acknowledge the attempt briefly
2. Give ONE specific hint based on the error (don't reveal the solution)
3. Encourage them to try again

Keep response under 80 words. Be helpful, not condescending."""
        
        # Get AI response
        if settings.AZURE_OPENAI_API_KEY and settings.AZURE_OPENAI_ENDPOINT:
            from app.agents.sk_agent import SemanticKernelInterviewerAgent
            agent = SemanticKernelInterviewerAgent(socket_to_session[sid])
            ai_response = await agent.send_message(prompt, context)
        else:
            from app.agents.interviewer_agent import InterviewerAgent
            agent = InterviewerAgent(socket_to_session[sid])
            ai_response = await agent.send_message(prompt, context)
        
        # Store and send AI response
        ai_message = ChatMessage(
            role="assistant",
            content=ai_response,
            timestamp=datetime.utcnow()
        )
        session.chat_history.append(ai_message)
        
        # Emit to client with speak flag for TTS
        await sio.emit('chat_response', {
            'role': 'assistant',
            'content': ai_response,
            'timestamp': ai_message.timestamp.isoformat(),
            'speak': True  # Enable TTS for this response
        }, room=sid)
        
    except Exception as e:
        print(f"AI feedback error: {str(e)}")
        # Don't crash if AI feedback fails - the execution result already sent

@sio.event
async def chat_message(sid, data):
    """
    Handle chat messages from candidate with streaming response
    Expected data: { message: str }
    """
    if sid not in socket_to_session:
        return
    
    session_id = socket_to_session[sid]
    session = active_sessions.get(session_id)
    
    if not session:
        return
    
    user_message = data.get('message', '')
    
    # Add user message to history
    user_chat = ChatMessage(
        role="user",
        content=user_message,
        timestamp=datetime.utcnow()
    )
    session.chat_history.append(user_chat)
    
    # Get AI response
    try:
        # SELECT AGENT STRATEGY
        # If Azure keys are present, use the advanced Semantic Kernel Agent
        if settings.AZURE_OPENAI_API_KEY and settings.AZURE_OPENAI_ENDPOINT:
            try:
                from app.agents.sk_agent import SemanticKernelInterviewerAgent
                print("🚀 Using Microsoft Semantic Kernel Agent (Azure Configured)")
                agent = SemanticKernelInterviewerAgent(session_id)
            except Exception as e:
                print(f"⚠️ Failed to load Semantic Kernel ({e}). Falling back to Standard Agent.")
                from app.agents.interviewer_agent import InterviewerAgent
                agent = InterviewerAgent(session_id)
        else:
            # Fallback / Local LLM Mode
            from app.agents.interviewer_agent import InterviewerAgent
            agent = InterviewerAgent(session_id)
        
        # Prepare context
        context = {
            'current_code': session.current_code,
            'problem_title': session.problem_title,
            'recent_errors': session.last_error_message
        }

        # Get instant response (no streaming)
        print(f"DEBUG: Getting AI response for: {user_message[:50]}...")
        full_response = await agent.send_message(user_message, context)
        print(f"DEBUG: AI response received. Length: {len(full_response)}")
        
        # Add to chat history
        assistant_chat = ChatMessage(
            role="assistant",
            content=full_response,
            timestamp=datetime.utcnow()
        )
        session.chat_history.append(assistant_chat)
        
        # Send complete message with voice flag
        await sio.emit('chat_response', {
            'role': 'assistant',
            'content': full_response,
            'timestamp': assistant_chat.timestamp.isoformat(),
            'speak': True  # Enable text-to-speech on frontend
        }, room=sid)
        
    except Exception as e:
        print(f"Chat error: {str(e)}")
        await sio.emit('chat_error', {
            'error': str(e)
        }, room=sid)

@sio.event
async def proctoring_event(sid, data):
    """
    Log proctoring events (tab switches, paste detection)
    Expected data: { type: str, metadata?: dict }
    """
    if sid not in socket_to_session:
        return
    
    session_id = socket_to_session[sid]
    session = active_sessions.get(session_id)
    
    if not session:
        return
    
    event_type = data.get('type')
    metadata = data.get('metadata', {})
    
    # Create proctoring event
    event = ProctoringEvent(
        type=ProctoringEventType(event_type),
        timestamp=datetime.utcnow(),
        metadata=metadata
    )
    
    session.proctoring_events.append(event)
    
    print(f"Proctoring event: {event_type} for session {session_id}")

async def trigger_stuck_hint(sid: str, session_id: str, session: InterviewSession):
    """
    Trigger proactive hint when candidate is stuck
    """
    try:
        from app.agents.interviewer_agent import InterviewerAgent
        
        agent = InterviewerAgent(session_id)
        hint = await agent.proactive_hint({
            'error': session.last_error_message,
            'code': session.current_code,
            'consecutive_errors': session.consecutive_errors
        })
        
        # Add hint to chat history
        hint_message = ChatMessage(
            role="assistant",
            content=f"💡 **Hint:** {hint}",
            timestamp=datetime.utcnow()
        )
        session.chat_history.append(hint_message)
        session.hint_given = True
        
        # Send hint to client
        await sio.emit('chat_response', {
            'role': 'assistant',
            'content': hint_message.content,
            'timestamp': hint_message.timestamp.isoformat(),
            'is_hint': True
        }, room=sid)
        
    except Exception as e:
        print(f"Failed to generate hint: {str(e)}")

# Export session access for other modules
def get_session(session_id: str) -> InterviewSession:
    """Get session by ID"""
    return active_sessions.get(session_id)
