from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from uuid import UUID
from .types import Task, TaskResult, Message, MemoryObject, AgentState

class LLMInterface(ABC):
    """Interface for Large Language Model interactions."""
    @abstractmethod
    async def generate(self, prompt: str, context: Optional[List[Dict[str, Any]]] = None, **kwargs) -> str:
        pass

    @abstractmethod
    async def embed(self, text: str) -> List[float]:
        pass

class MemoryInterface(ABC):
    """Interface for memory storage (Vector DB + Key-Value)."""
    @abstractmethod
    async def store(self, item: MemoryObject, collection: str = "default") -> bool:
        pass

    @abstractmethod
    async def retrieve(self, query: str, limit: int = 5, collection: str = "default") -> List[MemoryObject]:
        pass

    @abstractmethod
    async def search_by_vector(self, vector: List[float], limit: int = 5, collection: str = "default") -> List[MemoryObject]:
        pass

    @abstractmethod
    async def clear(self, collection: str = "default"):
        pass

class CommunicationInterface(ABC):
    """Interface for inter-agent and system communication."""
    @abstractmethod
    async def send(self, message: Message):
        pass

    @abstractmethod
    async def receive(self, timeout: float = 1.0) -> Optional[Message]:
        pass

    @abstractmethod
    async def broadcast(self, message: Message):
        pass

class AgentInterface(ABC):
    """Interface for an autonomous agent."""
    @abstractmethod
    async def boot(self):
        """Initialize agent resources."""
        pass

    @abstractmethod
    async def shutdown(self):
        """Clean up agent resources."""
        pass

    @abstractmethod
    async def process_task(self, task: Task) -> TaskResult:
        """Execute a assigned task."""
        pass

    @abstractmethod
    async def receive_message(self, message: Message):
        """Handle incoming messages asynchronously."""
        pass

    @abstractmethod
    def get_state(self) -> AgentState:
        pass

class TeamInterface(ABC):
    """Interface for a team of agents."""
    @abstractmethod
    def add_agent(self, agent: AgentInterface):
        pass

    @abstractmethod
    def remove_agent(self, agent_id: str):
        pass

    @abstractmethod
    async def assign_task(self, task: Task) -> TaskResult:
        """Assigns a task to the team to solve."""
        pass

    @abstractmethod
    def get_agents(self) -> List[AgentInterface]:
        pass

class OrchestratorInterface(ABC):
    """Interface for the central orchestrator."""
    @abstractmethod
    async def register_team(self, team: TeamInterface):
        pass

    @abstractmethod
    async def submit_task(self, description: str) -> UUID:
        pass

    @abstractmethod
    async def run_competition(self, task_id: UUID, team_ids: List[str]) -> Dict[str, Any]:
        pass
