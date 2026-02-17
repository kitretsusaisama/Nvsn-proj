import asyncio
import structlog
from typing import Dict, Any, List
from ..agents.cognitive import CognitiveAgent
from ..agents.roles import AgentRole
from ..core.types import Task, TaskResult, MemoryObject
from ..core.interfaces import LLMInterface, MemoryInterface, CommunicationInterface

logger = structlog.get_logger()

class GovernanceCouncil:
    """
    A special team of Supervisor Agents that audit other agents' code *before* execution.
    Acts as a CI/CD Gatekeeper in the NvsN loop.
    """
    def __init__(self, llm: LLMInterface, memory: MemoryInterface):
        self.llm = llm
        self.memory = memory
        self.logger = logger.bind(component="GovernanceCouncil")

        # Instantiate Virtual Auditors
        self.security_auditor = CognitiveAgent(AgentRole.CRITIC, llm, memory, None, "gov", name="Security_Auditor")
        self.compliance_auditor = CognitiveAgent(AgentRole.CRITIC, llm, memory, None, "gov", name="Compliance_Auditor")

    async def audit_code(self, code: str, context: str) -> Dict[str, Any]:
        """
        Runs code through multiple independent auditors.
        """
        self.logger.info("Auditing Code Submission...")

        task = Task(
            description=f"Audit this code for security vulnerabilities (SQLi, RCE, Secrets).\nCode:\n{code}",
            metadata={"previous_output": context}
        )

        # Parallel Audit
        results = await asyncio.gather(
            self.security_auditor.process_task(task),
            self.compliance_auditor.process_task(task)
        )

        feedback = []
        approved = True

        for res in results:
            feedback.append(f"[{res.output}]")
            # Heuristic check for rejection keywords
            if "critical" in res.output.lower() or "reject" in res.output.lower():
                approved = False

        audit_report = {
            "approved": approved,
            "feedback": "\n".join(feedback),
            "timestamp": "now"
        }

        self.logger.info("Audit Complete", approved=approved)
        return audit_report
