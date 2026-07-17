from swarmcore_domain import FindingStatus, can_transition_finding


def test_finding_lifecycle_is_frozen() -> None:
    assert can_transition_finding(FindingStatus.OPEN, FindingStatus.ACKNOWLEDGED)
    assert can_transition_finding(FindingStatus.OPEN, FindingStatus.WAIVED)
    assert can_transition_finding(FindingStatus.ACKNOWLEDGED, FindingStatus.RESOLVED)
    assert can_transition_finding(FindingStatus.RESOLVED, FindingStatus.OPEN)
    assert can_transition_finding(FindingStatus.WAIVED, FindingStatus.OPEN)
    assert not can_transition_finding(FindingStatus.RESOLVED, FindingStatus.WAIVED)
