from typing import Dict, Any
import structlog

logger = structlog.get_logger()

class PolicyEngine:
    """
    Enforces safety and compliance.
    """
    def __init__(self):
        self.forbidden_actions = ["rm -rf", "shutdown", "drop table"]
        self.logger = logger.bind(component="Governance")

    def validate_action(self, action: str, params: Dict[str, Any]) -> bool:
        for forbidden in self.forbidden_actions:
            if forbidden in action.lower():
                self.logger.critical("Action Blocked by Governance", action=action, reason="Unsafe Operation")
                return False

        self.logger.info("Action Approved", action=action)
        return True

governance = PolicyEngine()
