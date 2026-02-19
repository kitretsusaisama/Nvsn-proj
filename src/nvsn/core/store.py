from typing import Dict, Any
import structlog
from ..core.kernel import kernel

logger = structlog.get_logger()

class CapabilityStore:
    """
    Registry where agents publish tools they have written.
    Other agents can query and hot-load these tools.
    """
    def __init__(self):
        self.capabilities: Dict[str, str] = {} # name -> code
        self.logger = logger.bind(component="CapabilityStore")

    def publish(self, name: str, code: str, author: str):
        self.capabilities[name] = code
        self.logger.info("New Capability Published", tool=name, author=author)

        # Immediate Hot-Load into Kernel
        kernel.load_module(f"nvsn.dynamic.{name}", code)

    def retrieve(self, name: str) -> Any:
        # Get class from kernel
        return kernel.get_class(f"nvsn.dynamic.{name}", name)

# Global Store
store = CapabilityStore()
