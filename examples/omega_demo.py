import asyncio
import sys
import os
import uvicorn
import structlog
from multiprocessing import Process

sys.path.append(os.path.join(os.path.dirname(__file__), '../src'))

from nvsn.dashboard.server import app, stream_events_to_dashboard
from nvsn.orchestrator.scaler import PredictiveScaler
from nvsn.orchestrator.tensor_state import GlobalStateTensor
from nvsn.core.evolution import EvolutionaryEngine
from nvsn.core.store import store
from nvsn.infra.mesh import mesh
from nvsn.agents.omni import OmniAgent

logger = structlog.get_logger()

def start_server():
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="error")

async def omega_loop():
    logger.info("Initializing Omega Framework V8...")

    # 1. Start Evolution
    evo = EvolutionaryEngine()
    evo.evolve()

    # 2. Start Predictive Scaling
    tensor = GlobalStateTensor()
    scaler = PredictiveScaler(tensor)
    asyncio.create_task(scaler.run_loop())

    # 3. Agents writing code for the Store
    coder = OmniAgent("Coder_Zero", "Architect")
    mesh.register(coder)
    await coder.start()

    new_capability = """
class QuantumOptimizer:
    def optimize(self):
        return "Quantum State Optimized"
"""
    store.publish("QuantumOptimizer", new_capability, coder.id)

    # 4. Verify Usage
    OptClass = store.retrieve("QuantumOptimizer")
    if OptClass:
        instance = OptClass()
        logger.info("Capability Executed", result=instance.optimize())

    logger.info("System Running. Access Dashboard at http://localhost:8000")

    # Keep alive for a bit to show scaling
    await asyncio.sleep(5)

async def main():
    # Start Web Server in background thread/process
    # For this demo script, we'll run logic then hold
    server_process = Process(target=start_server)
    server_process.start()

    try:
        await omega_loop()
        # Keep alive for user to potentially curl
        await asyncio.sleep(5)
    finally:
        server_process.terminate()

if __name__ == "__main__":
    asyncio.run(main())
