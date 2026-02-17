from .base import BaseAgent
from ..core.types import AgentRole, Task, TaskResult
from ..core.interfaces import LLMInterface, MemoryInterface, CommunicationInterface

class PlannerAgent(BaseAgent):
    def __init__(self, llm: LLMInterface, memory: MemoryInterface, communication: CommunicationInterface, team_id: str, name: str = None):
        super().__init__(AgentRole.PLANNER, llm, memory, communication, team_id, name)

    async def process_task(self, task: Task) -> TaskResult:
        self.logger.info("Planner is decomposing task")
        # Specialized prompt for planning
        prompt = f"""
        You are a Planner Agent.
        Goal: Create a detailed execution plan for the following task.
        Task: {task.description}
        Requirements: {task.requirements}

        Output format: Numbered list of subtasks with assigned roles.
        """
        response = await self.llm.generate(prompt)
        return TaskResult(task_id=task.id, success=True, output=response)

class EngineerAgent(BaseAgent):
    def __init__(self, llm: LLMInterface, memory: MemoryInterface, communication: CommunicationInterface, team_id: str, name: str = None):
        super().__init__(AgentRole.ENGINEER, llm, memory, communication, team_id, name)

    async def process_task(self, task: Task) -> TaskResult:
        self.logger.info("Engineer is writing code")
        prompt = f"""
        You are an Engineer Agent.
        Goal: Write robust, production-ready code.
        Task: {task.description}
        Specs: {task.requirements}

        Output: Code implementation.
        """
        response = await self.llm.generate(prompt)
        return TaskResult(task_id=task.id, success=True, output=response)

class CriticAgent(BaseAgent):
    def __init__(self, llm: LLMInterface, memory: MemoryInterface, communication: CommunicationInterface, team_id: str, name: str = None):
        super().__init__(AgentRole.CRITIC, llm, memory, communication, team_id, name)

    async def process_task(self, task: Task) -> TaskResult:
        self.logger.info("Critic is reviewing work")
        prompt = f"""
        You are a Critic Agent.
        Goal: Evaluate the following work for errors, security, and performance.
        Context: {task.metadata.get('previous_output', 'No context')}

        Output: Review and score.
        """
        response = await self.llm.generate(prompt)
        return TaskResult(task_id=task.id, success=True, output=response)
