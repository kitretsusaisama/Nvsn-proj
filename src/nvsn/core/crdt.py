import structlog
from typing import List, Tuple

logger = structlog.get_logger()

class SequenceCRDT:
    """
    Conflict-Free Replicated Data Type for real-time collaborative text editing.
    Uses a simplified RGA (Replicated Growable Array) algorithm.
    """
    def __init__(self, site_id: str):
        self.site_id = site_id
        # List of (char, site_id, timestamp)
        self.buffer: List[Tuple[str, str, int]] = []
        self.clock = 0
        self.logger = logger.bind(component="CRDT", site=site_id)

    def local_insert(self, index: int, char: str):
        """
        User types a character locally.
        """
        self.clock += 1
        op = (char, self.site_id, self.clock)
        self.buffer.insert(index, op)
        return {"op": "insert", "idx": index, "char": char, "site": self.site_id, "clk": self.clock}

    def remote_insert(self, op: dict):
        """
        Handle insertion from another agent.
        """
        # Simplified: We trust the index for this demo (assuming causal order delivery via Mesh)
        # Real CRDTs need complex ID handling.
        char = op["char"]
        idx = op["idx"]

        if idx > len(self.buffer):
            idx = len(self.buffer)

        self.buffer.insert(idx, (char, op["site"], op["clk"]))
        self.logger.debug("Remote Insert Applied", content=self.get_text())

    def get_text(self) -> str:
        return "".join([c[0] for c in self.buffer])
