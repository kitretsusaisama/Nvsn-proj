import asyncio
import sys
import os
import structlog
import numpy as np
from dotenv import load_dotenv

sys.path.append(os.path.join(os.path.dirname(__file__), '../src'))

from nvsn.orchestrator.scheduler_dqn import NeuralScheduler
from nvsn.core.kernel import kernel, HotSwapper
from nvsn.infra.compute import compute
from nvsn.utils.logging import configure_logging
from nvsn.core.types import Task, AgentState, AgentRole

def heavy_computation(x):
    # Simulate CPU intensive task
    return sum([i**2 for i in range(x)])

async def main():
    load_dotenv()
    logger = configure_logging(level="INFO")
    logger.info("Starting NvsN V5 (Hyper-Advanced) Framework")

    # 1. Initialize Compute Cluster
    logger.info("Booting Compute Cluster...")
    # Offload a heavy task to verify process pool
    result = await compute.submit(heavy_computation, 1000000)
    logger.info("Compute Cluster Verified", result=result)

    # 2. Initialize Neural Orchestrator
    scheduler = NeuralScheduler(num_agents=3, state_dim=4)
    logger.info("Neural Scheduler Online (DQN Initialized)")

    # 3. Simulate Training Loop
    logger.info("Training Neural Scheduler...")
    for episode in range(5):
        # Mock State: [Diff, Load, Health, Time]
        state = np.array([0.5, 0.1 * episode, 1.0, 0.5], dtype=np.float32)

        # Select Action
        action = scheduler.select_action(state, ["Agent_1", "Agent_2", "Agent_3"])

        # Simulate Result
        reward = 1.0 if action == 0 else -0.1 # Fake reward function favoring Agent 0
        next_state = state + 0.1
        done = False

        # Store & Optimize
        scheduler.store_experience(state, action, reward, next_state, done)
        loss = scheduler.optimize_model()
        if loss:
            logger.info("DQN Training Step", episode=episode, loss=f"{loss:.4f}")

    # 4. Self-Evolution (Hot-Swapping)
    swapper = HotSwapper(kernel)

    # Agent "writes" a new tool
    new_tool_code = """
class OptimizationTool:
    def run(self):
        return "System Optimized by 10000x"
"""
    logger.info("Agent generated patch for Self-Evolution...")
    await swapper.apply_patch("optimizer", new_tool_code)

    # Verify Hot-Swap
    ToolClass = kernel.get_class("nvsn.dynamic.nvsn.dynamic.optimizer", "OptimizationTool")
    # Due to dynamic loading logic naming might be nested, checking simple match
    if not ToolClass:
         # Try direct module name from load call
         ToolClass = kernel.get_class("nvsn.dynamic.optimizer", "OptimizationTool")

    if ToolClass:
        tool_instance = ToolClass()
        logger.info("Hot-Swapped Tool Executed", output=tool_instance.run())
    else:
        logger.error("Failed to load hot-swapped tool")

    # Cleanup
    compute.shutdown()
    logger.info("System Shutdown Complete")

if __name__ == "__main__":
    asyncio.run(main())
