from datetime import datetime
import asyncio
import uuid
import structlog
from typing import Dict, Any, List
from ..core.interfaces import OrchestratorInterface, TeamInterface, LLMInterface
from ..core.types import Task, TaskStatus
from ..infra.bus import bus
from ..infra.database import db
from ..infra.models import TaskModel, AgentModel
from .registry import TeamRegistry
from .scheduler import TaskScheduler
from ..competition.arena import CompetitionArena
from ..competition.judge import CompetitionJudge

logger = structlog.get_logger()

class OrchestratorV2(OrchestratorInterface):
    """
    Production-grade Orchestrator utilizing DB and MessageBus.
    """
    def __init__(self, llm: LLMInterface):
        self.llm = llm
        self.registry = TeamRegistry()
        self.scheduler = TaskScheduler()
        self.judge = CompetitionJudge(llm)
        self.arena = CompetitionArena(self.judge)
        self.logger = logger.bind(component="OrchestratorV2")

        # Initialize Infra
        asyncio.create_task(db.init_models())
        asyncio.create_task(self._listen_for_tasks())

    async def _listen_for_tasks(self):
        """
        Background worker simulating a distributed consumer.
        """
        self.logger.info("Worker started, listening for tasks...")
        # In a real system, this runs in a separate process/container.
        while True:
            # Poll queue
            task_data = await bus.pop_task("tasks", timeout=1)
            if task_data:
                await self._process_task_event(task_data)
            await asyncio.sleep(0.1)

    async def _process_task_event(self, task_data: Dict[str, Any]):
        self.logger.info("Processing Task Event", task_id=task_data.get("id"))
        # In a real distributed system, this would:
        # 1. Check if it's a competition task or single team task
        # 2. Assign to specific worker queue if needed
        # 3. Trigger execution (e.g. self.run_competition(...))
        #
        # For this MVP, since we run everything in one process for demo,
        # we acknowledge receipt but rely on the direct `run_competition` call
        # in the example script to trigger the actual logic to avoid double execution.
        pass

    async def register_team(self, team: TeamInterface):
        self.registry.register(team)
        self.logger.info("Registered team", team_name=team.name)

        # Persist Team/Agents to SQL
        async for session in db.get_session():
            # session.merge(TeamModel(...)) - implementation detail for full prod
            pass

    async def submit_task(self, description: str, requirements: List[str] = None) -> uuid.UUID:
        task = Task(description=description, requirements=requirements or [])

        # 1. Persist to SQL
        async for session in db.get_session():
            db_task = TaskModel(
                id=str(task.id),
                description=description,
                requirements=requirements,
                status="PENDING"
            )
            session.add(db_task)
            await session.commit()

        # 2. Push to Distributed Queue
        await bus.push_task("tasks", task.model_dump(mode='json'))

        self.logger.info("Task submitted & persisted", task_id=str(task.id))
        return task.id

    async def run_competition(self, task_id: uuid.UUID, team_ids: List[str]) -> Dict[str, Any]:
        """
        Orchestrates the competition execution.
        """
        # Retrieve Task from DB
        task = None
        # Simplified retrieval for MVP: usually fetch from DB, here re-construct or fetch
        # For now, let's assume passed task ID is valid and re-create object or fetch from memory if needed
        # To keep it robust, we should fetch from DB.

        from sqlalchemy import select
        async for session in db.get_session():
            result = await session.execute(select(TaskModel).where(TaskModel.id == str(task_id)))
            db_task = result.scalars().first()
            if db_task:
                 task = Task(
                     id=uuid.UUID(db_task.id),
                     description=db_task.description,
                     requirements=db_task.requirements or [],
                     status=TaskStatus.IN_PROGRESS
                 )

        if not task:
            raise ValueError(f"Task {task_id} not found in DB")

        teams = []
        for tid in team_ids:
            team = self.registry.get_team(tid)
            if team:
                teams.append(team)
            else:
                 self.logger.warning("Team not found in registry", team_id=tid)

        self.logger.info("Starting V2 Competition", task_id=str(task.id), teams=[t.name for t in teams])

        try:
            results = await self.arena.conduct_match(task, teams)

            # Update Task Status in DB
            from sqlalchemy import select
            async for session in db.get_session():
                 # Re-fetch to update
                 result = await session.execute(select(TaskModel).where(TaskModel.id == str(task_id)))
                 db_task = result.scalars().first()
                 if db_task:
                     db_task.status = "COMPLETED"
                     db_task.result = results
                     db_task.completed_at = datetime.utcnow()
                     await session.commit()

            return results

        except Exception as e:
            self.logger.error("Competition failed", error=str(e))
            raise e
