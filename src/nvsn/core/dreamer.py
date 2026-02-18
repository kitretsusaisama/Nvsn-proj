import asyncio
import structlog
from ..infra.database import db
from ..infra.models import MemoryLogModel
from ..memory.graph import KnowledgeGraphMemory
from sqlalchemy import select

logger = structlog.get_logger()

class Dreamer:
    """
    Background process that runs during idle time.
    Reads raw Event Logs (SQL) and distills them into Wisdom (Knowledge Graph).
    """
    def __init__(self, kg: KnowledgeGraphMemory):
        self.kg = kg
        self.logger = logger.bind(component="Dreamer")
        self._running = False

    async def start(self):
        self._running = True
        asyncio.create_task(self._dream_loop())

    async def _dream_loop(self):
        self.logger.info("Dreamer Online")
        while self._running:
            await asyncio.sleep(5) # Dream every 5 seconds
            try:
                await self._consolidate_memories()
            except Exception as e:
                self.logger.error("Nightmare (Error)", error=str(e))

    async def _consolidate_memories(self):
        """
        Reads recent logs and updates graph.
        """
        async for session in db.get_session():
            # Get unindexed logs (mock query)
            result = await session.execute(select(MemoryLogModel).limit(5))
            logs = result.scalars().all()

            count = 0
            for log in logs:
                # Naive NLP extraction simulation
                if "error" in log.content.lower():
                    self.kg.add_fact(log.agent_id, "encountered", "Error")
                    count += 1

            if count > 0:
                self.logger.info("Dream Consolidated", facts_learned=count)
