from ..core.interfaces import TeamInterface, AgentInterface
from ..core.types import Task, TaskResult, TeamState, AgentRole
from typing import List, Dict
import uuid
import structlog
import asyncio

logger = structlog.get_logger()

class Team(TeamInterface):
    """
    Manages a group of agents working towards a common goal.
    """
    def __init__(self, name: str):
        self.id = str(uuid.uuid4())
        self.name = name
        self.agents: Dict[str, AgentInterface] = {}
        self.state = TeamState(
            id=self.id,
            name=self.name,
            agent_ids=[],
            active_tasks=0,
            score=0.0
        )
        self.logger = logger.bind(team_id=self.id, team_name=self.name)

    def add_agent(self, agent: AgentInterface):
        self.agents[agent.id] = agent
        self.state.agent_ids.append(agent.id)
        self.logger.info("Agent added to team", agent_id=agent.id)

    def remove_agent(self, agent_id: str):
        if agent_id in self.agents:
            del self.agents[agent_id]
            self.state.agent_ids.remove(agent_id)
            self.logger.info("Agent removed from team", agent_id=agent_id)

    def get_agents(self) -> List[AgentInterface]:
        return list(self.agents.values())

    async def assign_task(self, task: Task) -> TaskResult:
        """
        Orchestrates the task execution within the team.
        Simple workflow: Planner -> Engineer -> Critic.
        """
        self.logger.info("Team received task", task_id=str(task.id))
        self.state.active_tasks += 1

        try:
            # 1. Find a Planner
            planner = self._find_agent_by_role(AgentRole.PLANNER)
            if planner:
                self.logger.info("Delegating to Planner", agent_id=planner.id)
                plan_result = await planner.process_task(task)
                task.metadata["plan"] = plan_result.output

            # 2. Find an Engineer
            engineer = self._find_agent_by_role(AgentRole.ENGINEER)
            if engineer:
                self.logger.info("Delegating to Engineer", agent_id=engineer.id)
                # Update task description with plan
                exec_task = Task(
                    description=f"Implement the following plan: {task.metadata.get('plan', 'No plan')}",
                    requirements=task.requirements
                )
                code_result = await engineer.process_task(exec_task)
                task.metadata["code"] = code_result.output
            else:
                code_result = TaskResult(task_id=task.id, success=False, output="No Engineer available")

            # 3. Find a Critic (Optional)
            critic = self._find_agent_by_role(AgentRole.CRITIC)
            final_output = code_result.output

            if critic and code_result.success:
                self.logger.info("Delegating to Critic", agent_id=critic.id)
                review_task = Task(
                    description="Review the code",
                    metadata={"previous_output": code_result.output}
                )
                review_result = await critic.process_task(review_task)
                final_output = f"Code:\n{code_result.output}\n\nReview:\n{review_result.output}"

            self.state.active_tasks -= 1
            return TaskResult(
                task_id=task.id,
                success=True,
                output=final_output
            )

        except Exception as e:
            self.logger.error("Team task execution failed", error=str(e))
            self.state.active_tasks -= 1
            return TaskResult(
                task_id=task.id,
                success=False,
                output=str(e)
            )

    def _find_agent_by_role(self, role: AgentRole) -> AgentInterface:
        for agent in self.agents.values():
            if agent.get_state().role == role:
                return agent
        return None
