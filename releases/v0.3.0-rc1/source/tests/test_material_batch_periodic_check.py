from app.core.db import SessionLocal
from app.plugins.base import gateway


def _execute(capability, project, payload):
    with SessionLocal() as db:
        return gateway.execute(db, capability, project, "cost", "cost_lead", payload)[1]


def test_weekly_material_batch_check_passes_each_period():
    result = _execute("p07.material_batch_periodic_check", "P-BATCH-W", {
        "frequency": "weekly",
        "periods": [
            {"period": "2026-W31", "cumulative_construction_quantity": 100, "cumulative_tested_batch_quantity": 102},
            {"period": "2026-W32", "cumulative_construction_quantity": 180, "cumulative_tested_batch_quantity": 185},
        ],
    })
    assert result.outcome == "success"
    assert result.data["conflict_count"] == 0
    assert result.data["final_as_built_reconciliation_required"] is True


def test_monthly_material_batch_check_flags_under_coverage():
    result = _execute("p07.material_batch_periodic_check", "P-BATCH-M1", {
        "frequency": "monthly",
        "periods": [
            {"period": "2026-07", "cumulative_construction_quantity": 500, "cumulative_tested_batch_quantity": 490},
        ],
    })
    assert result.outcome == "conflict"
    assert result.data["periods"][0]["state"] == "insufficient_coverage"


def test_monthly_material_batch_check_flags_over_five_percent():
    result = _execute("p07.material_batch_periodic_check", "P-BATCH-M2", {
        "frequency": "monthly",
        "periods": [
            {"period": "2026-07", "cumulative_construction_quantity": 500, "cumulative_tested_batch_quantity": 526},
        ],
    })
    assert result.outcome == "conflict"
    assert result.data["periods"][0]["state"] == "exceeds_internal_control"


def test_periodic_cumulative_quantities_cannot_regress():
    result = _execute("p07.material_batch_periodic_check", "P-BATCH-R", {
        "frequency": "weekly",
        "periods": [
            {"period": "2026-W31", "cumulative_construction_quantity": 100, "cumulative_tested_batch_quantity": 102},
            {"period": "2026-W32", "cumulative_construction_quantity": 90, "cumulative_tested_batch_quantity": 105},
        ],
    })
    assert result.outcome == "conflict"
    assert result.data["state"] == "cumulative_quantity_regression"


def test_final_as_built_reconciliation_keeps_100_to_105_rule():
    passed = _execute("p07.material_evidence_reconcile", "P-BATCH-F1", {"as_built_quantity": 1000, "tested_batch_quantity": 1040})
    low = _execute("p07.material_evidence_reconcile", "P-BATCH-F2", {"as_built_quantity": 1000, "tested_batch_quantity": 999})
    high = _execute("p07.material_evidence_reconcile", "P-BATCH-F3", {"as_built_quantity": 1000, "tested_batch_quantity": 1051})
    assert passed.outcome == "success"
    assert low.data["state"] == "insufficient_coverage"
    assert high.data["state"] == "exceeds_internal_control"
