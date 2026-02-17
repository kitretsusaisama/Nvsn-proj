import asyncio
import sys
import os

# Ensure src is in python path
sys.path.append(os.path.join(os.path.dirname(__file__), '../src'))

from nvsn.orchestrator.core import Orchestrator
from nvsn.teams.workflow import create_software_team
from nvsn.agents.llm import MockLLM
from nvsn.memory.local import LocalVectorMemory
from nvsn.utils.logging import configure_logging

async def main():
    # 1. Setup Logging
    logger = configure_logging(level="INFO")
    logger.info("Starting NvsN Framework Demo")

    # 2. Initialize Infrastructure (Mock)
    llm = MockLLM()
    memory = LocalVectorMemory()
    # Communication interface is implicit in direct calls for now or could be a simple InMemoryBus
    communication = None # Not strictly needed for this simple demo as agents call direct methods

    # 3. Initialize Orchestrator
    orchestrator = Orchestrator(llm=llm)

    # 4. Create Teams
    team_alpha = create_software_team("Team_Alpha", llm, memory, communication)
    team_beta = create_software_team("Team_Beta", llm, memory, communication)

    # 5. Register Teams
    await orchestrator.register_team(team_alpha)
    await orchestrator.register_team(team_beta)

    # 6. Define a Task
    task_description = "Build a Python script that calculates the Fibonacci sequence up to N terms."
    task_requirements = ["Must be efficient", "Include error handling", "Add comments"]

    # 7. Submit Task for Competition
    task_id = await orchestrator.submit_task(task_description, task_requirements)

    # 8. Run Competition
    logger.info("Initiating Competition between Alpha and Beta...")
    results = await orchestrator.run_competition(task_id, [team_alpha.id, team_beta.id])

    # 9. Output Results
    print("\n" + "="*50)
    print("COMPETITION RESULTS")
    print("="*50)
    print(f"Winner: {results.get('winner')}")
    print(f"Scores: {results.get('scores')}")
    print(f"Reasoning: {results.get('reasoning')}")
    print("-" * 50)
    for team, output in results.get("team_outputs", {}).items():
        print(f"\n[{team} Output]:\n{output[:200]}...") # Truncate for display
    print("="*50 + "\n")

if __name__ == "__main__":
    asyncio.run(main())
