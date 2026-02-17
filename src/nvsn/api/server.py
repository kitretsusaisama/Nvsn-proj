from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Optional
import structlog
import uuid
import asyncio
from ..orchestrator.core_v2 import OrchestratorV2
from ..agents.gemini_llm import GeminiLLM
from ..config import settings
from ..infra.database import db

logger = structlog.get_logger()

app = FastAPI(title="NvsN API Gateway", version="1.0.0")

# Singleton Orchestrator (Shared State)
# In real prod, use DI container
llm = GeminiLLM(api_key=settings.google_api_key) if settings.google_api_key else None
orchestrator = OrchestratorV2(llm=llm) if llm else None

class TaskCreate(BaseModel):
    description: str
    requirements: List[str] = []

class TaskResponse(BaseModel):
    id: str
    status: str

@app.on_event("startup")
async def startup_event():
    logger.info("Starting API Gateway...")
    await db.init_models()
    # Start worker (if not already running)
    asyncio.create_task(orchestrator._listen_for_tasks())

@app.post("/tasks", response_model=TaskResponse)
async def create_task(task: TaskCreate):
    if not orchestrator:
        raise HTTPException(status_code=503, detail="Orchestrator not ready (LLM missing)")

    try:
        task_id = await orchestrator.submit_task(task.description, task.requirements)
        return TaskResponse(id=str(task_id), status="SUBMITTED")
    except Exception as e:
        logger.error("API Task Submit Failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    return {"status": "healthy", "version": "1.0.0"}
