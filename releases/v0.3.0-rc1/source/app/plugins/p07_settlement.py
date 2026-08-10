from __future__ import annotations

from app.plugins.base import register
from app.services.capability import CapabilityManifest, CapabilityResult


def _reconcile(required, tested, lower=1.0, upper=1.05):
    required, tested = float(required), float(tested)
    if required < 0 or tested < 0:
        return {"coverage_ratio": None, "state": "invalid_negative_quantity"}
    if required == 0:
        return {"coverage_ratio": None, "state": "unresolved"}
    ratio = tested / required
    if ratio < lower:
        state = "insufficient_coverage"
    elif ratio > upper:
        state = "exceeds_internal_control"
    else:
        state = "closed"
    return {"coverage_ratio": ratio, "state": state}


@register(CapabilityManifest(id="p07.material_evidence_reconcile", version="1.1.0", risk="high"))
def material_evidence_reconcile(db, project_id, actor, role, payload):
    required = payload.get("as_built_quantity")
    tested = payload.get("tested_batch_quantity")
    lower = float(payload.get("lower_ratio", 1.0))
    upper = float(payload.get("upper_ratio", 1.05))
    if required is None or tested is None:
        return CapabilityResult("needs_information", {"required": ["as_built_quantity", "tested_batch_quantity"]})
    row = _reconcile(required, tested, lower, upper)
    state = row["state"]
    return CapabilityResult("success" if state == "closed" else "conflict", {
        **row,
        "threshold": {"type": "internal_control", "lower": lower, "upper": upper},
    })


@register(CapabilityManifest(id="p07.material_batch_periodic_check", version="1.0.0", risk="high"))
def material_batch_periodic_check(db, project_id, actor, role, payload):
    """Weekly/monthly material test-batch control against cumulative verified construction quantity.

    Periodic checks are early-warning controls. Final settlement still uses the as-built
    reconciliation capability. Each period must independently satisfy 100%-105% coverage.
    """
    periods = payload.get("periods") or []
    frequency = (payload.get("frequency") or "").strip().lower()
    if frequency not in {"weekly", "monthly"}:
        return CapabilityResult("needs_information", {"required": ["frequency: weekly|monthly"]})
    if not periods:
        return CapabilityResult("needs_information", {"required": ["periods"]})

    rows = []
    conflict_count = 0
    previous_required = 0.0
    previous_tested = 0.0
    for idx, period in enumerate(periods, start=1):
        label = period.get("period") or f"{frequency}-{idx}"
        required = period.get("cumulative_construction_quantity")
        tested = period.get("cumulative_tested_batch_quantity")
        if required is None or tested is None:
            return CapabilityResult("needs_information", {
                "required": ["cumulative_construction_quantity", "cumulative_tested_batch_quantity"],
                "period": label,
            })
        required = float(required)
        tested = float(tested)
        if required < previous_required or tested < previous_tested:
            return CapabilityResult("conflict", {
                "state": "cumulative_quantity_regression",
                "period": label,
                "previous": {"construction": previous_required, "tested": previous_tested},
                "current": {"construction": required, "tested": tested},
            })
        check = _reconcile(required, tested)
        if check["state"] != "closed":
            conflict_count += 1
        rows.append({
            "period": label,
            "cumulative_construction_quantity": required,
            "cumulative_tested_batch_quantity": tested,
            **check,
        })
        previous_required = required
        previous_tested = tested

    return CapabilityResult("success" if conflict_count == 0 else "conflict", {
        "frequency": frequency,
        "rule": "construction_quantity <= tested_batch_quantity <= construction_quantity * 1.05",
        "period_count": len(rows),
        "conflict_count": conflict_count,
        "periods": rows,
        "final_as_built_reconciliation_required": True,
    })


@register(CapabilityManifest(id="p07.major_change_dossier_check", version="1.0.0", risk="medium"))
def major_change_check(db, project_id, actor, role, payload):
    amount = float(payload.get("amount", 0))
    contract = float(payload.get("contract_amount", 0))
    fixed = float(payload.get("fixed_threshold", 0))
    ratio_threshold = float(payload.get("ratio_threshold", 1))
    ratio = amount / contract if contract else 0
    major = (fixed > 0 and amount >= fixed) or (contract > 0 and ratio >= ratio_threshold) or bool(payload.get("manual_major", False))
    return CapabilityResult("success", {"major": major, "amount": amount, "contract_ratio": ratio, "thresholds": {"fixed": fixed, "ratio": ratio_threshold}})
