import uuid
from enum import Enum
from typing import List, Optional
import structlog
from pydantic import BaseModel

logger = structlog.get_logger()

class GoalPriority(str, Enum):
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"

class Goal(BaseModel):
    id: str
    description: str
    priority: GoalPriority
    status: str = "ACTIVE"
    sub_goals: List[str] = []

class GoalManager:
    """
    Autonomously generates, prioritizes, and retires goals.
    """
    def __init__(self, world_model):
        self.world_model = world_model
        self.active_goals: List[Goal] = []
        self.logger = logger.bind(component="GoalManager")

    def generate_goal(self, trigger: str, priority: GoalPriority = GoalPriority.MEDIUM) -> Goal:
        goal_id = str(uuid.uuid4())
        goal = Goal(id=goal_id, description=trigger, priority=priority)
        self.active_goals.append(goal)
        # Sort by priority
        self.active_goals.sort(key=lambda x: x.priority, reverse=True) # Simple sort
        self.logger.info("New Goal Generated", goal=trigger, priority=priority)
        return goal

    def check_feasibility(self, goal: Goal) -> bool:
        # Check World Model for resources
        # Stub logic
        return True

    def complete_goal(self, goal_id: str):
        self.active_goals = [g for g in self.active_goals if g.id != goal_id]
        self.logger.info("Goal Achieved", goal_id=goal_id)
