import pytest
import asyncio
from nvsn.core.types import Task, TaskResult, AgentRole
from nvsn.agents.llm import MockLLM
from nvsn.agents.base import BaseAgent
from nvsn.memory.local import LocalVectorMemory

@pytest.mark.asyncio
async def test_agent_initialization():
    llm = MockLLM()
    memory = LocalVectorMemory()
    agent = BaseAgent(
        role=AgentRole.PLANNER,
        llm=llm,
        memory=memory,
        communication=None,
        team_id="test_team"
    )

    assert agent.id is not None
    assert agent.role == AgentRole.PLANNER
    assert agent.state.status == "INITIALIZING"

    await agent.boot()
    assert agent.state.status == "IDLE"

@pytest.mark.asyncio
async def test_agent_process_task():
    llm = MockLLM()
    memory = LocalVectorMemory()
    agent = BaseAgent(
        role=AgentRole.ENGINEER,
        llm=llm,
        memory=memory,
        communication=None,
        team_id="test_team"
    )
    await agent.boot()

    task = Task(description="Write code")
    result = await agent.process_task(task)

    assert isinstance(result, TaskResult)
    assert result.success is True
    assert result.task_id == task.id
