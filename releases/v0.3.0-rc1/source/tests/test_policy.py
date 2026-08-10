from app.services.policy import can_view_commercial

def test_commercial_access():
    assert can_view_commercial("project_manager").allowed
    assert can_view_commercial("cost_lead").allowed
    assert not can_view_commercial("technical").allowed
