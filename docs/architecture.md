# Architecture notes

## Request lifecycle

1. A requester submits a resource, permission, environment, reason, and TTL.
2. Gatehouse derives a risk level from the requested scope and environment.
3. The API persists the request with a workspace boundary and optional idempotency key.
4. An audit event is appended with the previous workspace event hash.
5. An approver or admin decides. The optimistic version column rejects a stale concurrent decision.
6. The dashboard refreshes the queue and exposes the decision evidence.

## Boundaries

- **Identity boundary:** the demo uses explicit headers so the workflow can be inspected without an identity provider. Production should put OIDC/SCIM in front of the API and map claims to `X-Workspace-ID`, `X-Actor`, and `X-Role` at a trusted edge.
- **Data boundary:** every query includes `workspace_id`; the schema is ready for a PostgreSQL row-level security policy when regulated isolation is required.
- **Evidence boundary:** audit events are append-only at the API layer. The chain detects edits and missing links but is not a substitute for WORM storage.
- **Delivery boundary:** images use immutable tags, CI scans them, and Kubernetes overlays provide environment-specific rollout inputs.

## Trade-offs

The reference implementation keeps the model small and uses SQLAlchemy `create_all` for a clean demo start. A production fork should add Alembic migrations, external identity, a durable queue for notifications, and a database backup/restore runbook before onboarding real teams.
