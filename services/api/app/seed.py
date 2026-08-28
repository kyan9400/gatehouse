from datetime import UTC, datetime, timedelta

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from .audit import append_audit
from .models import AccessPolicy, AccessRequest


async def seed_demo(session: AsyncSession) -> None:
    existing = await session.scalar(
        select(func.count()).select_from(AccessRequest).where(AccessRequest.workspace_id == "demo")
    )
    if existing:
        return

    now = datetime.now(UTC)
    policies = [
        AccessPolicy(
            id="policy-production-read",
            workspace_id="demo",
            name="Production read-only",
            description="Low-risk visibility into production telemetry and logs.",
            resource_prefix="prod/",
            max_ttl_hours=24,
            requires_step_up=False,
            approver_group="on-call",
        ),
        AccessPolicy(
            id="policy-production-write",
            workspace_id="demo",
            name="Production change access",
            description="Short-lived write access for an approved incident or change window.",
            resource_prefix="prod/",
            max_ttl_hours=4,
            requires_step_up=True,
            approver_group="platform-leads",
        ),
        AccessPolicy(
            id="policy-staging-admin",
            workspace_id="demo",
            name="Staging administration",
            description="Admin access for integration testing and release verification.",
            resource_prefix="staging/",
            max_ttl_hours=12,
            requires_step_up=False,
            approver_group="engineering",
        ),
    ]
    session.add_all(policies)
    requests = [
        AccessRequest(
            id="req-7f2a",
            workspace_id="demo",
            resource="prod/payments/logs",
            permission="read",
            environment="production",
            requester="maya.chen",
            reason="Investigate elevated checkout latency after the 14:00 UTC release.",
            risk="medium",
            status="pending",
            requested_at=now - timedelta(minutes=12),
            expires_at=now + timedelta(hours=7),
            version_id=1,
        ),
        AccessRequest(
            id="req-1b90",
            workspace_id="demo",
            resource="prod/orders/database",
            permission="write",
            environment="production",
            requester="omar.hassan",
            reason="Apply the approved index change from incident INC-4821.",
            risk="high",
            status="pending",
            requested_at=now - timedelta(minutes=31),
            expires_at=now + timedelta(hours=3),
            version_id=1,
        ),
        AccessRequest(
            id="req-58c1",
            workspace_id="demo",
            resource="staging/catalog",
            permission="admin",
            environment="staging",
            requester="lucas.rossi",
            reason="Validate the catalog migration against the release candidate.",
            risk="low",
            status="approved",
            requested_at=now - timedelta(hours=2),
            expires_at=now + timedelta(hours=10),
            decided_at=now - timedelta(hours=1, minutes=48),
            decided_by="nora.patel",
            decision_note="Approved for release verification.",
            version_id=1,
        ),
        AccessRequest(
            id="req-3a77",
            workspace_id="demo",
            resource="prod/identity/secrets",
            permission="admin",
            environment="production",
            requester="jules.martin",
            reason="Temporary credentials requested without a linked incident.",
            risk="critical",
            status="denied",
            requested_at=now - timedelta(hours=5),
            expires_at=now - timedelta(hours=1),
            decided_at=now - timedelta(hours=4, minutes=40),
            decided_by="nora.patel",
            decision_note="Link an incident and use the break-glass policy.",
            version_id=1,
        ),
    ]
    session.add_all(requests)
    for request in requests:
        await append_audit(
            session,
            workspace_id="demo",
            actor=request.requester,
            action=f"request.{request.status}"
            if request.status != "pending"
            else "request.created",
            entity_type="access_request",
            entity_id=request.id,
            payload={"resource": request.resource, "permission": request.permission},
        )
    await session.commit()
