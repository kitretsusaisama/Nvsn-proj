import asyncio
import random
from ..infra.mesh import mesh
from ..core.actor import Actor, Message
from ..agents.omni import OmniAgent

class ChaosMonkey(Actor):
    """
    Randomly kills actors to test system resilience.
    """
    def __init__(self):
        super().__init__("CHAOS_MONKEY")

    async def start(self):
        await super().start()
        asyncio.create_task(self._wreak_havoc())

    async def _wreak_havoc(self):
        while self._running:
            await asyncio.sleep(5) # Every 5 seconds

            # Pick a victim
            victims = [aid for aid in mesh._actors.keys() if aid != self.id and aid != "GOD_VIEW"]
            if victims:
                victim_id = random.choice(victims)
                self.logger.critical("Killing Actor", victim=victim_id)

                # Kill it
                actor = mesh.get_actor(victim_id)
                if actor:
                    await actor.stop()
                    mesh.deregister(victim_id)

                    # Broadcast death event
                    await mesh.broadcast(self.id, {"victim": victim_id}, "ACTOR_KILLED")

class Resurrector(Actor):
    """
    Watches for dead actors and respawns them.
    """
    def __init__(self):
        super().__init__("RESURRECTOR")

    async def handle_message(self, message: Message):
        if message.type == "ACTOR_KILLED":
            victim_id = message.payload.get("victim")
            self.logger.warning("Detected Death. Resurrecting...", victim=victim_id)
            await asyncio.sleep(1)

            # Respawn logic
            new_agent = OmniAgent(victim_id, role="Resurrected_Worker")
            mesh.register(new_agent)
            await new_agent.start()
            self.logger.info("Resurrection Complete", agent=victim_id)
