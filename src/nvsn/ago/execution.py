import asyncio
import structlog
from ..orchestrator.core_v2 import OrchestratorV2
from .governance import governance
from .goals import Goal

logger = structlog.get_logger()

class ExecutionInterface:
    """
    Bridge between Goal Management and NvsN Orchestration.
    """
    def __init__(self, orchestrator: OrchestratorV2):
        self.orchestrator = orchestrator
        self.logger = logger.bind(component="ExecutionLayer")

    async def execute_goal(self, goal: Goal):
        self.logger.info("Translating Goal to Task", goal=goal.description)

        # 1. Governance Check
        if not governance.validate_action(goal.description, {}):
            return "Execution Blocked"

        # 2. Trigger Orchestration
        task_id = await self.orchestrator.submit_task(goal.description)

        # 3. Wait for Result (Simplified for MVP)
        # Real system would async wait or callback
        self.logger.info("Orchestration Initiated", task_id=str(task_id))
        return task_id
