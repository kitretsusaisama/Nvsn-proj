from .base import BaseAgent
from ..core.types import AgentRole, Task, TaskResult
from ..core.interfaces import LLMInterface, MemoryInterface, CommunicationInterface

class PlannerAgent(BaseAgent):
    def __init__(self, llm: LLMInterface, memory: MemoryInterface, communication: CommunicationInterface, team_id: str, name: str = None):
        super().__init__(AgentRole.PLANNER, llm, memory, communication, team_id, name)

    async def process_task(self, task: Task) -> TaskResult:
        self.logger.info("Planner is decomposing task")

        # Leverage base agent's memory retrieval (simple MVP integration)
        context_items = await self.memory.retrieve(task.description, limit=2)
        context_str = "\n".join([item.content for item in context_items]) if context_items else "No prior context."

        # Specialized prompt for planning
        prompt = f"""
        You are a Planner Agent.
        Goal: Create a detailed execution plan for the following task.
        Task: {task.description}
        Requirements: {task.requirements}
        Context: {context_str}

        Output format: Numbered list of subtasks with assigned roles.
        """
        response = await self.llm.generate(prompt)

        # Store result in memory via base implementation helper if we refactored,
        # but for now we manually store to ensure memory is populated.
        from ..core.types import MemoryObject
        await self.memory.store(
            MemoryObject(
                content=response,
                metadata={"task_id": str(task.id), "role": self.role.value, "type": "plan"},
                vector=await self.llm.embed(response)
            )
        )

        return TaskResult(task_id=task.id, success=True, output=response)

class EngineerAgent(BaseAgent):
    def __init__(self, llm: LLMInterface, memory: MemoryInterface, communication: CommunicationInterface, team_id: str, name: str = None):
        super().__init__(AgentRole.ENGINEER, llm, memory, communication, team_id, name)

    async def process_task(self, task: Task) -> TaskResult:
        self.logger.info("Engineer is writing code")

        context_items = await self.memory.retrieve(task.description, limit=2)
        context_str = "\n".join([item.content for item in context_items]) if context_items else ""

        prompt = f"""
        You are an Engineer Agent.
        Goal: Write robust, production-ready code.
        Task: {task.description}
        Specs: {task.requirements}
        Relevant Context: {context_str}

        Output: Code implementation.
        """
        response = await self.llm.generate(prompt)

        from ..core.types import MemoryObject
        await self.memory.store(
            MemoryObject(
                content=response,
                metadata={"task_id": str(task.id), "role": self.role.value, "type": "code"},
                vector=await self.llm.embed(response)
            )
        )

        return TaskResult(task_id=task.id, success=True, output=response)

class CriticAgent(BaseAgent):
    def __init__(self, llm: LLMInterface, memory: MemoryInterface, communication: CommunicationInterface, team_id: str, name: str = None):
        super().__init__(AgentRole.CRITIC, llm, memory, communication, team_id, name)

    async def process_task(self, task: Task) -> TaskResult:
        self.logger.info("Critic is reviewing work")
        prompt = f"""
        You are a Critic Agent.
        Goal: Evaluate the following work for errors, security, and performance.
        Work to Review: {task.metadata.get('previous_output', 'No context')}

        Output: Review and score.
        """
        response = await self.llm.generate(prompt)

        from ..core.types import MemoryObject
        await self.memory.store(
            MemoryObject(
                content=response,
                metadata={"task_id": str(task.id), "role": self.role.value, "type": "review"},
                vector=await self.llm.embed(response)
            )
        )

        return TaskResult(task_id=task.id, success=True, output=response)
