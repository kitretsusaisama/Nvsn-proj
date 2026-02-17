import asyncio
import sys
import os
import structlog
from dotenv import load_dotenv

# Ensure src is in python path
sys.path.append(os.path.join(os.path.dirname(__file__), '../src'))

from nvsn.orchestrator.core_v2 import OrchestratorV2
from nvsn.teams.workflow_v2 import create_cognitive_team
from nvsn.agents.llm import MockLLM
from nvsn.agents.gemini_llm import GeminiLLM
from nvsn.memory.hybrid import HybridMemory
from nvsn.utils.logging import configure_logging
from nvsn.config import settings
from nvsn.infra.database import db

async def main():
    load_dotenv()
    logger = configure_logging(level=settings.log_level)
    logger.info("Starting NvsN V2 (Production Grade) Framework")

    # 1. Initialize Infra
    await db.init_models()

    # 2. Select LLM
    api_key = settings.google_api_key or os.getenv("GOOGLE_API_KEY")
    if api_key:
        logger.info("Using Gemini 1.5 Pro")
        llm = GeminiLLM(api_key=api_key, model_name="gemini-1.5-pro")
    else:
        logger.warning("Using Mock LLM")
        llm = MockLLM()

    # 3. Initialize Hybrid Memory (Short-term + Long-term)
    memory = HybridMemory(persist_path="./nvsn_memory_v2.json")
    communication = None

    # 4. Initialize Production Orchestrator
    orchestrator = OrchestratorV2(llm=llm)

    # 5. Create Advanced Cognitive Teams
    team_alpha = create_cognitive_team("Team_ReAct_Alpha", llm, memory, communication)
    team_beta = create_cognitive_team("Team_ReAct_Beta", llm, memory, communication)

    await orchestrator.register_team(team_alpha)
    await orchestrator.register_team(team_beta)

    # 6. Submit Complex Task
    task_description = """
    Create a Python script that scrapes the top 3 headlines from 'news.ycombinator.com'
    and saves them to a JSON file named 'news.json'.
    Ensure you use 'requests' and 'BeautifulSoup'.
    Handle network errors gracefully.
    """

    logger.info("Submitting Complex Task to Distributed Queue...")
    task_id = await orchestrator.submit_task(task_description)

    # 7. Run Competition (Triggering from Orchestrator)
    logger.info("Initiating ReAct-based Competition...")
    try:
        results = await orchestrator.run_competition(task_id, [team_alpha.id, team_beta.id])

        print("\n" + "="*60)
        print("PRODUCTION V2 RESULTS")
        print("="*60)
        print(f"Winner: {results.get('winner')}")
        print(f"Scores: {results.get('scores')}")
        print("-" * 60)
        for team, output in results.get("team_outputs", {}).items():
            print(f"\n[{team} Thought Process & Output]:\n{output[:1000]}...")
        print("="*60 + "\n")

    except Exception as e:
        logger.error("Competition failed", error=str(e))

if __name__ == "__main__":
    asyncio.run(main())
