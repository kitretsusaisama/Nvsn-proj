from ..core.interfaces import TeamInterface
from ..core.types import Task, TaskResult
from .judge import CompetitionJudge
from typing import Dict, Any, List
import structlog
import asyncio

logger = structlog.get_logger()

class CompetitionArena:
    """
    Manages the competitive execution of tasks between teams.
    """
    def __init__(self, judge: CompetitionJudge):
        self.judge = judge
        self.logger = logger.bind(component="Arena")

    async def conduct_match(self, task: Task, teams: List[TeamInterface]) -> Dict[str, Any]:
        """
        Executes a task concurrently across all participating teams.
        """
        if len(teams) < 2:
            raise ValueError("Competition requires at least 2 teams")

        self.logger.info("Match starting", teams=[t.name for t in teams], task_id=str(task.id))

        # 1. Execute tasks in parallel
        # We wrap each task execution in a separate future
        tasks = [t.assign_task(task) for t in teams]

        try:
            results = await asyncio.gather(*tasks, return_exceptions=True)
        except Exception as e:
            self.logger.error("Error during team execution", error=str(e))
            raise e

        # 2. Process results
        task_results: Dict[str, TaskResult] = {}
        successful_results: Dict[str, TaskResult] = {}

        for team, result in zip(teams, results):
            if isinstance(result, Exception):
                self.logger.error("Team failed", team=team.name, error=str(result))
                task_results[team.name] = TaskResult(
                    task_id=task.id,
                    success=False,
                    output=str(result)
                )
            else:
                self.logger.info("Team finished", team=team.name, success=result.success)
                task_results[team.name] = result
                if result.success:
                    successful_results[team.name] = result

        # 3. If no team succeeded, competition is void
        if not successful_results:
            self.logger.warning("No teams succeeded in competition")
            return {
                "winner": None,
                "scores": {},
                "reasoning": "All teams failed to complete the task.",
                "details": {t: r.output for t, r in task_results.items()}
            }

        # 4. If only one team succeeded, they win by default (or still judge quality?)
        if len(successful_results) == 1:
            winner = list(successful_results.keys())[0]
            self.logger.info("Only one team succeeded", winner=winner)
            return {
                "winner": winner,
                "scores": {winner: 100},
                "reasoning": "Only team to complete the task successfully.",
                "details": {t: r.output for t, r in task_results.items()}
            }

        # 5. Judge the successful results
        evaluation = await self.judge.evaluate(task, successful_results)

        # 6. Return final competition report
        report = {
            "task_id": str(task.id),
            "participants": [t.name for t in teams],
            "winner": evaluation.get("winner"),
            "scores": evaluation.get("scores", {}),
            "reasoning": evaluation.get("reasoning", "No reasoning provided"),
            "team_outputs": {t: r.output for t, r in task_results.items()}
        }

        self.logger.info("Match concluded", winner=report["winner"])
        return report
