import asyncio
import pickle
import structlog
from typing import Callable, Any, Dict, List
from datetime import datetime
from ..infra.database import db
from sqlalchemy import Column, String, Integer, LargeBinary, select
from ..infra.database import Base

logger = structlog.get_logger()

# SQL Model for Event History
class WorkflowEventModel(Base):
    __tablename__ = "workflow_events"
    id = Column(Integer, primary_key=True, autoincrement=True)
    workflow_id = Column(String, index=True)
    event_type = Column(String)
    payload = Column(LargeBinary) # Pickled data
    timestamp = Column(String)

class WorkflowContext:
    def __init__(self, workflow_id: str, replaying: bool = False):
        self.workflow_id = workflow_id
        self.replaying = replaying
        self.event_id = 0

class DurableEngine:
    """
    Deterministically executes workflows by logging events.
    On restart, it replays history to restore state without re-executing side effects.
    """
    def __init__(self):
        self.logger = logger.bind(component="DurableEngine")

    async def run_workflow(self, workflow_id: str, workflow_fn: Callable, *args):
        self.logger.info("Starting Workflow", id=workflow_id)

        # 1. Replay History
        ctx = WorkflowContext(workflow_id, replaying=True)
        history = await self._fetch_history(workflow_id)

        # Generator based workflow? Or simplified awaitable based?
        # Simplified: We inject a proxy context that intercepts calls

        try:
            await workflow_fn(ctx, *args)
        except Exception as e:
            self.logger.error("Workflow Failed", error=str(e))
            raise e

    async def activity(self, ctx: WorkflowContext, name: str, fn: Callable, *args):
        """
        Executes a side-effect activity.
        If replaying, returns recorded result.
        If new, executes and records.
        """
        ctx.event_id += 1
        event_key = f"{name}_{ctx.event_id}"

        # check history
        history = await self._fetch_history(ctx.workflow_id)
        # Naive matching by sequence index for MVP
        if ctx.event_id <= len(history):
            recorded_event = history[ctx.event_id - 1]
            if recorded_event.event_type == name:
                self.logger.info("Replaying Activity", name=name, result="SKIPPED (Cached)")
                return pickle.loads(recorded_event.payload)

        # Execute Real
        self.logger.info("Executing Activity", name=name)
        # Check if function is coroutine
        if asyncio.iscoroutinefunction(fn):
            result = await fn(*args)
        else:
            # Run sync function
            result = fn(*args)

        # Persist
        await self._persist_event(ctx.workflow_id, name, result)
        return result

    async def _fetch_history(self, workflow_id: str):
        async for session in db.get_session():
            result = await session.execute(
                select(WorkflowEventModel)
                .where(WorkflowEventModel.workflow_id == workflow_id)
                .order_by(WorkflowEventModel.id)
            )
            return result.scalars().all()

    async def _persist_event(self, workflow_id: str, event_type: str, result: Any):
        async for session in db.get_session():
            evt = WorkflowEventModel(
                workflow_id=workflow_id,
                event_type=event_type,
                payload=pickle.dumps(result),
                timestamp=str(datetime.utcnow())
            )
            session.add(evt)
            await session.commit()

# Singleton
durable = DurableEngine()
