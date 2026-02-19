import asyncio
import structlog
from typing import List, Dict, Any, Optional
from datetime import datetime
import random

logger = structlog.get_logger()

class Signal:
    def __init__(self, source: str, type: str, payload: Dict[str, Any], severity: float = 0.5):
        self.source = source
        self.type = type
        self.payload = payload
        self.severity = severity
        self.timestamp = datetime.utcnow()

class SensoryCortex:
    """
    Perception Layer: Monitors and ingests signals from the environment.
    """
    def __init__(self):
        self.signals: asyncio.Queue = asyncio.Queue()
        self.logger = logger.bind(component="SensoryCortex")
        self._sources = []

    def register_source(self, source_name: str):
        self._sources.append(source_name)
        self.logger.info("Registered Sensory Source", source=source_name)

    async def ingest(self, signal: Signal):
        self.logger.debug("Signal Received", type=signal.type, source=signal.source)
        await self.signals.put(signal)

    async def sense(self) -> List[Signal]:
        """
        Batch retrieve processed signals.
        """
        batch = []
        while not self.signals.empty():
            batch.append(await self.signals.get())
        return batch

    # Simulation method for demo
    async def simulate_environment(self):
        """
        Randomly generates environmental noise and events.
        """
        while True:
            await asyncio.sleep(random.uniform(2, 5))
            # Simulate random system event
            event_type = random.choice(["LOG", "METRIC", "ALERT"])
            severity = random.random()

            if severity > 0.8:
                await self.ingest(Signal("SYS_MONITOR", "CRITICAL_ALERT", {"msg": "High CPU"}, severity))
            else:
                await self.ingest(Signal("SYS_LOG", "INFO", {"msg": "Routine check"}, severity))
