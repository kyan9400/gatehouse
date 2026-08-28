import { useEffect, useMemo, useState } from "react";
import type { FormEvent } from "react";

import { decideRequest, loadDashboard } from "./api";
import { demoData } from "./data";
import type { AccessRequest, DashboardData, RequestStatus } from "./types";
import "./styles.css";

type QueueFilter = "pending" | "all";

const riskLabel: Record<AccessRequest["risk"], string> = {
  low: "Low",
  medium: "Review",
  high: "High",
  critical: "Critical",
};

const timeSince = (value: string) => {
  const minutes = Math.max(1, Math.round((Date.now() - new Date(value).getTime()) / 60_000));
  return minutes < 60 ? `${minutes}m ago` : `${Math.round(minutes / 60)}h ago`;
};

const expiresIn = (value: string) => {
  const hours = Math.round((new Date(value).getTime() - Date.now()) / 3_600_000);
  if (hours < 0) return "expired";
  if (hours < 1) return "under 1h";
  return `${hours}h left`;
};

function App() {
  const [data, setData] = useState<DashboardData>(demoData);
  const [filter, setFilter] = useState<QueueFilter>("pending");
  const [selectedId, setSelectedId] = useState("req-7f2a");
  const [loading, setLoading] = useState(true);
  const [decisionBusy, setDecisionBusy] = useState(false);
  const [toast, setToast] = useState("");
  const [showRequestForm, setShowRequestForm] = useState(false);

  useEffect(() => {
    loadDashboard().then((next) => {
      setData(next);
      setLoading(false);
    });
  }, []);

  const visibleRequests = useMemo(
    () => (filter === "pending" ? data.requests.filter((request) => request.status === "pending") : data.requests),
    [data.requests, filter],
  );
  const selected = data.requests.find((request) => request.id === selectedId) ?? visibleRequests[0];
  const pending = data.requests.filter((request) => request.status === "pending").length;

  const showToast = (message: string) => {
    setToast(message);
    window.setTimeout(() => setToast(""), 3200);
  };

  const decide = async (decision: Exclude<RequestStatus, "pending">) => {
    if (!selected || selected.status !== "pending") return;
    setDecisionBusy(true);
    try {
      await decideRequest(selected.id, decision, decision === "approved" ? "Approved in the access review queue." : "Denied by policy review.");
      setData((current) => ({
        ...current,
        overview: {
          ...current.overview,
          pending: Math.max(0, current.overview.pending - 1),
          high_risk_pending: selected.risk === "high" || selected.risk === "critical" ? Math.max(0, current.overview.high_risk_pending - 1) : current.overview.high_risk_pending,
          decisions_today: current.overview.decisions_today + 1,
        },
        requests: current.requests.map((request) =>
          request.id === selected.id
            ? { ...request, status: decision, decided_by: "nora.patel", decided_at: new Date().toISOString(), decision_note: decision === "approved" ? "Approved in the access review queue." : "Denied by policy review." }
            : request,
        ),
      }));
      showToast(`${selected.id} ${decision}`);
    } catch {
      showToast("The API rejected that decision. Refresh and try again.");
    } finally {
      setDecisionBusy(false);
    }
  };

  const createDemoRequest = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    const request: AccessRequest = {
      id: `req-${Math.random().toString(16).slice(2, 6)}`,
      resource: String(form.get("resource")),
      permission: String(form.get("permission")) as AccessRequest["permission"],
      environment: String(form.get("environment")) as AccessRequest["environment"],
      requester: "nora.patel",
      reason: String(form.get("reason")),
      risk: String(form.get("environment")) === "production" ? "high" : "low",
      status: "pending",
      requested_at: new Date().toISOString(),
      expires_at: new Date(Date.now() + 4 * 3_600_000).toISOString(),
      decided_at: null,
      decided_by: null,
      decision_note: null,
      version_id: 1,
    };
    setData((current) => ({ ...current, requests: [request, ...current.requests], overview: { ...current.overview, pending: current.overview.pending + 1 } }));
    setSelectedId(request.id);
    setShowRequestForm(false);
    showToast("Request added to the review queue");
  };

  return (
    <main className="app-shell">
      <header className="topbar">
        <a className="wordmark" href="#top" aria-label="Gatehouse home"><span className="mark">G</span><span>gatehouse</span></a>
        <div className="topbar-context"><span className="live-dot" /> <span>access control plane</span><span className="slash">/</span><strong>acme-platform</strong><span className="slash">/</span><strong>production</strong></div>
        <div className="topbar-actions"><button className="icon-button" aria-label="Open command palette">⌘ K</button><button className="avatar" aria-label="Signed in as Nora Patel">NP</button></div>
      </header>

      <section className="hero" id="top">
        <div><p className="eyebrow">review desk · 28 august 2026</p><h1>Grant access<br /><em>with evidence.</em></h1><p className="hero-copy">Short-lived permissions, clear ownership, and an audit trail your future self can trust.</p></div>
        <div className="hero-actions"><span className={`mode-pill ${data.demo ? "demo" : "connected"}`}><span className="mode-dot" />{data.demo ? "Demo data" : "API connected"}</span><button className="primary-button" onClick={() => setShowRequestForm(true)}><span>＋</span> New request</button></div>
      </section>

      <section className="metric-strip" aria-label="Access overview">
        <Metric label="Pending review" value={loading ? "—" : String(data.overview.pending)} detail={data.overview.high_risk_pending ? `${data.overview.high_risk_pending} high risk` : "Queue clear"} tone="lime" />
        <Metric label="Active grants" value={loading ? "—" : String(data.overview.active_grants)} detail="Across 4 environments" />
        <Metric label="Expiring soon" value={loading ? "—" : String(data.overview.expiring_24h)} detail="Next 24 hours" tone="amber" />
        <Metric label="Decisions today" value={loading ? "—" : String(data.overview.decisions_today)} detail="100% with a note" />
      </section>

      <section className="workspace-grid">
        <div className="queue-panel panel">
          <div className="panel-heading"><div><p className="eyebrow">inbox</p><h2>Review queue <span>{pending}</span></h2></div><div className="filter-tabs" role="tablist" aria-label="Request filter"><button className={filter === "pending" ? "active" : ""} onClick={() => setFilter("pending")}>Needs review</button><button className={filter === "all" ? "active" : ""} onClick={() => setFilter("all")}>All activity</button></div></div>
          <div className="queue-list">{visibleRequests.map((request) => <RequestRow key={request.id} request={request} selected={selected?.id === request.id} onSelect={() => setSelectedId(request.id)} />)}{visibleRequests.length === 0 && <div className="empty-state">No requests match this view.</div>}</div>
          <div className="panel-footer"><span><span className="pulse" /> Updates live</span><button onClick={() => setFilter("all")}>View audit trail <span>↗</span></button></div>
        </div>

        <div className="detail-panel panel">
          {selected ? <><div className="detail-header"><div><p className="eyebrow">request {selected.id}</p><h2>{selected.resource}</h2></div><span className={`risk-badge ${selected.risk}`}>{riskLabel[selected.risk]} risk</span></div><div className="request-meta"><Meta label="Requested by" value={selected.requester} /><Meta label="Permission" value={`${selected.permission} access`} /><Meta label="Environment" value={selected.environment} /><Meta label="Window" value={expiresIn(selected.expires_at)} /></div><div className="reason-block"><p className="eyebrow">request context</p><p>“{selected.reason}”</p></div><div className="policy-callout"><span className="shield">✦</span><div><strong>{selected.risk === "high" || selected.risk === "critical" ? "Step-up approval required" : "Matches an active policy"}</strong><span>{selected.risk === "high" || selected.risk === "critical" ? "Two-person review is required for production mutations." : "This request is inside the staging administration guardrail."}</span></div></div>{selected.status === "pending" ? <div className="decision-actions"><button className="deny-button" disabled={decisionBusy} onClick={() => decide("denied")}>Deny</button><button className="approve-button" disabled={decisionBusy} onClick={() => decide("approved")}>{decisionBusy ? "Saving…" : "Approve access"}<span>→</span></button></div> : <div className={`decision-result ${selected.status}`}><span>{selected.status === "approved" ? "✓" : "×"}</span><div><strong>Request {selected.status}</strong><small>{selected.decision_note}</small></div></div>}<p className="requested-time">Submitted {timeSince(selected.requested_at)} · version {selected.version_id}</p></> : <div className="empty-state">Select a request to inspect it.</div>}
        </div>

        <aside className="side-column">
          <div className="policy-panel panel"><div className="panel-heading compact"><div><p className="eyebrow">guardrails</p><h2>Active policies</h2></div><span className="count-chip">{data.policies.length}</span></div><div className="policy-list">{data.policies.map((policy) => <div className="policy-item" key={policy.id}><div className="policy-icon">{policy.requires_step_up ? "⌁" : "○"}</div><div><strong>{policy.name}</strong><span>{policy.description}</span><small>{policy.resource_prefix} · max {policy.max_ttl_hours}h{policy.requires_step_up ? " · step-up" : ""}</small></div></div>)}</div></div>
          <div className="audit-panel panel"><div className="panel-heading compact"><div><p className="eyebrow">integrity</p><h2>Audit chain</h2></div><span className="verified">✓ verified</span></div><div className="chain-visual"><div className="chain-node"><span>head</span><strong>{data.overview.audit_head ?? "genesis"}</strong></div><div className="chain-line" /><div className="chain-node faded"><span>previous</span><strong>1a4f3c…d902</strong></div></div><p className="audit-copy">Every decision links to the previous event. Exportable evidence stays verifiable after the request is gone.</p><button className="text-button" onClick={() => setFilter("all")}>Inspect events <span>↗</span></button></div>
        </aside>
      </section>

      {showRequestForm && <div className="modal-backdrop" role="presentation" onMouseDown={(event) => { if (event.target === event.currentTarget) setShowRequestForm(false); }}><form className="request-modal" onSubmit={createDemoRequest}><div className="modal-heading"><div><p className="eyebrow">new request</p><h2>Ask for access</h2></div><button type="button" className="close-button" onClick={() => setShowRequestForm(false)} aria-label="Close">×</button></div><label>Resource<input required name="resource" placeholder="prod/payments/logs" /></label><div className="form-row"><label>Permission<select name="permission" defaultValue="read"><option>read</option><option>write</option><option>admin</option></select></label><label>Environment<select name="environment" defaultValue="staging"><option>development</option><option>staging</option><option>production</option></select></label></div><label>Why do you need it?<textarea required minLength={10} name="reason" placeholder="Explain the change, incident, or verification task…" /></label><button className="approve-button" type="submit">Submit for review <span>→</span></button></form></div>}
      {toast && <div className="toast" role="status">{toast}</div>}
      <footer className="footer"><span>Gatehouse / policy-first access operations</span><span>v0.1.0 · all events UTC</span></footer>
    </main>
  );
}

function Metric({ label, value, detail, tone }: { label: string; value: string; detail: string; tone?: string }) { return <div className="metric"><span className="metric-label">{label}</span><strong className={tone ?? ""}>{value}</strong><span className="metric-detail">{detail}</span></div>; }
function Meta({ label, value }: { label: string; value: string }) { return <div><span>{label}</span><strong>{value}</strong></div>; }
function RequestRow({ request, selected, onSelect }: { request: AccessRequest; selected: boolean; onSelect: () => void }) { return <button className={`request-row ${selected ? "selected" : ""}`} onClick={onSelect}><div className="row-top"><span className={`risk-dot ${request.risk}`} /><span className="request-id">{request.id}</span><span className={`status-text ${request.status}`}>{request.status}</span><span className="row-time">{timeSince(request.requested_at)}</span></div><div className="row-main"><strong>{request.resource}</strong><span>{request.permission} · {request.requester}</span></div><p>{request.reason}</p></button>; }

export default App;
