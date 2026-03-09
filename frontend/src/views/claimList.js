import { currency, labelize } from "../lib/format.js";

function badgeClass(value) {
  return `${value || ""}`.replaceAll(" ", "_");
}

export function renderClaimList(claims, selectedClaimId) {
  return `
    <section class="panel stack">
      <div class="row-between">
        <div>
          <h2>Claims Queue</h2>
          <p class="footer-note">Reviewer queue with seeded claims and new API-created claims.</p>
        </div>
      </div>
      <div class="claim-list">
        ${claims.map((claim) => `
          <article class="claim-card ${claim.id === selectedClaimId ? "active" : ""}" data-claim-id="${claim.id}">
            <div class="claim-head">
              <strong>${claim.external_claim_ref}</strong>
              <span class="badge ${badgeClass(claim.decision_status || claim.status)}">${labelize(claim.decision_status || claim.status)}</span>
            </div>
            <p>${claim.member_name} · ${claim.provider_name}</p>
            <div class="row-between">
              <small>${claim.claim_type} · DOS ${claim.date_of_service}</small>
              <small>${currency(claim.total_billed_amount)}</small>
            </div>
            <div class="row-between">
              <span class="badge ${badgeClass(claim.priority)}">${labelize(claim.priority)}</span>
              <span class="badge ${badgeClass(claim.fraud_level || "unscored")}">Fraud ${labelize(claim.fraud_level || "unscored")}</span>
            </div>
          </article>
        `).join("")}
      </div>
    </section>
  `;
}
