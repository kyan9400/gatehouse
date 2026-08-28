# Security and threat model

## Assets

- Access request reasons and resource names
- Approver identity and decision notes
- Workspace boundaries
- Database credentials and API keys

## Threats and controls

| Threat | Control |
| --- | --- |
| Cross-workspace data access | Every request and audit query is scoped by `X-Workspace-ID`; production should enforce the same boundary with database RLS. |
| Replay of a create request | `Idempotency-Key` is unique per workspace. |
| Double approval | Status checks plus SQLAlchemy optimistic versioning return `409` on a stale decision. |
| Forged approver | API key support and explicit role dependency; production must derive role from OIDC claims at a trusted edge. |
| Audit tampering | Append-only events are hash-linked and expose a chain head in the overview. |
| Container escape | Non-root images, dropped Linux capabilities, read-only filesystems, resource limits, and CI image scanning. |
| Secret leakage | No secrets in source or manifests; Kubernetes example secret is a placeholder and runtime values belong in a secret manager. |

## Out of scope for the demo

The header-based identity adapter is deliberately inspectable, not a complete IAM system. Do not use the demo configuration for real privileged access. Add OIDC, short-lived service credentials, TLS, network segmentation, database encryption, and centralized immutable audit retention before production use.
