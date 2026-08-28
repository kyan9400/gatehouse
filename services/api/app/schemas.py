from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class AccessRequestCreate(BaseModel):
    resource: str = Field(min_length=3, max_length=180)
    permission: Literal["read", "write", "admin"]
    environment: Literal["development", "staging", "production"]
    requester: str = Field(min_length=2, max_length=120)
    reason: str = Field(min_length=10, max_length=1000)
    ttl_hours: int = Field(default=8, ge=1, le=168)


class AccessRequestDecision(BaseModel):
    note: str = Field(default="", max_length=500)


class AccessRequestOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    resource: str
    permission: str
    environment: str
    requester: str
    reason: str
    risk: str
    status: str
    requested_at: datetime
    expires_at: datetime
    decided_at: datetime | None
    decided_by: str | None
    decision_note: str | None
    version_id: int


class AccessPolicyOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    description: str
    resource_prefix: str
    max_ttl_hours: int
    requires_step_up: bool
    approver_group: str
    active: bool


class OverviewOut(BaseModel):
    pending: int
    active_grants: int
    expiring_24h: int
    high_risk_pending: int
    decisions_today: int
    audit_head: str | None


class AuditEventOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    actor: str
    action: str
    entity_type: str
    entity_id: str
    prev_hash: str | None
    event_hash: str
    created_at: datetime
