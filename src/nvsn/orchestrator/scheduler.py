import asyncio
from typing import Dict, List, Any, Callable
from ..core.types import Task, TaskStatus

class TaskScheduler:
    """
    Manages task execution and scheduling.
    """
    def __init__(self):
        self.task_queue = asyncio.Queue()
        self.active_tasks: Dict[str, Task] = {}

    async def add_task(self, task: Task):
        task.status = TaskStatus.PENDING
        await self.task_queue.put(task)
        self.active_tasks[str(task.id)] = task

    async def get_next_task(self) -> Task:
        return await self.task_queue.get()

    def complete_task(self, task_id: str, result: Any):
        if task_id in self.active_tasks:
            task = self.active_tasks[task_id]
            task.status = TaskStatus.COMPLETED
            task.result = result
            # Ideally store in persistent DB here
