from __future__ import annotations

from datetime import UTC, datetime, timedelta
from types import SimpleNamespace
from uuid import uuid4

from swarmcore_api.routes import approval_decision_error


def _request(**overrides: object) -> SimpleNamespace:
    base = {
        "id": uuid4(),
        "status": "PENDING",
        "expires_at": datetime.now(UTC) - timedelta(hours=1),
        "requires_distinct_approver": False,
        "requested_by": "workflow",
    }
    base.update(overrides)
    return SimpleNamespace(**base)


def test_expired_pending_approval_remains_actionable() -> None:
    assert approval_decision_error(_request(), actor="operator") is None


def test_already_handled_approval_is_blocked() -> None:
    blocked = approval_decision_error(_request(status="APPROVED"), actor="operator")
    assert blocked == (410, "该审批已处理，请刷新待办列表。")


def test_maker_checker_blocks_same_actor() -> None:
    blocked = approval_decision_error(
        _request(requires_distinct_approver=True, requested_by="alice"),
        actor="alice",
    )
    assert blocked == (403, "关键审批要求审批人与发起人分离（maker-checker）。")
