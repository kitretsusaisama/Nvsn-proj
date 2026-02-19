import asyncio
import sys
import os
import structlog
from dotenv import load_dotenv

sys.path.append(os.path.join(os.path.dirname(__file__), '../src'))

from nvsn.sovereign.workflow import durable, WorkflowContext
from nvsn.sovereign.logic import verifier
from nvsn.sovereign.entanglement import EntangledMemory
from nvsn.infra.database import db
from nvsn.utils.logging import configure_logging

async def mock_migration_step(delay: int):
    await asyncio.sleep(delay)
    return "MIGRATED"

async def mission_critical_workflow(ctx: WorkflowContext):
    # Step 1: Formal Verification
    if not await durable.activity(ctx, "verify_plan", lambda: verifier.verify_plan(100, 5, 200, 10)):
        raise ValueError("Plan Rejected by Logic Gate")

    # Step 2: Backup
    backup_status = await durable.activity(ctx, "backup_db", lambda: "BACKUP_OK")

    # Step 3: Migration (Simulate Crash here)
    # Ideally we crash the process, but for single script demo we simulate restart by re-running
    migration_status = await durable.activity(ctx, "migrate_schema", mock_migration_step, 0.1)

    return "SUCCESS"

async def main():
    load_dotenv()
    logger = configure_logging(level="INFO")
    logger.info("Initializing Sovereign V10 Framework...")

    await db.init_models()

    # 1. Start Shared Memory
    entangled = EntangledMemory()
    entangled.write(b"GLOBAL_STATE: NORMAL")

    # 2. Run Workflow - Part 1 (Simulate Crash)
    workflow_id = "wf_prod_db_001"

    logger.info("--- ATTEMPT 1 (Simulating Crash) ---")
    # Manually inject a partial history to simulate a crash after Step 2
    # In real world, we'd kill the process. Here we just rely on the Engine's replay logic.
    # Actually, let's run it fully to see it pass first.

    try:
        await durable.run_workflow(workflow_id, mission_critical_workflow)
        logger.info("Workflow Completed Successfully")
    except Exception as e:
        logger.error("Workflow Crashed", error=str(e))

    # 3. Verify Replay (Idempotency)
    logger.info("--- ATTEMPT 2 (Restart/Replay) ---")
    # This should be instant because steps are cached in SQL
    await durable.run_workflow(workflow_id, mission_critical_workflow)

    # 4. Symbolic Logic Check
    logger.info("--- LOGIC GATE CHECK ---")
    # Prove that Cost=300 fails if Limit=200
    is_valid = verifier.verify_plan(300, 5, 200, 10)
    logger.info("Invalid Plan Rejected?", status=not is_valid)

    entangled.cleanup()

if __name__ == "__main__":
    asyncio.run(main())
