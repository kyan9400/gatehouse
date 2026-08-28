import hashlib
import json
from datetime import UTC, datetime
from uuid import uuid4

from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from .models import AuditEvent


async def append_audit(
    session: AsyncSession,
    *,
    workspace_id: str,
    actor: str,
    action: str,
    entity_type: str,
    entity_id: str,
    payload: dict[str, object],
) -> AuditEvent:
    previous = await session.scalar(
        select(AuditEvent)
        .where(AuditEvent.workspace_id == workspace_id)
        .order_by(desc(AuditEvent.created_at), desc(AuditEvent.id))
        .limit(1)
    )
    created_at = datetime.now(UTC)
    payload_json = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)
    prev_hash = previous.event_hash if previous else None
    digest_input = "|".join(
        [
            prev_hash or "GENESIS",
            workspace_id,
            actor,
            action,
            entity_type,
            entity_id,
            payload_json,
            created_at.isoformat(),
        ]
    )
    event_hash = hashlib.sha256(digest_input.encode("utf-8")).hexdigest()
    event = AuditEvent(
        id=str(uuid4()),
        workspace_id=workspace_id,
        actor=actor,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        payload_json=payload_json,
        prev_hash=prev_hash,
        event_hash=event_hash,
        created_at=created_at,
    )
    session.add(event)
    return event
