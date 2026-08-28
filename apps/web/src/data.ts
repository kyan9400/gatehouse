import type { AccessRequest, DashboardData, Overview, Policy } from "./types";

const now = Date.now();
const minutesAgo = (minutes: number) => new Date(now - minutes * 60_000).toISOString();
const hoursFromNow = (hours: number) => new Date(now + hours * 3_600_000).toISOString();

export const demoRequests: AccessRequest[] = [
  {
    id: "req-7f2a",
    resource: "prod/payments/logs",
    permission: "read",
    environment: "production",
    requester: "maya.chen",
    reason: "Investigate elevated checkout latency after the 14:00 UTC release.",
    risk: "medium",
    status: "pending",
    requested_at: minutesAgo(12),
    expires_at: hoursFromNow(7),
    decided_at: null,
    decided_by: null,
    decision_note: null,
    version_id: 1,
  },
  {
    id: "req-1b90",
    resource: "prod/orders/database",
    permission: "write",
    environment: "production",
    requester: "omar.hassan",
    reason: "Apply the approved index change from incident INC-4821.",
    risk: "high",
    status: "pending",
    requested_at: minutesAgo(31),
    expires_at: hoursFromNow(3),
    decided_at: null,
    decided_by: null,
    decision_note: null,
    version_id: 1,
  },
  {
    id: "req-58c1",
    resource: "staging/catalog",
    permission: "admin",
    environment: "staging",
    requester: "lucas.rossi",
    reason: "Validate the catalog migration against the release candidate.",
    risk: "low",
    status: "approved",
    requested_at: minutesAgo(120),
    expires_at: hoursFromNow(10),
    decided_at: minutesAgo(108),
    decided_by: "nora.patel",
    decision_note: "Approved for release verification.",
    version_id: 1,
  },
  {
    id: "req-3a77",
    resource: "prod/identity/secrets",
    permission: "admin",
    environment: "production",
    requester: "jules.martin",
    reason: "Temporary credentials requested without a linked incident.",
    risk: "critical",
    status: "denied",
    requested_at: minutesAgo(300),
    expires_at: hoursFromNow(-1),
    decided_at: minutesAgo(280),
    decided_by: "nora.patel",
    decision_note: "Link an incident and use the break-glass policy.",
    version_id: 1,
  },
];

export const demoOverview: Overview = {
  pending: 2,
  active_grants: 14,
  expiring_24h: 2,
  high_risk_pending: 1,
  decisions_today: 18,
  audit_head: "86c7b6e5…8a1c",
};

export const demoPolicies: Policy[] = [
  {
    id: "policy-production-read",
    name: "Production read-only",
    description: "Telemetry and logs, no mutation privileges.",
    resource_prefix: "prod/",
    max_ttl_hours: 24,
    requires_step_up: false,
    approver_group: "on-call",
    active: true,
  },
  {
    id: "policy-production-write",
    name: "Production change access",
    description: "Short-lived write access for an approved change window.",
    resource_prefix: "prod/",
    max_ttl_hours: 4,
    requires_step_up: true,
    approver_group: "platform-leads",
    active: true,
  },
  {
    id: "policy-staging-admin",
    name: "Staging administration",
    description: "Admin access for release verification and integration tests.",
    resource_prefix: "staging/",
    max_ttl_hours: 12,
    requires_step_up: false,
    approver_group: "engineering",
    active: true,
  },
];

export const demoData: DashboardData = {
  overview: demoOverview,
  requests: demoRequests,
  policies: demoPolicies,
  demo: true,
};
