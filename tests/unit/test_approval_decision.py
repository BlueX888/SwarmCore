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
        "required_roles": [],
    }
    base.update(overrides)
    return SimpleNamespace(**base)


def test_expired_pending_approval_remains_actionable() -> None:
    assert approval_decision_error(_request(), actor="operator") is None


def test_already_handled_approval_is_blocked() -> None:
    blocked = approval_decision_error(_request(status="APPROVED"), actor="operator")
    assert blocked == (410, "该审批已处理, 请刷新待办列表。")


def test_maker_checker_blocks_same_actor() -> None:
    blocked = approval_decision_error(
        _request(requires_distinct_approver=True, requested_by="alice"),
        actor="alice",
    )
    assert blocked == (403, "关键审批要求审批人与发起人分离(maker-checker)。")


def test_required_business_role_is_enforced() -> None:
    request = _request(required_roles=["risk_reviewer", "tenant_admin"])

    assert approval_decision_error(
        request, actor="buyer", roles=("procurement_operator",)
    ) == (403, "当前身份不具备该审批要求的业务角色。")
    assert approval_decision_error(
        request, actor="risk", roles=("risk_reviewer",)
    ) is None
