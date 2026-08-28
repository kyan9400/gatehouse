from contextlib import asynccontextmanager
from datetime import UTC, datetime, timedelta
from uuid import uuid4

from fastapi import Depends, FastAPI, Header, HTTPException, Query, Response, status
from fastapi.middleware.cors import CORSMiddleware
from prometheus_client import CONTENT_TYPE_LATEST, Counter, Gauge, generate_latest
from sqlalchemy import desc, func, select, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm.exc import StaleDataError

from .audit import append_audit
from .config import settings
from .db import SessionLocal, engine, get_session, init_db
from .models import AccessPolicy, AccessRequest, AuditEvent
from .schemas import (
    AccessPolicyOut,
    AccessRequestCreate,
    AccessRequestDecision,
    AccessRequestOut,
    AuditEventOut,
    OverviewOut,
)
from .security import RequestContext, get_context, require_approver
from .seed import seed_demo

REQUESTS_CREATED = Counter("gatehouse_access_requests_created_total", "Access requests created")
DECISIONS_TOTAL = Counter(
    "gatehouse_access_decisions_total", "Access request decisions", ["decision"]
)
PENDING_REQUESTS = Gauge("gatehouse_pending_access_requests", "Pending access requests")


@asynccontextmanager
async def lifespan(_: FastAPI):
    await init_db()
    if settings.demo_seed:
        async with SessionLocal() as session:
            await seed_demo(session)
    yield
    await engine.dispose()


app = FastAPI(
    title="Gatehouse API",
    version="0.1.0",
    description="Multi-tenant, auditable access request and approval workflows.",
    lifespan=lifespan,
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=[
        "Content-Type",
        "X-API-Key",
        "X-Actor",
        "X-Role",
        "X-Workspace-ID",
        "Idempotency-Key",
    ],
)


def _risk_for(request: AccessRequestCreate) -> str:
    if request.environment == "production" and request.permission == "admin":
        return "critical"
    if request.environment == "production" and request.permission == "write":
        return "high"
    if request.environment == "production" or request.permission == "admin":
        return "medium"
    return "low"


async def _get_request(session: AsyncSession, workspace_id: str, request_id: str) -> AccessRequest:
    request = await session.scalar(
        select(AccessRequest).where(
            AccessRequest.workspace_id == workspace_id,
            AccessRequest.id == request_id,
        )
    )
    if request is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Access request not found"
        )
    return request


@app.get("/healthz", tags=["system"])
async def healthz() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/readyz", tags=["system"])
async def readyz() -> dict[str, str]:
    async with engine.connect() as connection:
        await connection.execute(text("SELECT 1"))
    return {"status": "ready"}


@app.get("/metrics", tags=["system"])
async def metrics() -> Response:
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)


@app.get("/api/v1/overview", response_model=OverviewOut, tags=["operations"])
async def overview(
    context: RequestContext = Depends(get_context),
    session: AsyncSession = Depends(get_session),
) -> OverviewOut:
    now = datetime.now(UTC)
    day_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    pending = await session.scalar(
        select(func.count())
        .select_from(AccessRequest)
        .where(
            AccessRequest.workspace_id == context.workspace_id,
            AccessRequest.status == "pending",
        )
    )
    active = await session.scalar(
        select(func.count())
        .select_from(AccessRequest)
        .where(
            AccessRequest.workspace_id == context.workspace_id,
            AccessRequest.status == "approved",
            AccessRequest.expires_at > now,
        )
    )
    expiring = await session.scalar(
        select(func.count())
        .select_from(AccessRequest)
        .where(
            AccessRequest.workspace_id == context.workspace_id,
            AccessRequest.status == "approved",
            AccessRequest.expires_at > now,
            AccessRequest.expires_at <= now + timedelta(hours=24),
        )
    )
    high_risk = await session.scalar(
        select(func.count())
        .select_from(AccessRequest)
        .where(
            AccessRequest.workspace_id == context.workspace_id,
            AccessRequest.status == "pending",
            AccessRequest.risk.in_(["high", "critical"]),
        )
    )
    decisions = await session.scalar(
        select(func.count())
        .select_from(AccessRequest)
        .where(
            AccessRequest.workspace_id == context.workspace_id,
            AccessRequest.decided_at >= day_start,
        )
    )
    head = await session.scalar(
        select(AuditEvent.event_hash)
        .where(AuditEvent.workspace_id == context.workspace_id)
        .order_by(desc(AuditEvent.created_at), desc(AuditEvent.id))
        .limit(1)
    )
    PENDING_REQUESTS.set(pending or 0)
    return OverviewOut(
        pending=pending or 0,
        active_grants=active or 0,
        expiring_24h=expiring or 0,
        high_risk_pending=high_risk or 0,
        decisions_today=decisions or 0,
        audit_head=head,
    )


