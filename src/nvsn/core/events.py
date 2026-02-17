from typing import Any, Dict
from pydantic import BaseModel, Field
from datetime import datetime
from uuid import UUID
from enum import Enum

class EventType(str, Enum):
    TASK_CREATED = "TASK_CREATED"
    TASK_ASSIGNED = "TASK_ASSIGNED"
    TASK_COMPLETED = "TASK_COMPLETED"
    AGENT_STATUS_CHANGE = "AGENT_STATUS_CHANGE"
    TEAM_CREATED = "TEAM_CREATED"
    COMPETITION_START = "COMPETITION_START"
    COMPETITION_END = "COMPETITION_END"
    MEMORY_UPDATED = "MEMORY_UPDATED"
    ERROR = "ERROR"

class SystemEvent(BaseModel):
    event_type: EventType
    payload: Dict[str, Any]
    source: str = "SYSTEM"
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    correlation_id: str = Field(default_factory=lambda: str(datetime.utcnow().timestamp()))

class TaskEvent(SystemEvent):
    task_id: UUID

class AgentEvent(SystemEvent):
    agent_id: str
    team_id: str

class CompetitionEvent(SystemEvent):
    competition_id: str
    teams: list[str]
