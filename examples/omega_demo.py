import asyncio
import sys
import os
import uvicorn
import structlog
from multiprocessing import Process

sys.path.append(os.path.join(os.path.dirname(__file__), '../src'))

from nvsn.dashboard.server import app, stream_events_to_dashboard, manager
from nvsn.orchestrator.scaler import PredictiveScaler
from nvsn.orchestrator.tensor_state import GlobalStateTensor
from nvsn.core.evolution import EvolutionaryEngine
from nvsn.core.store import store
from nvsn.infra.mesh import mesh
from nvsn.agents.omni import OmniAgent

logger = structlog.get_logger()

# Shared queue for IPC between processes (Demo hack for WebSocket)
# In real life, use Redis Pub/Sub
msg_queue = None

def start_server(queue):
    # Patch manager to read from queue
    async def queue_reader():
        while True:
            if not queue.empty():
                msg = queue.get()
                await manager.broadcast(msg)
            await asyncio.sleep(0.1)

    @app.on_event("startup")
    async def startup():
        asyncio.create_task(queue_reader())

    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="error")

async def omega_loop(queue):
    logger.info("Initializing Omega Framework V8...")

    # Send test log
    queue.put({"type": "LOG", "content": "Omega Framework Initialized", "level": "success"})

    # 1. Start Evolution
    evo = EvolutionaryEngine()
    evo.evolve()
    queue.put({"type": "LOG", "content": "Evolution Step Complete", "level": "info"})

    # 2. Start Predictive Scaling
    tensor = GlobalStateTensor()
    scaler = PredictiveScaler(tensor)
    asyncio.create_task(scaler.run_loop())

    # 3. Agents writing code for the Store
    coder = OmniAgent("Coder_Zero", "Architect")
    mesh.register(coder)
    await coder.start()
    queue.put({"type": "TOPOLOGY", "action": "add_node", "id": "Coder_Zero", "label": "Architect"})

    new_capability = """
class QuantumOptimizer:
    def optimize(self):
        return "Quantum State Optimized"
"""
    store.publish("QuantumOptimizer", new_capability, coder.id)
    queue.put({"type": "LOG", "content": "New Capability Published: QuantumOptimizer", "level": "success"})

    # 4. Verify Usage
    OptClass = store.retrieve("QuantumOptimizer")
    if OptClass:
        instance = OptClass()
        result = instance.optimize()
        logger.info("Capability Executed", result=result)
        queue.put({"type": "LOG", "content": f"Capability Executed: {result}", "level": "info"})

    logger.info("System Running. Access Dashboard at http://localhost:8000")

    # Keep alive for a bit to show scaling
    await asyncio.sleep(5)

async def main():
    from multiprocessing import Queue
    queue = Queue()

    # Start Web Server in background thread/process
    server_process = Process(target=start_server, args=(queue,))
    server_process.start()

    try:
        await omega_loop(queue)
        # Keep alive for user to potentially curl
        await asyncio.sleep(5)
    finally:
        server_process.terminate()

if __name__ == "__main__":
    asyncio.run(main())
