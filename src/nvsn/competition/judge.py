from ..core.interfaces import LLMInterface
from ..core.types import Task, TaskResult
from typing import Dict, Any, List
import structlog
import json

logger = structlog.get_logger()

class CompetitionJudge:
    """
    Evaluates task outputs from multiple teams using an LLM.
    """
    def __init__(self, llm: LLMInterface):
        self.llm = llm
        self.logger = logger.bind(component="Judge")

    async def evaluate(self, task: Task, results: Dict[str, TaskResult]) -> Dict[str, Any]:
        """
        Compare results and declare a winner.
        """
        self.logger.info("Evaluating competition", task_id=str(task.id), team_count=len(results))

        # Prepare prompt for LLM judge
        teams_outputs = ""
        for team_name, result in results.items():
            teams_outputs += f"\n--- Team: {team_name} ---\n{result.output}\n"

        prompt = f"""
        You are an impartial Judge in an AI competition.
        Task: {task.description}
        Requirements: {task.requirements}

        Evaluate the following submissions based on:
        1. Correctness
        2. Efficiency
        3. Code Quality
        4. Innovation

        Submissions:
        {teams_outputs}

        Output format (JSON):
        {{
            "scores": {{ "TeamName": score_0_to_100, ... }},
            "winner": "TeamName",
            "reasoning": "Explanation..."
        }}
        """

        try:
            response = await self.llm.generate(prompt)
            # Basic parsing, might need more robust JSON extraction in prod
            start = response.find('{')
            end = response.rfind('}') + 1
            if start != -1 and end != -1:
                json_str = response[start:end]
                evaluation = json.loads(json_str)
            else:
                # Fallback if LLM doesn't output valid JSON
                self.logger.warning("Judge LLM did not return JSON", response=response)
                evaluation = {"error": "Invalid judge output", "raw": response}

            return evaluation

        except Exception as e:
            self.logger.error("Evaluation failed", error=str(e))
            return {"error": str(e)}
