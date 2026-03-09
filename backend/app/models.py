from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field

DecisionStatus = Literal["approved", "denied", "manual_review", "received", "pended"]
CheckStatus = Literal["pass", "fail", "warning"]


class Tenant(BaseModel):
    id: str
    name: str
    payer_code: str
    region: str
    primary_line_of_business: str


class Member(BaseModel):
    id: str
    tenant_id: str
    member_number: str
    first_name: str
    last_name: str
    dob: str
    policy_id: str
    coverage_status: str
    risk_tier: str
    plan_type: str


class Provider(BaseModel):
    id: str
    tenant_id: str
    npi: str
    organization_name: str
    specialty: str
    network_status: str
    fraud_watch_level: str
    average_claim_amount: float
    state: str


class Policy(BaseModel):
    id: str
    tenant_id: str
    plan_name: str
    policy_number: str
    product_type: str
    effective_date: str
    termination_date: str
    requires_referral: str
    manual_excerpt: str
    knowledge_tags: list[str]


class Benefit(BaseModel):
    id: str
    policy_id: str
    cpt_code: str
    service_name: str
    coverage_status: str
    authorization_required: str
    network_requirement: str
    annual_limit: int
    notes: str


class Authorization(BaseModel):
    id: str
    tenant_id: str
    member_id: str
    provider_id: str
    cpt_code: str
    status: str
    approved_units: int
    valid_from: str
    valid_to: str


class ClaimLine(BaseModel):
    line_number: int
    cpt_code: str
    icd10_code: str
    description: str
    units: int
    billed_amount: float
    modifier: str = ""
    requires_authorization: bool = False


class Attachment(BaseModel):
    attachment_type: str
    file_name: str
    extracted_text: str


class ValidationCheck(BaseModel):
    name: str
    status: CheckStatus
    detail: str
    weight: float


class EvidenceItem(BaseModel):
    source: str
    title: str
    snippet: str
    score: float
    tags: list[str] = Field(default_factory=list)


class GraphPathNode(BaseModel):
    from_node: str
    edge: str
    to_node: str
    status: str


class GraphInsight(BaseModel):
    title: str
    status: Literal["supported", "blocked", "warning"]
    detail: str
    evidence: list[str] = Field(default_factory=list)


class GraphReasoningResult(BaseModel):
    entry_point: str
    confidence: float
    decision_hint: Literal["approve", "deny", "review"]
    path: list[GraphPathNode]
    insights: list[GraphInsight]
    ontology_nodes: list[str] = Field(default_factory=list)


class FraudFactor(BaseModel):
    factor: str
    impact: float
    detail: str


class FraudAssessment(BaseModel):
    score: float
    level: str
    factors: list[FraudFactor]
    model_version: str = "hybrid-heuristic-v1"


class Adjudication(BaseModel):
    decision_status: DecisionStatus
    confidence_score: float
    risk_score: float
    policy_match_score: float
    data_completeness_score: float
    explanation_text: str
    rules_fired: list[ValidationCheck]
    policy_evidence: list[EvidenceItem]
    graph_path: list[GraphPathNode]
    graph_reasoning: GraphReasoningResult | None = None


class AuditEvent(BaseModel):
    created_at: str
    event_type: str
    actor: str
    message: str
    metadata: dict[str, Any] = Field(default_factory=dict)


class Claim(BaseModel):
    id: str
    tenant_id: str
    external_claim_ref: str
    claim_type: str
    status: DecisionStatus
    member_id: str
    policy_id: str
    billing_provider_id: str
    rendering_provider_id: str
    date_of_service: str
    place_of_service: str
    total_billed_amount: float
    intake_channel: str
    priority: str
    clinical_summary: str
    lines: list[ClaimLine]
    attachments: list[Attachment]
    extraction: dict[str, Any] = Field(default_factory=dict)
    fraud: FraudAssessment | None = None
    adjudication: Adjudication | None = None
    audit_events: list[AuditEvent] = Field(default_factory=list)
    ingestion_payload: dict[str, Any] = Field(default_factory=dict)
    created_at: str
    updated_at: str


class ClaimCreate(BaseModel):
    tenant_id: str
    external_claim_ref: str
    claim_type: str
    member_id: str
    billing_provider_id: str
    rendering_provider_id: str
    date_of_service: str
    place_of_service: str
    intake_channel: str
    priority: str = "standard"
    clinical_summary: str = ""
    lines: list[ClaimLine]
    attachments: list[Attachment] = Field(default_factory=list)


class ClaimSummary(BaseModel):
    id: str
    external_claim_ref: str
    member_name: str
    provider_name: str
    claim_type: str
    status: str
    date_of_service: str
    total_billed_amount: float
    priority: str
    decision_status: str | None = None
    fraud_level: str | None = None


class DashboardOverview(BaseModel):
    tenant: Tenant
    metrics: dict[str, Any]
    queue_mix: list[dict[str, Any]]
    flagged_claims: list[dict[str, Any]]
    recent_events: list[dict[str, Any]]
    architecture_layers: list[dict[str, Any]]
    ontology: list[dict[str, Any]]


class DataBundle(BaseModel):
    tenants: list[Tenant]
    members: list[Member]
    providers: list[Provider]
    policies: list[Policy]
    benefits: list[Benefit]
    authorizations: list[Authorization]
    claims: list[Claim]
