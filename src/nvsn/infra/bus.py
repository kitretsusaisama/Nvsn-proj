import asyncio
from typing import Dict, Any, Callable, Optional
import structlog
import json

logger = structlog.get_logger()

class MessageBus:
    """
    Simulates a Redis-backed Message Bus.
    In production, this would wrap `redis-py` Pub/Sub.
    """
    def __init__(self):
        self._channels: Dict[str, asyncio.Queue] = {}
        self._handlers: Dict[str, list[Callable]] = {}
        self.logger = logger.bind(component="MessageBus")

    async def subscribe(self, channel: str, handler: Callable):
        if channel not in self._handlers:
            self._handlers[channel] = []
        self._handlers[channel].append(handler)
        self.logger.info("Subscribed to channel", channel=channel)

    async def publish(self, channel: str, message: Dict[str, Any]):
        """
        Publish a message to a channel.
        """
        # In a real Redis impl, this would strictly publish.
        # Here we also trigger handlers immediately for the simulation.
        self.logger.debug("Publishing message", channel=channel, type=message.get("type"))

        if channel in self._handlers:
            for handler in self._handlers[channel]:
                try:
                    # Execute handlers asynchronously
                    asyncio.create_task(handler(message))
                except Exception as e:
                    self.logger.error("Error in handler", channel=channel, error=str(e))

    async def push_task(self, queue_name: str, task_data: Dict[str, Any]):
        """
        Simulate pushing to a Redis List (LPUSH).
        """
        if queue_name not in self._channels:
            self._channels[queue_name] = asyncio.Queue()
        await self._channels[queue_name].put(task_data)
        self.logger.info("Task pushed to queue", queue=queue_name, task_id=task_data.get("id"))

    async def pop_task(self, queue_name: str, timeout: int = 5) -> Optional[Dict[str, Any]]:
        """
        Simulate popping from a Redis List (BRPOP).
        """
        if queue_name not in self._channels:
            return None

        try:
            return await asyncio.wait_for(self._channels[queue_name].get(), timeout=timeout)
        except asyncio.TimeoutError:
            return None

# Singleton
bus = MessageBus()
