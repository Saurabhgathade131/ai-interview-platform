"""
Data models for interview sessions and related entities
"""
from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from enum import Enum

class SessionStatus(str, Enum):
    """Interview session status"""
    WAITING = "waiting"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    ABANDONED = "abandoned"

class ProctoringEventType(str, Enum):
    """Types of proctoring events"""
    TAB_SWITCH = "tab_switch"
    PASTE_DETECTED = "paste_detected"
    COPY_DETECTED = "copy_detected"
    WINDOW_BLUR = "window_blur"

class ProctoringEvent(BaseModel):
    """Single proctoring event"""
    type: ProctoringEventType
    timestamp: datetime
    metadata: Optional[Dict[str, Any]] = None

class CodeExecution(BaseModel):
    """Code execution result from Judge0"""
    stdout: Optional[str] = None
    stderr: Optional[str] = None
    compile_output: Optional[str] = None
    status: str
    time: Optional[float] = None
    memory: Optional[int] = None
    test_passed: bool = False
    test_total: int = 0

class ChatMessage(BaseModel):
    """Chat message between candidate and AI interviewer"""
    role: str  # 'user' or 'assistant'
    content: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class InterviewSession(BaseModel):
    """Complete interview session state"""
    session_id: str
    candidate_name: Optional[str] = None
    problem_id: str
    problem_title: str
    status: SessionStatus = SessionStatus.WAITING
    
    # Code state
    current_code: str = ""
    last_code_update: Optional[datetime] = None
    
    # Execution history
    executions: List[CodeExecution] = []
    last_execution: Optional[CodeExecution] = None
    
    # Chat history
    chat_history: List[ChatMessage] = []
    
    # Proctoring
    proctoring_events: List[ProctoringEvent] = []
    
    # Timestamps
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    
    # Stuck detection state
    consecutive_errors: int = 0
    last_error_message: Optional[str] = None
    hint_given: bool = False
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
