import asyncio
import sys
import os
import structlog
from dotenv import load_dotenv

# Ensure src is in python path
sys.path.append(os.path.join(os.path.dirname(__file__), '../src'))

from nvsn.orchestrator.core_v2 import OrchestratorV2
from nvsn.orchestrator.planner import HierarchicalTaskPlanner
from nvsn.competition.governance import GovernanceCouncil
from nvsn.teams.workflow_v2 import create_cognitive_team
from nvsn.agents.llm import MockLLM
from nvsn.agents.gemini_llm import GeminiLLM
from nvsn.memory.hybrid import HybridMemory
from nvsn.utils.logging import configure_logging
from nvsn.config import settings
from nvsn.infra.database import db
from nvsn.core.types import Task

async def main():
    load_dotenv()
    logger = configure_logging(level="INFO")
    logger.info("Starting Enterprise-Grade NvsN Framework (V3)")

    await db.init_models()

    api_key = settings.google_api_key or os.getenv("GOOGLE_API_KEY")
    if api_key:
        llm = GeminiLLM(api_key=api_key, model_name="gemini-1.5-pro")
    else:
        logger.warning("Using Mock LLM")
        llm = MockLLM()

    # 1. Initialize Components
    memory = HybridMemory(persist_path="./nvsn_memory_enterprise.json")
    planner = HierarchicalTaskPlanner(llm)
    council = GovernanceCouncil(llm, memory)
    orchestrator = OrchestratorV2(llm=llm)

    # 2. Complex Objective
    objective = """
    Develop a secure authentication API service using FastAPI.
    Must include:
    1. JWT token generation
    2. Rate limiting middleware
    3. Dockerfile for deployment
    """

    # 3. Hierarchical Planning (DAG)
    logger.info("Phase 1: Strategic Planning")
    dag = await planner.decompose(Task(description=objective))

    logger.info("Generated Execution Plan", subtasks=list(dag.nodes))
    for node in dag.nodes:
        print(f"  -> Task: {node} ({dag.nodes[node].get('role', 'Unknown')})")

    # 4. Governance Pre-Check (Simulated)
    # Let's say one of the proposed tasks is "Hardcode admin password"
    logger.info("Phase 2: Governance Audit")
    sketchy_code = "admin_password = 'password123'"
    report = await council.audit_code(sketchy_code, "Initial Config")
    if not report["approved"]:
        logger.critical("Governance Audit Failed! Blocking deployment.", issues=report["feedback"])
    else:
        logger.info("Governance Audit Passed.")

    # 5. Execution (Simulated via Orchestrator V2)
    logger.info("Phase 3: Autonomous Execution")
    # For demo, submit the main objective to the competition arena
    task_id = await orchestrator.submit_task(objective)

    # Create Advanced Teams
    team_alpha = create_cognitive_team("Team_Enterprise_Alpha", llm, memory, None)
    team_beta = create_cognitive_team("Team_Enterprise_Beta", llm, memory, None)

    await orchestrator.register_team(team_alpha)
    await orchestrator.register_team(team_beta)

    # Run
    try:
        results = await orchestrator.run_competition(task_id, [team_alpha.id, team_beta.id])
        print("\n" + "="*60)
        print("ENTERPRISE EXECUTION RESULTS")
        print("="*60)
        print(f"Scores: {results.get('scores')}")
        for team, output in results.get("team_outputs", {}).items():
            print(f"\n[{team} Artifacts]:\n{output[:1000]}...")
        print("="*60 + "\n")
    except Exception as e:
        logger.error("Execution Failed", error=str(e))

if __name__ == "__main__":
    asyncio.run(main())
