from app.core.db import Base, engine, SessionLocal
from app.core.models import Project, Source, BOQItem, Measurement
from app.services.capability import gateway
from app import plugins


def setup_module():
    Base.metadata.create_all(bind=engine)


def test_baseline0_build_uses_drawing_quantity_and_award_price():
    project_id = "PRJ-B0-READY"
    with SessionLocal() as db:
        db.merge(Project(id=project_id, name="baseline0-ready"))
        db.merge(Source(id="SRC-B0-BOQ", project_id=project_id, source_type="award_boq", title="中标清单.xlsx", file_path="demo://award-boq", sha256="b0-ready-award"))
        db.merge(Source(id="SRC-B0-DRAW", project_id=project_id, source_type="construction_drawing", title="施工图S-001", file_path="demo://drawing-s001", sha256="b0-ready-drawing"))
        db.merge(
            BOQItem(
                id="BOQ-B0-1",
                project_id=project_id,
                code="010101",
                name="C30混凝土",
                unit="m3",
                award_quantity=100.0,
                award_unit_price=900.0,
            )
        )
        db.merge(
            Measurement(
                id="M-B0-DRAW-1",
                project_id=project_id,
                object_id="BOQ-B0-1",
                measurement_type="baseline_drawing",
                quantity=120.0,
                unit="m3",
                method="drawing_takeoff",
            )
        )
        db.commit()

        _, health = gateway.execute(db, "p01.startup_health", project_id, "tester", "cost_lead", {})
        assert health.outcome == "success"
        assert health.data["boq_items"] == 1
        assert health.data["baseline_measurements"] == 1
        assert health.data["missing"] == []

        _, result = gateway.execute(db, "p01.baseline0_build", project_id, "tester", "cost_lead", {})
        assert result.outcome == "success"
        assert result.data["principle"] == (
            "construction_drawing_quantity_is_baseline; "
            "award_boq_quantity_is_reference; "
            "award_unit_price_is_baseline"
        )
        assert result.data["summary"] == {"boq_items": 1, "baseline_ready": 1, "missing": 0}

        row = result.data["rows"][0]
        assert row["boq_id"] == "BOQ-B0-1"
        assert row["award_quantity_reference"] == 100.0
        assert row["construction_drawing_baseline_quantity"] == 120.0
        assert row["quantity_difference"] == 20.0
        assert row["award_unit_price_baseline"] == 900.0
        assert row["baseline_amount"] == 108000.0
        assert row["measurement_id"] == "M-B0-DRAW-1"


def test_baseline0_build_is_partial_when_any_boq_lacks_drawing_baseline():
    project_id = "PRJ-B0-PARTIAL"
    with SessionLocal() as db:
        db.merge(Project(id=project_id, name="baseline0-partial"))
        db.merge(
            BOQItem(
                id="BOQ-B0-P1",
                project_id=project_id,
                code="020101",
                name="钢筋",
                unit="t",
                award_quantity=10.0,
                award_unit_price=4200.0,
            )
        )
        db.merge(
            BOQItem(
                id="BOQ-B0-P2",
                project_id=project_id,
                code="020102",
                name="模板",
                unit="m2",
                award_quantity=200.0,
                award_unit_price=60.0,
            )
        )
        db.merge(
            Measurement(
                id="M-B0-P1",
                project_id=project_id,
                object_id="BOQ-B0-P1",
                measurement_type="baseline_drawing",
                quantity=9.5,
                unit="t",
                method="drawing_takeoff",
            )
        )
        db.commit()

        _, result = gateway.execute(db, "p01.baseline0_build", project_id, "tester", "cost_lead", {})
        assert result.outcome == "partial"
        assert result.data["summary"] == {"boq_items": 2, "baseline_ready": 1, "missing": 1}
        assert result.data["missing"] == [
            {
                "boq_id": "BOQ-B0-P2",
                "code": "020102",
                "name": "模板",
                "missing": "construction_drawing_baseline_quantity",
            }
        ]


def test_baseline0_build_requires_award_boq_and_startup_health_requires_drawing_baseline():
    empty_project_id = "PRJ-B0-NO-BOQ"
    with SessionLocal() as db:
        db.merge(Project(id=empty_project_id, name="baseline0-no-boq"))
        db.commit()
        _, result = gateway.execute(db, "p01.baseline0_build", empty_project_id, "tester", "cost_lead", {})
        assert result.outcome == "needs_information"
        assert result.data == {"required": ["award_boq"]}

    no_drawing_project_id = "PRJ-B0-NO-DRAW"
    with SessionLocal() as db:
        db.merge(Project(id=no_drawing_project_id, name="baseline0-no-drawing"))
        db.merge(Source(id="SRC-B0-ND", project_id=no_drawing_project_id, source_type="award_boq", title="中标清单.xlsx", file_path="demo://award-boq-no-draw", sha256="b0-no-draw-award"))
        db.merge(
            BOQItem(
                id="BOQ-B0-ND1",
                project_id=no_drawing_project_id,
                code="030101",
                name="砌体",
                unit="m3",
                award_quantity=50.0,
                award_unit_price=500.0,
            )
        )
        db.commit()

        _, health = gateway.execute(db, "p01.startup_health", no_drawing_project_id, "tester", "cost_lead", {})
        assert health.outcome == "needs_information"
        assert "construction_drawing_baseline_quantity" in health.data["missing"]

        _, result = gateway.execute(db, "p01.baseline0_build", no_drawing_project_id, "tester", "cost_lead", {})
        assert result.outcome == "needs_information"
        assert result.data["summary"] == {"boq_items": 1, "baseline_ready": 0, "missing": 1}
