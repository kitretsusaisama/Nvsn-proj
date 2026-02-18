import asyncio
import sys
import os
import random
from rich.live import Live
from rich.layout import Layout
from rich.panel import Panel
from rich.table import Table
from rich.console import Console

sys.path.append(os.path.join(os.path.dirname(__file__), '../src'))

from nvsn.infra.mesh import mesh
from nvsn.agents.omni import OmniAgent
from nvsn.core.chaos import ChaosMonkey, Resurrector
from nvsn.core.actor import Actor, Message

class GodModeObserver(Actor):
    def __init__(self):
        super().__init__("GOD_VIEW")
        self.logs = []
        self.active_actors = set()

    async def handle_message(self, message: Message):
        if message.type == "ACTOR_KILLED":
            victim = message.payload.get("victim")
            self.logs.append(f"[red]💀 Killed: {victim}[/]")
            if victim in self.active_actors:
                self.active_actors.remove(victim)

        elif message.type == "AGENT_STATUS":
            self.logs.append(f"[green]🤖 {message.sender}: {message.payload['result']}[/]")
            self.active_actors.add(message.sender)

def generate_layout(observer):
    layout = Layout()

    # Actors Table
    table = Table(title="Planetary Actor Mesh")
    table.add_column("Actor ID", style="cyan")
    table.add_column("Status", style="green")

    for actor_id in list(observer.active_actors): # Snapshot
        table.add_row(actor_id[:8], "ONLINE")

    # Logs
    log_content = "\n".join(observer.logs[-10:])

    layout.split_column(
        Layout(name="upper"),
        Layout(name="lower")
    )
    layout["upper"].update(Panel(table))
    layout["lower"].update(Panel(log_content, title="System Event Log"))

    return layout

async def main():
    # 1. Start Mesh
    observer = GodModeObserver()
    mesh.register(observer)
    await observer.start()

    chaos = ChaosMonkey()
    mesh.register(chaos)
    await chaos.start()

    resurrector = Resurrector()
    mesh.register(resurrector)
    await resurrector.start()

    # 2. Spawn Agents
    agents = []
    for i in range(3):
        a = OmniAgent(f"Worker_{i}", "Coder")
        mesh.register(a)
        await a.start()
        agents.append(a)
        observer.active_actors.add(a.id)

    # 3. UI Loop
    with Live(generate_layout(observer), refresh_per_second=4) as live:
        for _ in range(20): # Run for 20 "ticks" (~5-10 seconds)
            # Simulate work
            target = random.choice(agents)
            await target.inbox.put(Message("User", target.id, "Analyze system architecture", "TASK_TEXT"))

            live.update(generate_layout(observer))
            await asyncio.sleep(0.5)

    # Cleanup
    for a in agents: await a.stop()
    await chaos.stop()
    await resurrector.stop()
    await observer.stop()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
