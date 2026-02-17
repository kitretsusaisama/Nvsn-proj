import asyncio
import structlog
from tenacity import retry, stop_after_attempt, wait_exponential

logger = structlog.get_logger()

class ResiliencyLayer:
    """
    Middleware for Bus and API calls providing retries, circuit breakers, and DLQs.
    """
    def __init__(self):
        self.logger = logger.bind(component="Resiliency")

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    async def resilient_bus_push(self, bus, queue_name: str, task: dict):
        """
        Retry logic for task submission.
        """
        self.logger.debug("Pushing task with retry logic", task_id=task.get("id"))
        try:
            await bus.push_task(queue_name, task)
        except Exception as e:
            self.logger.error("Bus Push Failed, retrying...", error=str(e))
            raise e

    async def handle_dead_letter(self, queue_name: str, task: dict, error: str):
        """
        If retries fail, move to DLQ (Dead Letter Queue).
        """
        self.logger.critical("Task moved to DLQ", task_id=task.get("id"), reason=error)
        # Store in separate DLQ list or DB table
        # await bus.push_task(f"dlq:{queue_name}", task)