@app.get("/api/v1/policies", response_model=list[AccessPolicyOut], tags=["policies"])
async def policies(
    context: RequestContext = Depends(get_context),
    session: AsyncSession = Depends(get_session),
) -> list[AccessPolicy]:
    result = await session.scalars(
        select(AccessPolicy)
        .where(AccessPolicy.workspace_id == context.workspace_id, AccessPolicy.active.is_(True))
        .order_by(AccessPolicy.name)
    )
    return list(result)


@app.get("/api/v1/access-requests", response_model=list[AccessRequestOut], tags=["access"])
async def access_requests(
    request_status: str | None = Query(default=None, alias="status"),
    context: RequestContext = Depends(get_context),
    session: AsyncSession = Depends(get_session),
) -> list[AccessRequest]:
    statement = select(AccessRequest).where(AccessRequest.workspace_id == context.workspace_id)
    if request_status:
        if request_status not in {"pending", "approved", "denied"}:
            raise HTTPException(status_code=400, detail="Unsupported status filter")
        statement = statement.where(AccessRequest.status == request_status)
    result = await session.scalars(
        statement.order_by(AccessRequest.status.asc(), desc(AccessRequest.requested_at)).limit(100)
    )
    return list(result)


@app.post(
    "/api/v1/access-requests", response_model=AccessRequestOut, status_code=201, tags=["access"]
)
async def create_access_request(
    payload: AccessRequestCreate,
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
    context: RequestContext = Depends(get_context),
    session: AsyncSession = Depends(get_session),
) -> AccessRequest:
    if idempotency_key:
        existing = await session.scalar(
            select(AccessRequest).where(
                AccessRequest.workspace_id == context.workspace_id,
                AccessRequest.idempotency_key == idempotency_key,
            )
        )
        if existing:
            return existing
    now = datetime.now(UTC)
    request = AccessRequest(
        id=str(uuid4()),
        workspace_id=context.workspace_id,
        resource=payload.resource,
        permission=payload.permission,
        environment=payload.environment,
        requester=payload.requester,
        reason=payload.reason,
        risk=_risk_for(payload),
        status="pending",
        requested_at=now,
        expires_at=now + timedelta(hours=payload.ttl_hours),
        idempotency_key=idempotency_key,
        version_id=1,
    )
    session.add(request)
    await append_audit(
        session,
        workspace_id=context.workspace_id,
        actor=context.actor,
        action="request.created",
        entity_type="access_request",
        entity_id=request.id,
        payload={
            "resource": request.resource,
            "permission": request.permission,
            "risk": request.risk,
        },
    )
    try:
        await session.commit()
    except IntegrityError as exc:
        await session.rollback()
        raise HTTPException(status_code=409, detail="Idempotency key already used") from exc
    await session.refresh(request)
    REQUESTS_CREATED.inc()
    return request


async def _decide(
    request_id: str,
    decision: str,
    payload: AccessRequestDecision,
    context: RequestContext,
    session: AsyncSession,
) -> AccessRequest:
    request = await _get_request(session, context.workspace_id, request_id)
    if request.status != "pending":
        raise HTTPException(status_code=409, detail=f"Request is already {request.status}")
    request.status = decision
    request.decided_at = datetime.now(UTC)
    request.decided_by = context.actor
    request.decision_note = payload.note.strip() or None
    await append_audit(
        session,
        workspace_id=context.workspace_id,
        actor=context.actor,
        action=f"request.{decision}",
        entity_type="access_request",
        entity_id=request.id,
        payload={"note": request.decision_note or "", "risk": request.risk},
    )
    try:
        await session.commit()
    except StaleDataError as exc:
        await session.rollback()
        raise HTTPException(
            status_code=409, detail="Request changed; refresh and try again"
        ) from exc
    await session.refresh(request)
    DECISIONS_TOTAL.labels(decision=decision).inc()
    return request


@app.post(
    "/api/v1/access-requests/{request_id}/approve", response_model=AccessRequestOut, tags=["access"]
)
async def approve_request(
    request_id: str,
    payload: AccessRequestDecision,
    context: RequestContext = Depends(require_approver),
    session: AsyncSession = Depends(get_session),
) -> AccessRequest:
    return await _decide(request_id, "approved", payload, context, session)


@app.post(
    "/api/v1/access-requests/{request_id}/deny", response_model=AccessRequestOut, tags=["access"]
)
async def deny_request(
    request_id: str,
    payload: AccessRequestDecision,
    context: RequestContext = Depends(require_approver),
    session: AsyncSession = Depends(get_session),
) -> AccessRequest:
    return await _decide(request_id, "denied", payload, context, session)


@app.get("/api/v1/audit", response_model=list[AuditEventOut], tags=["audit"])
async def audit_events(
    context: RequestContext = Depends(get_context),
    session: AsyncSession = Depends(get_session),
) -> list[AuditEvent]:
    result = await session.scalars(
        select(AuditEvent)
        .where(AuditEvent.workspace_id == context.workspace_id)
        .order_by(desc(AuditEvent.created_at), desc(AuditEvent.id))
        .limit(100)
    )
    return list(result)
