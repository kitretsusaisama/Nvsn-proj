import numpy as np
import structlog
from typing import Dict, List, Any
from ..core.types import Task, AgentState
from ..infra.models import AgentModel

logger = structlog.get_logger()

class ProbabilisticScheduler:
    """
    Uses Bayesian inference (Naive Bayes) to predict task success probability and route accordingly.
    """
    def __init__(self):
        self.logger = logger.bind(component="ProbabilisticScheduler")
        # Feature Matrix: [Agent_ID, Task_Type_ID, Load]
        self.X_train = []
        # Target Vector: [Success (1) / Failure (0)]
        self.y_train = []

        # Simple mapping for categorical data
        self.agent_map = {}
        self.task_type_map = {"code": 0, "plan": 1, "review": 2, "general": 3}

    def _encode(self, agent_id: str, task_type: str, load: float):
        if agent_id not in self.agent_map:
            self.agent_map[agent_id] = len(self.agent_map)

        t_type = self.task_type_map.get(task_type, 3)
        return [self.agent_map[agent_id], t_type, load]

    def update_model(self, agent_id: str, task_type: str, success: bool, load: float = 0.5):
        """
        Online learning update.
        """
        features = self._encode(agent_id, task_type, load)
        self.X_train.append(features)
        self.y_train.append(1 if success else 0)
        self.logger.debug("Model updated", agent=agent_id, success=success)

    async def assign_agent(self, task: Task, candidates: List[AgentState]) -> AgentState:
        """
        Predicts P(Success | Agent, Task) and selects max.
        """
        if len(self.X_train) < 10:
            # Cold start: Round robin or random
            return candidates[0] if candidates else None

        from sklearn.naive_bayes import GaussianNB
        model = GaussianNB()
        model.fit(self.X_train, self.y_train)

        best_agent = None
        max_prob = -1.0

        task_type = "general"
        if "code" in task.description.lower(): task_type = "code"
        elif "plan" in task.description.lower(): task_type = "plan"

        for agent in candidates:
            # Encode query
            if agent.id not in self.agent_map:
                # New agent, neutral probability
                prob = 0.5
            else:
                features = [self._encode(agent.id, task_type, 0.5)] # Assume avg load
                prob = model.predict_proba(features)[0][1] # Probability of class 1 (Success)

            if prob > max_prob:
                max_prob = prob
                best_agent = agent

        self.logger.info("Bayesian Assignment", agent=best_agent.name, prob=f"{max_prob:.2f}")
        return best_agent
