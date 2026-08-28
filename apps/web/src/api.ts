import { demoData } from "./data";
import type { AccessRequest, DashboardData, Overview, Policy, RequestStatus } from "./types";

const apiUrl = (import.meta.env.VITE_API_URL as string | undefined)?.replace(/\/$/, "");
const headers = {
  "Content-Type": "application/json",
  "X-Workspace-ID": "demo",
  "X-Actor": "nora.patel",
  "X-Role": "approver",
};

async function get<T>(path: string): Promise<T> {
  const response = await fetch(`${apiUrl}${path}`, { headers });
  if (!response.ok) throw new Error(`Gatehouse API returned ${response.status}`);
  return response.json() as Promise<T>;
}

export async function loadDashboard(): Promise<DashboardData> {
  if (!apiUrl) return demoData;
  try {
    const [overview, requests, policies] = await Promise.all([
      get<Overview>("/api/v1/overview"),
      get<AccessRequest[]>("/api/v1/access-requests"),
      get<Policy[]>("/api/v1/policies"),
    ]);
    return { overview, requests, policies, demo: false };
  } catch {
    return demoData;
  }
}

export async function decideRequest(id: string, decision: Exclude<RequestStatus, "pending">, note: string): Promise<void> {
  if (!apiUrl) return;
  const response = await fetch(`${apiUrl}/api/v1/access-requests/${id}/${decision === "approved" ? "approve" : "deny"}`, {
    method: "POST",
    headers,
    body: JSON.stringify({ note }),
  });
  if (!response.ok) throw new Error(`Decision failed with ${response.status}`);
}
