from sqlalchemy import Column, Integer, String, JSON, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from .database import Base
from datetime import datetime
import uuid

def generate_uuid():
    return str(uuid.uuid4())

class AgentModel(Base):
    __tablename__ = "agents"

    id = Column(String, primary_key=True, default=generate_uuid)
    name = Column(String, nullable=False)
    role = Column(String, nullable=False)
    team_id = Column(String, ForeignKey("teams.id"), nullable=True)
    status = Column(String, default="OFFLINE")
    created_at = Column(DateTime, default=datetime.utcnow)
    memory_context = Column(JSON, default=dict) # Short-term memory state

    team = relationship("TeamModel", back_populates="agents")

class TeamModel(Base):
    __tablename__ = "teams"

    id = Column(String, primary_key=True, default=generate_uuid)
    name = Column(String, unique=True, nullable=False)
    score = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)

    agents = relationship("AgentModel", back_populates="team", lazy="selectin")

class TaskModel(Base):
    __tablename__ = "tasks"

    id = Column(String, primary_key=True, default=generate_uuid)
    description = Column(String, nullable=False)
    requirements = Column(JSON, default=list)
    status = Column(String, default="PENDING")
    result = Column(JSON, nullable=True)
    assigned_to = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)

class MemoryLogModel(Base):
    __tablename__ = "memory_logs"

    id = Column(String, primary_key=True, default=generate_uuid)
    agent_id = Column(String, ForeignKey("agents.id"), nullable=True)
    content = Column(String, nullable=False)
    vector_id = Column(String, nullable=True) # Reference to vector DB ID
    metadata_info = Column(JSON, default=dict)
    timestamp = Column(DateTime, default=datetime.utcnow)
