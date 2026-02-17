from typing import List, Dict, Any
import networkx as nx
import structlog
from ..core.types import Task
from ..core.interfaces import LLMInterface

logger = structlog.get_logger()

class HierarchicalTaskPlanner:
    """
    Decomposes high-level objectives into a DAG (Directed Acyclic Graph) of subtasks.
    Uses LLM to generate the graph structure.
    """
    def __init__(self, llm: LLMInterface):
        self.llm = llm
        self.logger = logger.bind(component="HierarchicalPlanner")

    async def decompose(self, main_task: Task) -> nx.DiGraph:
        self.logger.info("Decomposing task", task=main_task.description)

        prompt = f"""
        You are a Master Architect.
        Objective: {main_task.description}
        Requirements: {main_task.requirements}

        Output a dependency graph of subtasks in JSON format:
        {{
            "nodes": [
                {{"id": "task_1", "description": "...", "role": "PLANNER"}},
                {{"id": "task_2", "description": "...", "role": "ENGINEER"}}
            ],
            "edges": [
                {{"source": "task_1", "target": "task_2"}}
            ]
        }}
        """

        response = await self.llm.generate(prompt)
        # Simplify parsing for MVP
        try:
            import json
            # Extract JSON from potential markdown blocks
            clean_json = response.strip().replace("```json", "").replace("```", "")
            data = json.loads(clean_json)

            graph = nx.DiGraph()
            for node in data["nodes"]:
                graph.add_node(node["id"], description=node["description"], role=node["role"])

            for edge in data["edges"]:
                graph.add_edge(edge["source"], edge["target"])

            self.logger.info("Task DAG generated", nodes=len(graph.nodes), edges=len(graph.edges))
            return graph
        except Exception as e:
            self.logger.error("Failed to parse DAG", error=str(e), response=response)
            # Fallback: Single node graph
            g = nx.DiGraph()
            g.add_node("root", description=main_task.description, role="PLANNER")
            return g
