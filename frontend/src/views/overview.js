import { currency, percent } from "../lib/format.js";

export function renderOverview(overview) {
  if (!overview) {
    return "<div class=\"panel\">Loading overview...</div>";
  }
  const metrics = overview.metrics;
  return `
    <section class="hero">
      <div class="row-between">
        <div>
          <h1>ClaimSphere AI</h1>
          <p>Enterprise healthcare claims intake, hybrid adjudication, fraud scoring, and audit-ready reasoning in one reviewer workbench.</p>
        </div>
        <div class="badge">${overview.tenant.name} · ${overview.tenant.payer_code}</div>
      </div>
      <div class="topbar">
        <div class="metrics">
          <div class="metric"><small>Total claims</small><strong>${metrics.claims}</strong></div>
          <div class="metric"><small>Auto-approved</small><strong>${metrics.auto_approved}</strong></div>
          <div class="metric"><small>Manual review</small><strong>${metrics.manual_review}</strong></div>
          <div class="metric"><small>Total billed</small><strong>${currency(metrics.total_billed_amount)}</strong></div>
          <div class="metric"><small>Auto-approval rate</small><strong>${percent(metrics.auto_approval_rate)}</strong></div>
        </div>
      </div>
    </section>
  `;
}
