export type Risk = "low" | "medium" | "high" | "critical";
export type RequestStatus = "pending" | "approved" | "denied";

export type AccessRequest = {
  id: string;
  resource: string;
  permission: "read" | "write" | "admin";
  environment: "development" | "staging" | "production";
  requester: string;
  reason: string;
  risk: Risk;
  status: RequestStatus;
  requested_at: string;
  expires_at: string;
  decided_at: string | null;
  decided_by: string | null;
  decision_note: string | null;
  version_id: number;
};

export type Overview = {
  pending: number;
  active_grants: number;
  expiring_24h: number;
  high_risk_pending: number;
  decisions_today: number;
  audit_head: string | null;
};

export type Policy = {
  id: string;
  name: string;
  description: string;
  resource_prefix: string;
  max_ttl_hours: number;
  requires_step_up: boolean;
  approver_group: string;
  active: boolean;
};

export type DashboardData = {
  overview: Overview;
  requests: AccessRequest[];
  policies: Policy[];
  demo: boolean;
};
