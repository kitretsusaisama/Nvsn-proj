import asyncio
import sys
import os
import structlog
from dotenv import load_dotenv

sys.path.append(os.path.join(os.path.dirname(__file__), '../src'))

from nvsn.ago.core import ArtificialGeneralOperator
from nvsn.ago.world_model import WorldModel
from nvsn.ago.goals import GoalManager, GoalPriority
from nvsn.ago.execution import ExecutionInterface
from nvsn.ago.perception import Signal
from nvsn.utils.logging import configure_logging
from nvsn.infra.database import db

# Augment AGO class with Logic implemented in previous steps
# In a real refactor, these would be in the class definition.
# Here we patch for the demo flow since I split file creation.

async def process_signal_logic(self, signal):
    self.logger.info("Perception Event", type=signal.type, payload=signal.payload)

    # 2. Update World Model
    self.world_model.update_state("System", "status", signal.payload.get("msg"))

    # 3. Check Goals
    if signal.severity > 0.6:
        self.logger.warning("Anomaly Detected. Generating Goal...")
        goal = self.goal_manager.generate_goal(
            f"Resolve {signal.type}: {signal.payload.get('msg')}",
            GoalPriority.CRITICAL
        )

        # 4. Act
        if self.goal_manager.check_feasibility(goal):
            await self.execution.execute_goal(goal)
            self.goal_manager.complete_goal(goal.id)

# Patching
ArtificialGeneralOperator._process_signal = process_signal_logic

async def main():
    load_dotenv()
    logger = configure_logging(level="INFO")
    logger.info("Initializing AGO Genesis...")

    await db.init_models()

    # 1. Instantiate AGO
    ago = ArtificialGeneralOperator()

    # Wired Components
    ago.world_model = WorldModel()
    ago.goal_manager = GoalManager(ago.world_model)
    ago.execution = ExecutionInterface(ago.orchestrator)

    # 2. Boot
    await ago.boot()

    # 3. Inject "Security Breach" Signal
    logger.critical("INJECTING SIMULATED SECURITY BREACH...")
    await asyncio.sleep(2)
    await ago.senses.ingest(Signal("NetSec", "BREACH", {"msg": "Unauthorized Access Port 80"}, 0.9))

    # 4. Let autonomy run
    await asyncio.sleep(10)

    await ago.shutdown()

if __name__ == "__main__":
    asyncio.run(main())
