import asyncio
import uuid
import structlog
from typing import List, Dict, Optional
from ..core.types import Task, TaskResult
from ..core.actor import Actor
from ..infra.mesh import mesh

logger = structlog.get_logger()

class FractalAgent(Actor):
    """
    An agent capable of recursive mitosis (splitting into sub-agents)
    to handle complex tasks through massive parallelism.
    """
    def __init__(self, agent_id: str = None, parent_id: str = None, depth: int = 0):
        super().__init__(agent_id)
        self.parent_id = parent_id
        self.depth = depth
        self.children: List[str] = []
        self.max_depth = 3 # Prevent infinite recursion
        self.logger = logger.bind(id=self.id, depth=self.depth, type="Fractal")

    async def handle_message(self, message):
        if message.type == "TASK_FRACTAL":
            await self._process_fractal_task(message.payload)
        elif message.type == "CHILD_RESULT":
            await self._aggregate_result(message.payload)

    async def _process_fractal_task(self, task: Dict):
        complexity = task.get("complexity", 1)

        # Mitosis Condition: If complex and depth limit not reached
        if complexity > 1 and self.depth < self.max_depth:
            self.logger.info("Task too complex. Initiating Mitosis.", complexity=complexity)
            await self._mitosis(task)
        else:
            # Leaf Node Execution
            self.logger.info("Executing Leaf Task")
            await asyncio.sleep(0.1) # Work simulation
            result = f"Result from {self.id} (Depth {self.depth})"

            if self.parent_id:
                # Send back to parent
                from ..core.actor import Message
                await mesh.send_message(Message(self.id, self.parent_id, result, "CHILD_RESULT"))
            else:
                self.logger.info("Root Agent Finished", result=result)

    async def _mitosis(self, task: Dict):
        """
        Spawns sub-agents.
        """
        complexity = task.get("complexity", 1)
        sub_task_count = 2 # Binary split for simplicity

        for i in range(sub_task_count):
            child_id = f"{self.id}.{i}"
            child = FractalAgent(child_id, self.id, self.depth + 1)
            mesh.register(child)
            await child.start()
            self.children.append(child_id)

            # Send sub-task
            from ..core.actor import Message
            sub_task = task.copy()
            sub_task["complexity"] = complexity - 1
            await mesh.send_message(Message(self.id, child_id, sub_task, "TASK_FRACTAL"))

    async def _aggregate_result(self, result: str):
        self.logger.info("Received Child Result", result=result)
        # In a real system, wait for all children then reduce
        # Here we just log for the demo visualization
