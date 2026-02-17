from ..core.interfaces import OrchestratorInterface, TeamInterface, LLMInterface
from ..core.types import Task, TaskResult, TaskStatus
from .registry import TeamRegistry
from .scheduler import TaskScheduler
from ..competition.arena import CompetitionArena
from ..competition.judge import CompetitionJudge
from typing import List, Dict, Any, Optional
import uuid
import asyncio
import structlog
from datetime import datetime

logger = structlog.get_logger()

class Orchestrator(OrchestratorInterface):
    """
    The central brain coordinating teams, tasks, and competitions.
    """
    def __init__(self, llm: LLMInterface):
        self.llm = llm
        self.registry = TeamRegistry()
        self.scheduler = TaskScheduler()
        self.judge = CompetitionJudge(llm)
        self.arena = CompetitionArena(self.judge)
        self.logger = logger.bind(component="Orchestrator")

    async def register_team(self, team: TeamInterface):
        self.registry.register(team)
        self.logger.info("Registered team", team_name=team.name, team_id=team.id)

    async def submit_task(self, description: str, requirements: List[str] = None) -> uuid.UUID:
        task = Task(
            description=description,
            requirements=requirements or []
        )
        await self.scheduler.add_task(task)
        self.logger.info("Task submitted", task_id=str(task.id), description=description)
        return task.id

    async def run_competition(self, task_id: uuid.UUID, team_ids: List[str]) -> Dict[str, Any]:
        """
        Executes an N-vs-N competition for a given task.
        """
        task = self.scheduler.active_tasks.get(str(task_id))
        if not task:
            raise ValueError(f"Task {task_id} not found")

        teams = []
        for tid in team_ids:
            team = self.registry.get_team(tid)
            if not team:
                raise ValueError(f"Team {tid} not registered")
            teams.append(team)

        self.logger.info("Starting competition", task_id=str(task_id), teams=[t.name for t in teams])

        # Update task status
        task.status = TaskStatus.IN_PROGRESS
        task.assigned_to = "COMPETITION"

        try:
            # Delegate to Arena
            results = await self.arena.conduct_match(task, teams)

            # Process results
            winner = results.get("winner")
            scores = results.get("scores")

            task.status = TaskStatus.COMPLETED
            task.result = results

            self.logger.info("Competition finished", winner=winner, scores=scores)
            return results

        except Exception as e:
            self.logger.error("Competition failed", error=str(e))
            task.status = TaskStatus.FAILED
            raise e
