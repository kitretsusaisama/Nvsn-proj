import asyncio
import sys
import os
import structlog
from dotenv import load_dotenv

# Ensure src is in python path
sys.path.append(os.path.join(os.path.dirname(__file__), '../src'))

from nvsn.orchestrator.core import Orchestrator
from nvsn.teams.workflow import create_software_team
from nvsn.agents.llm import MockLLM
from nvsn.agents.gemini_llm import GeminiLLM
from nvsn.memory.local import LocalVectorMemory
from nvsn.utils.logging import configure_logging
from nvsn.config import settings

async def main():
    # Load environment variables
    load_dotenv()

    # 1. Setup Logging
    logger = configure_logging(level=settings.log_level)
    logger.info("Starting NvsN Framework Demo (Gemini Edition)")

    # 2. Initialize Infrastructure
    # Try to use Gemini if key is present, otherwise fallback to Mock
    api_key = settings.google_api_key or os.getenv("GOOGLE_API_KEY")

    if api_key:
        logger.info("Gemini API Key found. Using Google Generative AI.")
        try:
            llm = GeminiLLM(api_key=api_key)
            # Simple test to verify connection
            # await llm.generate("Hello")
        except Exception as e:
            logger.error("Failed to initialize Gemini", error=str(e))
            llm = MockLLM()
    else:
        logger.warning("No Google API Key found. Falling back to MockLLM.")
        llm = MockLLM()

    memory = LocalVectorMemory()
    # Communication interface is implicit in direct calls for now or could be a simple InMemoryBus
    communication = None

    # 3. Initialize Orchestrator
    orchestrator = Orchestrator(llm=llm)

    # 4. Create Teams
    team_alpha = create_software_team("Team_Alpha", llm, memory, communication)
    team_beta = create_software_team("Team_Beta", llm, memory, communication)

    # 5. Register Teams
    await orchestrator.register_team(team_alpha)
    await orchestrator.register_team(team_beta)

    # 6. Define a Task
    # Simplified task for demo speed if using real LLM
    task_description = "Write a Python function to check if a string is a palindrome."
    task_requirements = ["Handle case sensitivity", "Ignore spaces", "Add docstring"]

    # 7. Submit Task for Competition
    task_id = await orchestrator.submit_task(task_description, task_requirements)

    # 8. Run Competition
    logger.info("Initiating Competition between Alpha and Beta...")
    try:
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
            print(f"\n[{team} Output]:\n{output[:500]}...") # Truncate for display
        print("="*50 + "\n")

    except Exception as e:
        logger.error("Competition failed", error=str(e))

if __name__ == "__main__":
    asyncio.run(main())
