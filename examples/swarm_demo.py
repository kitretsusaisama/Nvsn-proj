import asyncio
import sys
import os
import random
from rich.live import Live
from rich.layout import Layout
from rich.panel import Panel
from rich.table import Table
from rich.tree import Tree

sys.path.append(os.path.join(os.path.dirname(__file__), '../src'))

from nvsn.infra.mesh import mesh
from nvsn.infra.environment import construct
from nvsn.agents.fractal import FractalAgent
from nvsn.core.language import elp
from nvsn.core.dreamer import Dreamer
from nvsn.memory.graph import KnowledgeGraphMemory
from nvsn.infra.database import db

# Shared State for Visualization
agent_tree = Tree("Swarm Queen")

class SwarmDemo:
    def __init__(self):
        self.kg = KnowledgeGraphMemory()
        self.dreamer = Dreamer(self.kg)
        self.logs = []

    def get_renderable(self):
        layout = Layout()
        layout.split_row(
            Layout(name="tree", ratio=1),
            Layout(name="stats", ratio=1)
        )

        # Build Tree View from Fractal State
        # In a real app we'd traverse the mesh relations.
        # Here we rely on the live `agent_tree` object being updated by the script.

        stats = Table(title="Swarm Telemetry")
        stats.add_column("Metric", style="cyan")
        stats.add_column("Value", style="magenta")
        stats.add_row("Active Agents", str(len(mesh._actors)))
        stats.add_row("Language Terms", str(len(elp.dictionary)))
        stats.add_row("Knowledge Facts", str(len(self.kg.graph.edges)))

        layout["tree"].update(Panel(agent_tree, title="Fractal Hierarchy"))
        layout["stats"].update(Panel(stats, title="Collective Consciousness"))
        return layout

async def main():
    await db.init_models()

    demo = SwarmDemo()
    await demo.dreamer.start()

    # 1. Spawn Queen
    queen = FractalAgent("Queen", depth=0)
    mesh.register(queen)
    construct.spawn("Queen", 50, 50)
    await queen.start()

    # 2. Emergent Language Init
    elp.propose_term("Requesting massive computation resources")

    # 3. Live Loop
    with Live(demo.get_renderable(), refresh_per_second=4) as live:
        # Trigger Fractal Mitosis
        task = {"complexity": 4, "data": "Map the Universe"}
        # Manually triggering internal mitosis logic for demo visual
        # Ideally this happens via message passing, but we want to update the Tree object

        # Simulate recursion visualization
        node_lvl_1 = agent_tree.add("General_1")
        node_lvl_1.add("Worker_1_A")
        node_lvl_1.add("Worker_1_B")

        node_lvl_2 = agent_tree.add("General_2")
        sub = node_lvl_2.add("Worker_2_A")
        sub.add("SubWorker_2_A_1")

        for _ in range(10):
            # Update stats
            live.update(demo.get_renderable())

            # Simulate work
            if random.random() > 0.7:
                term = elp.propose_term(f"Observation_{random.randint(100,999)}")

            await asyncio.sleep(0.5)

    # Cleanup
    await queen.stop()

if __name__ == "__main__":
    asyncio.run(main())
