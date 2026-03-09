import { api } from "./api.js";
import { state } from "./state/store.js";
import { renderArchitecture } from "./views/architecture.js";
import { renderClaimList } from "./views/claimList.js";
import { renderComposer } from "./views/composer.js";
import { renderDetail } from "./views/detail.js";
import { renderOverview } from "./views/overview.js";

const app = document.querySelector("#app");

function shell() {
  app.innerHTML = `
    <div class="shell">
      ${renderOverview(state.overview)}
      <div class="content">
        <div class="stack">
          ${renderClaimList(state.claims, state.selectedClaimId)}
          ${renderComposer(state.tenantId)}
        </div>
        <div class="stack">
          ${renderDetail(state.claimDetail)}
          ${state.overview ? renderArchitecture(state.overview) : ""}
        </div>
      </div>
    </div>
  `;
  wireEvents();
}

async function loadClaims() {
  state.claims = await api.listClaims(state.tenantId);
  if (!state.selectedClaimId && state.claims[0]) {
    state.selectedClaimId = state.claims[0].id;
  }
}

async function loadDetail() {
  if (!state.selectedClaimId) {
    state.claimDetail = null;
    return;
  }
  state.claimDetail = await api.claimDetail(state.selectedClaimId);
  state.claimDetail.validation = await api.validateClaim(state.selectedClaimId);
}

async function refresh() {
  state.overview = await api.overview(state.tenantId);
  await loadClaims();
  await loadDetail();
  shell();
}

function collectForm(form) {
  const data = new FormData(form);
  return {
    tenant_id: data.get("tenant_id"),
    external_claim_ref: data.get("external_claim_ref"),
    claim_type: data.get("claim_type"),
    member_id: data.get("member_id"),
    rendering_provider_id: data.get("rendering_provider_id"),
    billing_provider_id: data.get("billing_provider_id"),
    date_of_service: data.get("date_of_service"),
    place_of_service: data.get("place_of_service"),
    intake_channel: data.get("intake_channel"),
    priority: data.get("priority"),
    clinical_summary: data.get("clinical_summary"),
    lines: [
      {
        line_number: 1,
        cpt_code: data.get("cpt_code"),
        icd10_code: data.get("icd10_code"),
        description: data.get("description"),
        units: 1,
        billed_amount: Number(data.get("billed_amount")),
        modifier: "",
        requires_authorization: ["29881"].includes(data.get("cpt_code")),
      },
    ],
    attachments: [
      {
        attachment_type: "clinical_note",
        file_name: "api-note.txt",
        extracted_text: data.get("attachment_text"),
      },
    ],
  };
}

function wireEvents() {
  document.querySelectorAll("[data-claim-id]").forEach((node) => {
    node.addEventListener("click", async () => {
      state.selectedClaimId = node.dataset.claimId;
      await loadDetail();
      shell();
    });
  });

  const form = document.querySelector("#claim-form");
  if (form) {
    form.addEventListener("submit", async (event) => {
      event.preventDefault();
      const payload = collectForm(form);
      const claim = await api.createClaim(payload);
      state.selectedClaimId = claim.id;
      await refresh();
    });
  }

  document.querySelectorAll("[data-action]").forEach((button) => {
    button.addEventListener("click", async () => {
      if (!state.selectedClaimId) return;
      if (button.dataset.action === "validate") {
        state.claimDetail.validation = await api.validateClaim(state.selectedClaimId);
      }
      if (button.dataset.action === "fraud") {
        await api.fraudCheck(state.selectedClaimId);
        state.claimDetail = await api.claimDetail(state.selectedClaimId);
        state.claimDetail.validation = await api.validateClaim(state.selectedClaimId);
      }
      if (button.dataset.action === "adjudicate") {
        await api.adjudicateClaim(state.selectedClaimId);
        await refresh();
        return;
      }
      shell();
    });
  });
}

async function init() {
  state.tenants = await api.listTenants();
  state.tenantId = state.tenants[0]?.id || "";
  await refresh();
}

init().catch((error) => {
  app.innerHTML = `<section class="panel"><h2>Startup Error</h2><p>${error.message}</p></section>`;
});
