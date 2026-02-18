import asyncio
import structlog
from typing import Dict, Any, Optional
from ..core.actor import Actor, Message

logger = structlog.get_logger()

class ServiceMesh:
    """
    Global Actor Registry and Router.
    """
    def __init__(self):
        self._actors: Dict[str, Actor] = {}
        self.logger = logger.bind(component="ServiceMesh")

    def register(self, actor: Actor):
        if actor.id in self._actors:
            self.logger.warning("Actor already registered", actor_id=actor.id)
            return
        self._actors[actor.id] = actor
        self.logger.info("Actor Registered", actor_id=actor.id)

    def deregister(self, actor_id: str):
        if actor_id in self._actors:
            del self._actors[actor_id]
            self.logger.info("Actor Deregistered", actor_id=actor_id)

    def get_actor(self, actor_id: str) -> Optional[Actor]:
        return self._actors.get(actor_id)

    async def send_message(self, message: Message):
        receiver = self._actors.get(message.receiver)
        if receiver:
            await receiver.inbox.put(message)
        else:
            self.logger.warning("Message Dropped: Receiver not found", receiver=message.receiver)

    async def broadcast(self, sender_id: str, payload: Any, msg_type: str = "BROADCAST"):
        for actor_id, actor in self._actors.items():
            if actor_id != sender_id:
                await actor.inbox.put(Message(sender_id, actor_id, payload, msg_type))

# Singleton Mesh
mesh = ServiceMesh()
