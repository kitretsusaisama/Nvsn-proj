from enum import Enum
from typing import Dict, List, Optional, Any, Union
from datetime import datetime
from pydantic import BaseModel, Field, UUID4
import uuid

class TaskStatus(str, Enum):
    PENDING = "PENDING"
    ASSIGNED = "ASSIGNED"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    REVIEW_REQUIRED = "REVIEW_REQUIRED"

class AgentRole(str, Enum):
    PLANNER = "PLANNER"
    ENGINEER = "ENGINEER"
    ANALYST = "ANALYST"
    RESEARCHER = "RESEARCHER"
    CRITIC = "CRITIC"
    NEGOTIATOR = "NEGOTIATOR"
    OPTIMIZER = "OPTIMIZER"
    CEO = "CEO"

class MessageType(str, Enum):
    REQUEST = "REQUEST"
    RESPONSE = "RESPONSE"
    INFO = "INFO"
    ERROR = "ERROR"
    BROADCAST = "BROADCAST"

class Task(BaseModel):
    id: UUID4 = Field(default_factory=uuid.uuid4)
    description: str
    requirements: List[str] = Field(default_factory=list)
    status: TaskStatus = Field(default=TaskStatus.PENDING)
    assigned_to: Optional[str] = None  # Agent ID or Team ID
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    result: Optional[Any] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)

class TaskResult(BaseModel):
    task_id: UUID4
    success: bool
    output: Any
    metrics: Dict[str, float] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class AgentState(BaseModel):
    id: str
    name: str
    role: AgentRole
    team_id: str
    status: str = "IDLE"
    current_task_id: Optional[UUID4] = None
    memory_usage: float = 0.0
    uptime: float = 0.0

class TeamState(BaseModel):
    id: str
    name: str
    agent_ids: List[str]
    active_tasks: int = 0
    score: float = 0.0

class Message(BaseModel):
    id: UUID4 = Field(default_factory=uuid.uuid4)
    sender_id: str
    receiver_id: Optional[str] = None  # None for broadcast
    type: MessageType
    payload: Dict[str, Any]
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    conversation_id: Optional[str] = None

class MemoryObject(BaseModel):
    id: UUID4 = Field(default_factory=uuid.uuid4)
    content: str
    vector: Optional[List[float]] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    source_agent_id: Optional[str] = None
