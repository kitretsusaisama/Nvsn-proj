import asyncio
import structlog
from typing import Optional
from .perception import SensoryCortex
from ..orchestrator.core_v2 import OrchestratorV2
from ..agents.gemini_llm import GeminiLLM
from ..config import settings

logger = structlog.get_logger()

class ArtificialGeneralOperator:
    """
    The Core Intelligence Engine.
    Operates across 7 layers to achieve full autonomy.
    """
    def __init__(self):
        self.logger = logger.bind(component="AGO_Core")

        # Layer 1: Perception
        self.senses = SensoryCortex()

        # Layer 2: World Model (Initialized later)
        self.world_model = None

        # Layer 3: Goal Management (Initialized later)
        self.goal_manager = None

        # Layer 4: Orchestration (The Muscle)
        llm = GeminiLLM(api_key=settings.google_api_key) if settings.google_api_key else None

        # Fallback to MockLLM if no key
        if not llm:
            from ..agents.llm import MockLLM
            llm = MockLLM()

        self.orchestrator = OrchestratorV2(llm=llm)

        self._running = False

    async def boot(self):
        self.logger.info("Initializing Artificial General Operator...")
        # Bootup sequence for all layers
        self._running = True

        # Start sensory loop simulation
        asyncio.create_task(self.senses.simulate_environment())

        # Start Cognitive Loop
        asyncio.create_task(self._cognitive_loop())

    async def _cognitive_loop(self):
        self.logger.info("Cognitive Loop Online. Awaiting Signals...")
        while self._running:
            # 1. Perceive
            signals = await self.senses.sense()
            if signals:
                self.logger.info("Processing Sensory Batch", count=len(signals))
                for signal in signals:
                    await self._process_signal(signal)

            await asyncio.sleep(1)

    async def _process_signal(self, signal):
        # 2. Update World Model (Stub)
        # 3. Check Goals
        # 4. Act
        if signal.severity > 0.7:
            self.logger.critical("High Severity Signal Detected! Initiating Response Protocol.", type=signal.type)
            # Trigger Goal Formation -> Execution
            # (Implemented in next steps)

    async def shutdown(self):
        self._running = False
        self.logger.info("AGO Shutting Down.")
