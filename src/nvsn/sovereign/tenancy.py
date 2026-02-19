from typing import Dict
import structlog

logger = structlog.get_logger()

class TenantManager:
    """
    Enforces resource quotas per tenant (MNC Requirement).
    """
    def __init__(self):
        # Tenant -> Usage Stats
        self.quotas: Dict[str, Dict[str, int]] = {
            "default": {"cpu": 100, "ram": 1024, "agents": 10}
        }
        self.usage: Dict[str, Dict[str, int]] = {}
        self.logger = logger.bind(component="MultiTenancy")

    def register_tenant(self, tenant_id: str, quota: Dict[str, int]):
        self.quotas[tenant_id] = quota
        self.usage[tenant_id] = {"cpu": 0, "ram": 0, "agents": 0}
        self.logger.info("Tenant Onboarded", tenant=tenant_id)

    def check_quota(self, tenant_id: str, resource: str, amount: int) -> bool:
        if tenant_id not in self.quotas:
            return False

        limit = self.quotas[tenant_id].get(resource, 0)
        current = self.usage[tenant_id].get(resource, 0)

        if current + amount > limit:
            self.logger.warning("Quota Exceeded", tenant=tenant_id, resource=resource)
            return False

        self.usage[tenant_id][resource] += amount
        return True

# Global Tenancy
tenancy = TenantManager()
