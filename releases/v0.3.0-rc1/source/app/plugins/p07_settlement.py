from app.plugins.base import register
from app.services.capability import CapabilityManifest, CapabilityResult

@register(CapabilityManifest(id="p07.material_evidence_reconcile", version="1.0.0", risk="high"))
def material_evidence_reconcile(db, project_id, actor, role, payload):
    required = payload.get("as_built_quantity")
    tested = payload.get("tested_batch_quantity")
    lower = float(payload.get("lower_ratio", 1.0))
    upper = float(payload.get("upper_ratio", 1.05))
    if required is None or tested is None:
        return CapabilityResult("needs_information", {"required": ["as_built_quantity", "tested_batch_quantity"]})
    required, tested = float(required), float(tested)
    ratio = None if required == 0 else tested / required
    if ratio is None:
        state = "unresolved"
    elif ratio < lower:
        state = "insufficient_coverage"
    elif ratio > upper:
        state = "exceeds_internal_control"
    else:
        state = "closed"
    return CapabilityResult("conflict" if state != "closed" else "success", {"coverage_ratio": ratio, "state": state, "threshold": {"type": "internal_control", "lower": lower, "upper": upper}})

@register(CapabilityManifest(id="p07.major_change_dossier_check", version="1.0.0", risk="medium"))
def major_change_check(db, project_id, actor, role, payload):
    amount = float(payload.get("amount", 0))
    contract = float(payload.get("contract_amount", 0))
    fixed = float(payload.get("fixed_threshold", 0))
    ratio_threshold = float(payload.get("ratio_threshold", 1))
    ratio = amount / contract if contract else 0
    major = (fixed > 0 and amount >= fixed) or (contract > 0 and ratio >= ratio_threshold) or bool(payload.get("manual_major", False))
    return CapabilityResult("success", {"major": major, "amount": amount, "contract_ratio": ratio, "thresholds": {"fixed": fixed, "ratio": ratio_threshold}})
