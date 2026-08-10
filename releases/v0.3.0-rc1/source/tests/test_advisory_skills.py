from app.services.capability import gateway
from app.skills.advisory_search import AdvisoryDocument, AdvisorySearchIndex, normalize_text


def test_synonym_normalization():
    assert "混凝土" in normalize_text("C30砼基础")
    assert "钢筋" in normalize_text("螺纹钢加工")


def test_search_outputs_candidate_not_verified():
    index = AdvisorySearchIndex([
        AdvisoryDocument("1", "C30混凝土基础浇筑", {"kind": "boq"}),
        AdvisoryDocument("2", "HRB400E钢筋制作安装", {"kind": "boq"}),
    ])
    rows = index.search("C30砼基础")
    assert rows
    assert rows[0]["id"] == "1"
    assert rows[0]["state"] == "CANDIDATE"
    assert rows[0]["decision_authority"] == "NONE"


def test_advisory_capabilities_registered():
    ids = {m.id for m in gateway.manifests()}
    assert "p02.advisory_match" in ids
    assert "p08.advisory_search" in ids
