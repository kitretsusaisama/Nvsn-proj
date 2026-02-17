from ..core.interfaces import AgentInterface, LLMInterface, MemoryInterface, CommunicationInterface
from ..core.types import Task, TaskResult, Message, AgentState, AgentRole, MemoryObject
from ..utils.logging import configure_logging
from typing import Dict, List, Optional
import structlog
import uuid
from datetime import datetime

logger = structlog.get_logger()

class BaseAgent(AgentInterface):
    """
    Core implementation of an autonomous agent.
    """
    def __init__(self,
                 role: AgentRole,
                 llm: LLMInterface,
                 memory: MemoryInterface,
                 communication: CommunicationInterface,
                 team_id: str,
                 name: Optional[str] = None):
        self.id = str(uuid.uuid4())
        self.role = role
        self.name = name or f"{role.value}_{self.id[:8]}"
        self.team_id = team_id
        self.llm = llm
        self.memory = memory
        self.communication = communication

        self.state = AgentState(
            id=self.id,
            name=self.name,
            role=self.role,
            team_id=self.team_id,
            status="INITIALIZING"
        )
        self.logger = logger.bind(agent_id=self.id, role=self.role.value)

    async def boot(self):
        """Initialize agent resources."""
        self.state.status = "IDLE"
        self.logger.info("Agent booting up", status="IDLE")
        # Could load personality or skills from memory here

    async def shutdown(self):
        """Clean up agent resources."""
        self.state.status = "OFFLINE"
        self.logger.info("Agent shutting down")

    async def process_task(self, task: Task) -> TaskResult:
        """Execute a assigned task using LLM reasoning."""
        self.state.current_task_id = task.id
        self.state.status = "WORKING"
        self.logger.info("Processing task", task_id=str(task.id), description=task.description)

        try:
            # 1. Retrieve context from memory
            context_items = await self.memory.retrieve(task.description, limit=3)
            context_str = "\n".join([item.content for item in context_items]) if context_items else "No prior context."

            # 2. Construct prompt
            prompt = f"Role: {self.role.value}\nTask: {task.description}\nRequirements: {task.requirements}\nContext: {context_str}\nGenerate a solution."

            # 3. Use LLM to solve
            response = await self.llm.generate(prompt)

            # 4. Store result in memory (fire and forget or await)
            await self.memory.store(
                MemoryObject(
                    content=response,
                    metadata={"task_id": str(task.id), "role": self.role.value},
                    vector=await self.llm.embed(response)
                )
            )

            self.state.status = "IDLE"
            self.state.current_task_id = None

            return TaskResult(
                task_id=task.id,
                success=True,
                output=response,
                timestamp=datetime.utcnow()
            )

        except Exception as e:
            self.logger.error("Task execution failed", error=str(e))
            self.state.status = "ERROR"
            return TaskResult(
                task_id=task.id,
                success=False,
                output=str(e),
                timestamp=datetime.utcnow()
            )

    async def receive_message(self, message: Message):
        """Handle incoming messages asynchronously."""
        self.logger.info("Received message", sender=message.sender_id, type=message.type)
        # Logic to handle different message types (REQUEST, RESPONSE, INFO)

    def get_state(self) -> AgentState:
        return self.state
