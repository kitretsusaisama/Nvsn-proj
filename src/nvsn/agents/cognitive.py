import asyncio
import re
from typing import Dict, Any, List, Optional
from ..core.interfaces import AgentInterface, LLMInterface, MemoryInterface, CommunicationInterface
from ..core.types import Task, TaskResult, Message, AgentState, AgentRole
from ..core.tools import Tool, PythonInterpreter, WebSearch, FileSystem
from ..utils.logging import configure_logging
from ..infra.bus import bus
import structlog
import uuid
import json

logger = structlog.get_logger()

class CognitiveAgent(AgentInterface):
    """
    Advanced agent with ReAct (Reasoning + Acting) capabilities.
    """
    def __init__(self,
                 role: AgentRole,
                 llm: LLMInterface,
                 memory: MemoryInterface,
                 communication: CommunicationInterface,
                 team_id: str,
                 name: str = None):
        self.id = str(uuid.uuid4())
        self.role = role
        self.name = name or f"{role.value}_{self.id[:8]}"
        self.team_id = team_id
        self.llm = llm
        self.memory = memory
        self.communication = communication
        self.tools: Dict[str, Tool] = {}

        # Load tools
        self._register_tool(PythonInterpreter())
        self._register_tool(WebSearch())

        self.state = AgentState(
            id=self.id,
            name=self.name,
            role=self.role,
            team_id=self.team_id,
            status="IDLE"
        )
        self.logger = logger.bind(agent_id=self.id, role=self.role.value)

    def _register_tool(self, tool: Tool):
        self.tools[tool.name] = tool

    async def boot(self):
        """Initialize and hydrate from DB."""
        # TODO: Hydrate logic using new AgentModel
        self.logger.info("Cognitive Agent Booted", status="ONLINE")

    async def shutdown(self):
        self.state.status = "OFFLINE"

    async def process_task(self, task: Task) -> TaskResult:
        """
        Executes a ReAct loop: Think -> Act -> Observe -> Conclude.
        """
        self.state.current_task_id = task.id
        self.state.status = "THINKING"
        self.logger.info("Starting ReAct Loop", task=task.description)

        # 1. Retrieve Context
        context_items = await self.memory.retrieve(task.description, limit=3)
        context_str = "\n".join([f"- {item.content}" for item in context_items]) if context_items else "None"

        history = []
        max_iterations = 5

        for i in range(max_iterations):
            step_prompt = self._build_react_prompt(task, context_str, history)

            # 2. LLM Call (Think)
            response = await self.llm.generate(step_prompt)
            self.logger.debug("LLM Response", iteration=i, content=response)

            # 3. Parse Action
            thought, action, action_input = self._parse_react_response(response)

            history.append(f"Thought: {thought}")

            if action == "Final Answer":
                self.state.status = "IDLE"

                # Persist result to memory
                from ..core.types import MemoryObject
                await self.memory.store(
                    MemoryObject(
                        content=f"Task: {task.description}\nResult: {action_input}",
                        metadata={"task_id": str(task.id), "role": self.role.value, "type": "result"},
                        vector=await self.llm.embed(action_input)
                    )
                )

                return TaskResult(task_id=task.id, success=True, output=action_input)

            # 4. Execute Tool (Act)
            observation = await self._execute_tool(action, action_input)

            history.append(f"Action: {action}({action_input})")
            history.append(f"Observation: {observation}")

            # Update Context
            context_str += f"\nObservation {i}: {observation}"

        # If loop exhaustion
        return TaskResult(task_id=task.id, success=False, output="Max iterations reached without final answer.")

    def _build_react_prompt(self, task: Task, context: str, history: List[str]) -> str:
        tools_desc = "\n".join([f"- {t.name}: {t.description}" for t in self.tools.values()])
        history_str = "\n".join(history)

        return f"""
You are {self.name}, a {self.role.value} agent.
Your goal is to solve the user's task efficiently.

TOOLS AVAILABLE:
{tools_desc}

FORMAT:
Thought: (your reasoning about what to do next)
Action: (one of [{', '.join(self.tools.keys())}] or "Final Answer")
Action Input: (the input for the tool)

TASK:
{task.description}

CONTEXT:
{context}

HISTORY:
{history_str}

Now, provide your next step.
"""

    def _parse_react_response(self, response: str):
        """
        Extracts Thought, Action, and Action Input.
        """
        thought_match = re.search(r"Thought:\s*(.*?)\n", response, re.DOTALL)
        action_match = re.search(r"Action:\s*(.*?)\n", response, re.DOTALL)
        input_match = re.search(r"Action Input:\s*(.*)", response, re.DOTALL)

        thought = thought_match.group(1).strip() if thought_match else "Proceeding..."
        action = action_match.group(1).strip() if action_match else "Final Answer"
        action_input = input_match.group(1).strip() if input_match else response

        # Fallback if LLM just outputs the answer
        if "Final Answer" not in action and not any(t in action for t in self.tools):
             if len(response) < 200: # Heuristic
                 return thought, "Final Answer", response

        return thought, action, action_input

    async def _execute_tool(self, action: str, action_input: str) -> str:
        self.state.status = "ACTING"
        if action in self.tools:
            self.logger.info("Executing Tool", tool=action, input=action_input)
            try:
                # Basic args parsing (assuming single string input for MVP)
                # In robust version, parse JSON args
                if action == "python_interpreter":
                     # Strip code block markers if present
                     code = action_input.strip().strip("`").replace("python", "").strip()
                     result = await self.tools[action].run(code)
                     return result
                else:
                    return await self.tools[action].run(action_input)
            except Exception as e:
                return f"Tool Error: {str(e)}"

        return f"Unknown tool: {action}"

    async def receive_message(self, message: Message):
        pass

    def get_state(self) -> AgentState:
        return self.state
