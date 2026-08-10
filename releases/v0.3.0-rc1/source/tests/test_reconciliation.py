from app.services.reconciliation import reconcile

def test_difference_is_not_averaged():
    r = reconcile([("cad", 318.256), ("bim", 316.842)], tolerance=0)
    assert r.status == "unresolved_difference"
    assert round(r.difference, 3) == 1.414
