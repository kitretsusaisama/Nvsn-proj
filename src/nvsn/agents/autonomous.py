import structlog
from sqlalchemy import select

from ..agents.cognitive import CognitiveAgent
from ..core.types import AgentRole, Task, TaskResult
from ..infra.bus import bus
from ..infra.database import db
from ..infra.models import MemoryLogModel

logger = structlog.get_logger()

class AutonomousAgent(CognitiveAgent):
    """
    V3 Agent with Meta-Cognition:
    1. Reflects on past mistakes (Memory Retrieval)
    2. Dynamically creates Tools (Self-Code)
    3. Spawns Sub-Agents (Recursion)
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.logger = logger.bind(
            agent_id=self.id, role=self.role.value, type="Autonomous"
        )

    async def _reflect_on_failures(self, task: Task) -> str:
        """
        Look up similar failed tasks in episodic memory.
        """
        self.logger.info("Reflecting on past failures...")

        # Simulated lookup (in real prod, vector search for "failed task" + similarity)
        # For now, just check recent error logs
        reflections = []
        async for session in db.get_session():
            result = await session.execute(
                select(MemoryLogModel)
                .where(
                    MemoryLogModel.agent_id == self.role.value,
                    MemoryLogModel.content.ilike("%error%")
                )
                .order_by(MemoryLogModel.timestamp.desc())
                .limit(5)
            )
            logs = result.scalars().all()
            for log in logs:
                reflections.append(f"- Previous Failure: {log.content}")

        return "\n".join(reflections) if reflections else "No relevant failures found."

    async def _create_dynamic_tool(self, tool_spec: str):
        """
        Agent writes its own Python tool class and registers it.
        Risk: High. Use strictly sandboxed env.
        """
        self.logger.warning("Agent creating dynamic tool", spec=tool_spec[:50])
        # For MVP safety, we mock this creation or restrict severely
        # Real implementation: Write to file, import module, register class
        pass

    async def process_task(self, task: Task) -> TaskResult:
        # Pre-execution Reflection
        reflection = await self._reflect_on_failures(task)

        # Modify context with reflection
        task.description += (
            f"\n\n[SELF-REFLECTION]\nAvoid these past mistakes:\n{reflection}"
        )

        # Delegate to standard ReAct loop
        return await super().process_task(task)

    async def spawn_sub_agent(self, role: AgentRole, task: Task):
        """
        Spawns a temporary worker agent for parallel subtask.
        """
        self.logger.info("Spawning Sub-Agent", role=role)
        # In distributed system, this means sending a "SpawnRequest" to Orchestrator
        # MVP: Just log intent
        await bus.push_task("spawn_queue", {
            "parent_agent": self.id,
            "role": role,
            "task": task.model_dump(mode='json')
        })
