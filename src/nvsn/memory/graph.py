import networkx as nx
import structlog
from typing import List, Dict, Any

logger = structlog.get_logger()

class KnowledgeGraphMemory:
    """
    Semantic Memory using Graph Database.
    """
    def __init__(self):
        self.graph = nx.DiGraph()
        self.logger = logger.bind(component="KnowledgeGraph")

    def add_fact(self, subject: str, predicate: str, object: str):
        self.graph.add_edge(subject, object, relation=predicate)
        self.logger.debug("Fact Added", s=subject, p=predicate, o=object)

    def query_relation(self, subject: str, predicate: str) -> List[str]:
        if subject not in self.graph:
            return []

        results = []
        for neighbor in self.graph.neighbors(subject):
            edge_data = self.graph.get_edge_data(subject, neighbor)
            if edge_data.get("relation") == predicate:
                results.append(neighbor)
        return results

    def find_path(self, start: str, end: str):
        try:
            return nx.shortest_path(self.graph, start, end)
        except:
            return None
