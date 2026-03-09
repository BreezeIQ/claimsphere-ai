export function renderArchitecture(overview) {
  return `
    <section class="panel stack">
      <div class="row-between">
        <div>
          <h2>Hybrid Architecture</h2>
          <p class="footer-note">Vector recall first, graph precision second, then bounded decisioning and audit evidence.</p>
        </div>
      </div>
      <div class="arch-grid">
        ${overview.architecture_layers.map((layer) => `<div class="arch-box"><strong>${layer.name}</strong><small>${layer.status}</small><p>${layer.detail}</p></div>`).join("")}
      </div>
      <div class="grid-two">
        <div class="card-lite">
          <h3>Claims Ontology</h3>
          <div class="list-clean">
            ${overview.ontology.map((node) => `<div class="list-item"><strong>${node.node}</strong><small>${node.edges.join(" · ")}</small></div>`).join("")}
          </div>
        </div>
        <div class="card-lite">
          <h3>Flagged Queue</h3>
          <div class="list-clean">
            ${overview.flagged_claims.map((claim) => `<div class="list-item"><strong>${claim.claim_id}</strong><small>${claim.member_id} · ${claim.decision} · fraud ${claim.fraud_level}</small></div>`).join("") || `<div class="list-item"><small>No flagged claims.</small></div>`}
          </div>
        </div>
      </div>
    </section>
  `;
}
