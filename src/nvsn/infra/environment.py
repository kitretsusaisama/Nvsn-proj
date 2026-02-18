from typing import Dict, Tuple
import math
import structlog

logger = structlog.get_logger()

class VirtualEnvironment:
    """
    The Construct: A 2D spatial plane where agents exist.
    Communication latency is proportional to distance.
    """
    def __init__(self, width=100, height=100):
        self.width = width
        self.height = height
        self.positions: Dict[str, Tuple[float, float]] = {}
        self.logger = logger.bind(component="TheConstruct")

    def spawn(self, agent_id: str, x: float, y: float):
        self.positions[agent_id] = (x, y)
        self.logger.info("Agent Spawned in Construct", agent_id=agent_id, location=(x, y))

    def move(self, agent_id: str, dx: float, dy: float):
        if agent_id in self.positions:
            cx, cy = self.positions[agent_id]
            nx, ny = max(0, min(self.width, cx + dx)), max(0, min(self.height, cy + dy))
            self.positions[agent_id] = (nx, ny)

    def calculate_latency(self, agent_a: str, agent_b: str) -> float:
        if agent_a not in self.positions or agent_b not in self.positions:
            return 0.0

        pos_a = self.positions[agent_a]
        pos_b = self.positions[agent_b]
        distance = math.sqrt((pos_a[0] - pos_b[0])**2 + (pos_a[1] - pos_b[1])**2)

        # 1 unit distance = 1ms latency
        return distance * 0.001

# Global Construct
construct = VirtualEnvironment()
