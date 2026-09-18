from sample_app.liveops_service.service import ClaimRequest, claim_reward
from sample_app.liveops_service.state import STATE


def setup_function() -> None:
    STATE.reset()


def test_idempotent_duplicate_returns_same_claim() -> None:
    req = ClaimRequest("p1", "spring", "same")
    status1, payload1 = claim_reward(req)
    status2, payload2 = claim_reward(req)
    assert status1 == status2 == 200
    assert payload1 == payload2
    assert STATE.claim_count_by_player["p1"] == 1


def test_fourth_unique_claim_is_rejected() -> None:
    for i in range(3):
        status, _ = claim_reward(ClaimRequest("p1", "spring", f"k{i}"))
        assert status == 200
    status, payload = claim_reward(ClaimRequest("p1", "spring", "k3"))
    assert status == 409
    assert payload == {"error": "daily_limit_reached"}
