import asyncio
import uuid
import structlog
from typing import Any, Dict, Optional, Callable

logger = structlog.get_logger()

class Message:
    def __init__(self, sender: str, receiver: str, payload: Any, msg_type: str = "DATA"):
        self.id = str(uuid.uuid4())
        self.sender = sender
        self.receiver = receiver
        self.payload = payload
        self.type = msg_type

class Actor:
    """
    Base Actor class for the Mesh architecture.
    """
    def __init__(self, actor_id: str = None):
        self.id = actor_id or str(uuid.uuid4())
        self.inbox = asyncio.Queue()
        self.logger = logger.bind(actor_id=self.id, type="Actor")
        self._running = False
        self._task = None

    async def start(self):
        self._running = True
        self.logger.info("Actor Started")
        self._task = asyncio.create_task(self._process_inbox())

    async def stop(self):
        self._running = False
        if self._task:
            self._task.cancel()
        self.logger.info("Actor Stopped")

    async def _process_inbox(self):
        while self._running:
            try:
                message = await self.inbox.get()
                await self.handle_message(message)
                self.inbox.task_done()
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error("Error processing message", error=str(e))

    async def handle_message(self, message: Message):
        """Override this"""
        self.logger.info("Received message", sender=message.sender, type=message.type)

    async def send(self, receiver_id: str, payload: Any):
        """Send message via Mesh (Registry needed)"""
        from ..infra.mesh import mesh
        await mesh.send_message(Message(self.id, receiver_id, payload))
