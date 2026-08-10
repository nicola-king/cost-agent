from dataclasses import dataclass

COMMERCIAL_ROLES = {"project_manager", "cost_lead"}

@dataclass(frozen=True)
class AccessDecision:
    allowed: bool
    reason: str

def can_view_commercial(role: str) -> AccessDecision:
    if role in COMMERCIAL_ROLES:
        return AccessDecision(True, "authorized")
    return AccessDecision(False, "commercial_confidential")
