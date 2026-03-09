export function renderComposer(tenantId) {
  return `
    <section class="panel stack">
      <div>
        <h2>New Claim Intake</h2>
        <p class="footer-note">Create a claim from the reviewer workbench to exercise the API end to end.</p>
      </div>
      <form id="claim-form" class="form-grid">
        <input type="hidden" name="tenant_id" value="${tenantId}" />
        <label><span>External ref</span><input name="external_claim_ref" value="API-${Date.now()}" /></label>
        <label><span>Claim type</span><select name="claim_type"><option value="professional">Professional</option><option value="emergency">Emergency</option></select></label>
        <label><span>Member</span><select name="member_id"><option value="member_1001">Nina Patel</option><option value="member_1002">Marcus Green</option></select></label>
        <label><span>Provider</span><select name="rendering_provider_id"><option value="provider_ortho">Great Lakes Orthopedic Center</option><option value="provider_er">Lakeside Emergency Associates</option></select></label>
        <label><span>Billing provider</span><select name="billing_provider_id"><option value="provider_ortho">Great Lakes Orthopedic Center</option><option value="provider_er">Lakeside Emergency Associates</option></select></label>
        <label><span>Date of service</span><input name="date_of_service" type="date" value="2026-03-09" /></label>
        <label><span>Place of service</span><input name="place_of_service" value="22" /></label>
        <label><span>Intake channel</span><select name="intake_channel"><option value="x12_837">X12 837</option><option value="fhir_claim">FHIR Claim</option><option value="document_upload">Document Upload</option></select></label>
        <label><span>Priority</span><select name="priority"><option value="standard">Standard</option><option value="high">High</option></select></label>
        <label class="full"><span>Clinical summary</span><textarea name="clinical_summary">Procedure supported by documentation and ready for hybrid review.</textarea></label>
        <label><span>CPT code</span><select name="cpt_code"><option value="29881">29881</option><option value="99284">99284</option><option value="A0429">A0429</option></select></label>
        <label><span>ICD-10</span><input name="icd10_code" value="S83.241A" /></label>
        <label><span>Description</span><input name="description" value="Knee arthroscopy with meniscectomy" /></label>
        <label><span>Billed amount</span><input name="billed_amount" type="number" value="6800" /></label>
        <label class="full"><span>Attachment note</span><textarea name="attachment_text">Clinical note uploaded and ready for extraction.</textarea></label>
        <div class="full row-between">
          <span class="footer-note">The form creates one-line demo claims; the backend then validates, scores, and adjudicates them.</span>
          <button type="submit">Create Claim</button>
        </div>
      </form>
    </section>
  `;
}
