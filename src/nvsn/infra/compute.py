import asyncio
import concurrent.futures
import structlog
import multiprocessing
from typing import Callable, Any, TypeVar

logger = structlog.get_logger()

T = TypeVar("T")

class ComputeCluster:
    """
    Manages a pool of worker processes for CPU-intensive tasks.
    Offloads heavy tensor math and simulations from the main event loop.
    """
    def __init__(self, max_workers: int = None):
        self.max_workers = max_workers or multiprocessing.cpu_count()
        self.executor = concurrent.futures.ProcessPoolExecutor(max_workers=self.max_workers)
        self.logger = logger.bind(component="ComputeCluster", workers=self.max_workers)
        self.logger.info("Compute Cluster Initialized")

    async def submit(self, func: Callable[..., T], *args, **kwargs) -> T:
        """
        Run a blocking function in the process pool.
        Note: The function and its arguments must be picklable.
        """
        loop = asyncio.get_running_loop()

        self.logger.debug("Offloading task to compute cluster", func=func.__name__)
        try:
            # functools.partial is picklable, lambda is not.
            import functools
            call = functools.partial(func, *args, **kwargs)
            return await loop.run_in_executor(self.executor, call)
        except Exception as e:
            self.logger.error("Compute task failed", error=str(e))
            raise e

    def shutdown(self):
        self.executor.shutdown(wait=True)

# Global Compute Singleton
compute = ComputeCluster()
