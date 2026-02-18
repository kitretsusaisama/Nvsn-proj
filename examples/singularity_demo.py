import asyncio
import sys
import os
import structlog
from dotenv import load_dotenv

# Ensure src is in python path
sys.path.append(os.path.join(os.path.dirname(__file__), '../src'))

from nvsn.orchestrator.core_v2 import OrchestratorV2
from nvsn.orchestrator.tensor_state import GlobalStateTensor
from nvsn.orchestrator.scheduler_bayes import ProbabilisticScheduler
from nvsn.teams.workflow_v3 import create_super_team
from nvsn.agents.llm import MockLLM
from nvsn.agents.gemini_llm import GeminiLLM
from nvsn.memory.graph import KnowledgeGraphMemory
from nvsn.utils.logging import configure_logging
from nvsn.config import settings
from nvsn.infra.database import db

async def main():
    load_dotenv()
    logger = configure_logging(level="INFO")
    logger.info("Starting NvsN V4 (Singularity Grade) Framework")

    await db.init_models()

    api_key = settings.google_api_key or os.getenv("GOOGLE_API_KEY")
    if api_key:
        llm = GeminiLLM(api_key=api_key, model_name="gemini-1.5-pro")
    else:
        logger.warning("Using Mock LLM")
        llm = MockLLM()

    # 1. Initialize Galactic Components
    kg_memory = KnowledgeGraphMemory()
    tensor_state = GlobalStateTensor(max_agents=50)
    scheduler = ProbabilisticScheduler()
    orchestrator = OrchestratorV2(llm=llm)

    # 2. Spin up Super Intelligent Teams
    team_alpha = create_super_team("Team_Singularity_Alpha", llm, kg_memory, None)
    await orchestrator.register_team(team_alpha)

    # 3. Simulate War Room Scenario
    logger.critical("ALERT: SYSTEM ANOMALY DETECTED. DATABASE LATENCY > 5000ms")

    # Inject chaotic knowledge
    kg_memory.add_fact("Database", "status", "Critical")
    kg_memory.add_fact("Database", "dependency", "AuthService")

    # 4. Super Agent Response
    logger.info("Deploying Super Intelligent Agents...")

    task_id = await orchestrator.submit_task(
        "Diagnose and Patch Database Outage. Use Knowledge Graph for root cause analysis."
    )

    try:
        # Simulate Tensor updates during execution
        # Fix: team_alpha.agents is a dict {id: agent}, convert to list to index
        first_agent = list(team_alpha.agents.values())[0]
        tensor_state.update(first_agent.id, load=0.9, health=0.5, memory=0.8) # Anomaly!

        anomalies = tensor_state.detect_anomalies()
        if anomalies:
            logger.warning("Orchestrator detected anomalies via Tensor State", agents=anomalies)

        results = await orchestrator.run_competition(task_id, [team_alpha.id])

        print("\n" + "="*60)
        print("SINGULARITY RESPONSE")
        print("="*60)
        for team, output in results.get("team_outputs", {}).items():
            print(f"\n[{team} Optimized Future Path & Output]:\n{output[:1000]}...")
        print("="*60 + "\n")

    except Exception as e:
        logger.error("Singularity Failed", error=str(e))

if __name__ == "__main__":
    asyncio.run(main())
