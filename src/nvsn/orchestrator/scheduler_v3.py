import asyncio
import structlog
from typing import Dict, List, Any
from ..core.types import Task, AgentState
from ..infra.database import db
from sqlalchemy import select
from ..infra.models import AgentModel

logger = structlog.get_logger()

class AdaptiveScheduler:
    """
    Uses reinforcement learning (simulated) to assign tasks based on agent success rates.
    """
    def __init__(self):
        self.logger = logger.bind(component="AdaptiveScheduler")
        # In-memory "weights" for RL simulation
        self.agent_scores: Dict[str, float] = {}

    async def assign_agent(self, task: Task, candidates: List[AgentState]) -> AgentState:
        """
        Selects the best agent for the task.
        """
        best_agent = None
        highest_score = -1.0

        for agent in candidates:
            # Basic heuristic:
            # Score = (Base Capability) * (Past Success Rate) + (Load Balancing Factor)

            # Fetch past success rate from DB
            success_count = 0
            # For real implementation: Query TaskModel where assigned_to=agent.id AND status=COMPLETED

            # Simulated Score
            current_score = self.agent_scores.get(agent.id, 1.0)

            # Penalize busy agents
            load_penalty = 0.5 if agent.status == "BUSY" else 0.0

            final_score = current_score - load_penalty

            if final_score > highest_score:
                highest_score = final_score
                best_agent = agent

        if best_agent:
            self.logger.info("Assigned task", task=task.description[:30], agent=best_agent.name, score=highest_score)
            return best_agent

        return candidates[0] if candidates else None

    def update_feedback(self, agent_id: str, success: bool):
        """
        RL Update Step: Reward or Penalize agent.
        """
        current = self.agent_scores.get(agent_id, 1.0)
        if success:
            self.agent_scores[agent_id] = min(current * 1.1, 5.0) # Cap at 5.0
        else:
            self.agent_scores[agent_id] = max(current * 0.8, 0.1) # Floor at 0.1

        self.logger.debug("Updated Agent Score", agent_id=agent_id, new_score=self.agent_scores[agent_id])
