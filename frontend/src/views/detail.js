import { currency, labelize } from "../lib/format.js";

function renderChecks(checks = []) {
  return checks.map((check) => `
    <div class="list-item">
      <div class="row-between">
        <strong>${labelize(check.name)}</strong>
        <span class="badge ${check.status}">${labelize(check.status)}</span>
      </div>
      <small>${check.detail}</small>
    </div>
  `).join("");
}

export function renderDetail(claim) {
  if (!claim) {
    return `<section class="panel"><h2>Claim Detail</h2><p>Select a claim to inspect its extraction, policy evidence, and graph path.</p></section>`;
  }
  const fraud = claim.fraud;
  const adj = claim.adjudication;
  return `
    <section class="panel stack">
      <div class="row-between">
        <div>
          <h2>${claim.external_claim_ref}</h2>
          <p class="footer-note">${claim.claim_type} claim · ${claim.status} · billed ${currency(claim.total_billed_amount)}</p>
        </div>
        <div>
          <button data-action="validate">Validate</button>
          <button class="warn" data-action="fraud">Fraud check</button>
          <button class="success" data-action="adjudicate">Adjudicate</button>
        </div>
      </div>
      <div class="detail-grid">
        <div class="card-lite">
          <h3>Member</h3>
          <p><strong>${claim.member.first_name} ${claim.member.last_name}</strong></p>
          <p>${claim.member.member_number} · ${claim.member.coverage_status}</p>
          <p>${claim.member.plan_type} · ${claim.member.risk_tier}</p>
        </div>
        <div class="card-lite">
          <h3>Provider</h3>
          <p><strong>${claim.provider.organization_name}</strong></p>
          <p>${claim.provider.specialty} · ${labelize(claim.provider.network_status)}</p>
          <p>Watchlist ${labelize(claim.provider.fraud_watch_level)}</p>
        </div>
        <div class="card-lite">
          <h3>Policy</h3>
          <p><strong>${claim.policy.plan_name}</strong></p>
          <p>${claim.policy.policy_number} · ${claim.policy.product_type}</p>
          <p>${claim.policy.manual_excerpt}</p>
        </div>
        <div class="card-lite">
          <h3>Extraction</h3>
          <p>Confidence ${claim.extraction.confidence ?? "n/a"}</p>
          <p>CPT ${claim.extraction.entities?.cpt_codes?.join(", ") || "none"}</p>
          <p>ICD-10 ${claim.extraction.entities?.icd10_codes?.join(", ") || "none"}</p>
        </div>
      </div>

      <div class="grid-two">
        <div class="stack">
          <div class="card-lite">
            <h3>Validation Rules</h3>
            <div class="list-clean">${renderChecks(adj?.rules_fired || claim.validation || [])}</div>
          </div>
          <div class="card-lite">
            <h3>Fraud Signals</h3>
            ${fraud ? `
              <p><span class="badge ${fraud.level}">${labelize(fraud.level)}</span> score ${fraud.score}</p>
              <div class="list-clean">
                ${fraud.factors.map((factor) => `<div class="list-item"><strong>${labelize(factor.factor)}</strong><small>${factor.detail} (${factor.impact})</small></div>`).join("") || "<div class=\"list-item\"><small>No active factors.</small></div>"}
              </div>
            ` : `<p class="footer-note">Run a fraud check to generate risk factors.</p>`}
          </div>
        </div>
        <div class="stack">
          <div class="card-lite">
            <h3>Decision Trace</h3>
            ${adj ? `
              <p><span class="badge ${adj.decision_status}">${labelize(adj.decision_status)}</span> confidence ${adj.confidence_score}</p>
              <p>${adj.explanation_text}</p>
              <p>Policy match ${adj.policy_match_score} · Risk ${adj.risk_score} · Completeness ${adj.data_completeness_score}</p>
            ` : `<p class="footer-note">Run adjudication to produce an evidence-backed decision trace.</p>`}
          </div>
          <div class="card-lite">
            <h3>Policy Evidence</h3>
            <div class="list-clean">
              ${(adj?.policy_evidence || []).map((item) => `<div class="list-item"><strong>${item.title}</strong><small>${item.snippet}</small><small>Score ${item.score}</small></div>`).join("") || `<div class="list-item"><small>No evidence attached yet.</small></div>`}
            </div>
          </div>
          <div class="card-lite">
            <h3>Graph Reasoning Path</h3>
            <div class="list-clean">
              ${(adj?.graph_path || []).map((item) => `<div class="list-item"><strong>${item.from_node}</strong><small>${item.edge} → ${item.to_node} · ${item.status}</small></div>`).join("") || `<div class="list-item"><small>No graph path attached yet.</small></div>`}
            </div>
          </div>
        </div>
      </div>

      <div class="grid-two">
        <div class="card-lite">
          <h3>Claim Lines</h3>
          <div class="list-clean">
            ${claim.lines.map((line) => `<div class="list-item"><strong>${line.cpt_code}</strong><small>${line.description} · ICD ${line.icd10_code} · ${currency(line.billed_amount)}</small></div>`).join("")}
          </div>
        </div>
        <div class="card-lite">
          <h3>Audit Trail</h3>
          <div class="list-clean">
            ${claim.audit_events.map((event) => `<div class="list-item"><strong>${labelize(event.event_type)}</strong><small>${event.message}</small><small>${event.created_at}</small></div>`).join("")}
          </div>
        </div>
      </div>
    </section>
  `;
}
