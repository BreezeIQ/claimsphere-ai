from __future__ import annotations

from datetime import datetime, timezone

from app.models import Adjudication, AuditEvent, Claim, ClaimSummary, DashboardOverview, EvidenceItem, FraudAssessment, FraudFactor, GraphPathNode, ValidationCheck
from app.services.repository import FileRepository


class ClaimsEngine:
    def __init__(self, repository: FileRepository | None = None):
        self.repository = repository or FileRepository()

    def _bundle(self):
        return self.repository.load()

    def _tenant(self, tenant_id: str):
        return next(tenant for tenant in self._bundle().tenants if tenant.id == tenant_id)

    def _member(self, member_id: str):
        return next(member for member in self._bundle().members if member.id == member_id)

    def _provider(self, provider_id: str):
        return next(provider for provider in self._bundle().providers if provider.id == provider_id)

    def _policy(self, policy_id: str):
        return next(policy for policy in self._bundle().policies if policy.id == policy_id)

    def _benefits(self, policy_id: str):
        return [benefit for benefit in self._bundle().benefits if benefit.policy_id == policy_id]

    def _authorizations(self, claim: Claim):
        return [
            auth
            for auth in self._bundle().authorizations
            if auth.tenant_id == claim.tenant_id and auth.member_id == claim.member_id and auth.provider_id == claim.rendering_provider_id
        ]

    def list_tenants(self):
        return self._bundle().tenants

    def list_claims(self, tenant_id: str, status: str | None = None):
        claims = [claim for claim in self._bundle().claims if claim.tenant_id == tenant_id]
        if status:
            claims = [claim for claim in claims if claim.status == status]
        summaries = []
        for claim in claims:
            member = self._member(claim.member_id)
            provider = self._provider(claim.rendering_provider_id)
            summaries.append(
                ClaimSummary(
                    id=claim.id,
                    external_claim_ref=claim.external_claim_ref,
                    member_name=f"{member.first_name} {member.last_name}",
                    provider_name=provider.organization_name,
                    claim_type=claim.claim_type,
                    status=claim.status,
                    date_of_service=claim.date_of_service,
                    total_billed_amount=claim.total_billed_amount,
                    priority=claim.priority,
                    decision_status=claim.adjudication.decision_status if claim.adjudication else None,
                    fraud_level=claim.fraud.level if claim.fraud else None,
                )
            )
        return summaries

    def get_claim(self, claim_id: str) -> Claim:
        bundle = self._bundle()
        return next(claim for claim in bundle.claims if claim.id == claim_id)

    def validate_claim(self, claim_id: str):
        claim = self.get_claim(claim_id)
        member = self._member(claim.member_id)
        provider = self._provider(claim.rendering_provider_id)
        benefits = {benefit.cpt_code: benefit for benefit in self._benefits(claim.policy_id)}
        auths = {auth.cpt_code: auth for auth in self._authorizations(claim) if auth.status == "approved"}

        checks = [
            ValidationCheck(name="member_active", status="pass" if member.coverage_status == "active" else "fail", detail=f"Member coverage is {member.coverage_status}.", weight=0.24),
            ValidationCheck(name="claim_completeness", status="pass" if claim.attachments else "warning", detail="Clinical attachment present." if claim.attachments else "No attachments supplied.", weight=0.16),
        ]
        for line in claim.lines:
            benefit = benefits.get(line.cpt_code)
            if not benefit:
                checks.append(ValidationCheck(name=f"benefit_{line.line_number}", status="fail", detail=f"No benefit mapping found for CPT {line.cpt_code}.", weight=0.2))
                continue
            checks.append(ValidationCheck(name=f"benefit_{line.line_number}", status="pass" if benefit.coverage_status == "covered" else "fail", detail=f"{benefit.service_name} is {benefit.coverage_status}.", weight=0.18))
            auth_required = benefit.authorization_required == "required" or line.requires_authorization
            checks.append(ValidationCheck(name=f"auth_{line.line_number}", status="pass" if (not auth_required or line.cpt_code in auths) else "fail", detail=(f"Authorization {auths[line.cpt_code].id} matched." if line.cpt_code in auths else f"CPT {line.cpt_code} requires authorization."), weight=0.2))
            network_ok = benefit.network_requirement == "any" or provider.network_status == "in_network"
            checks.append(ValidationCheck(name=f"network_{line.line_number}", status="pass" if network_ok else "warning", detail="Network requirement satisfied." if network_ok else "Out-of-network exception requires review.", weight=0.1))
        return checks

    def _fraud_model(self, claim_id: str):
        claim = self.get_claim(claim_id)
        provider = self._provider(claim.rendering_provider_id)
        score = 0.08
        factors = []
        if provider.network_status == "out_of_network":
            score += 0.22
            factors.append(FraudFactor(factor="out_of_network_provider", impact=0.22, detail="Out-of-network billing increases exception-handling risk."))
        if provider.fraud_watch_level == "elevated":
            score += 0.18
            factors.append(FraudFactor(factor="provider_watch_level", impact=0.18, detail="Provider is monitored for peer-group variance."))
        if claim.total_billed_amount > provider.average_claim_amount * 1.25:
            score += 0.17
            factors.append(FraudFactor(factor="billing_variance", impact=0.17, detail="Claim amount exceeds provider benchmark."))
        if any(line.modifier in {"25", "59"} for line in claim.lines):
            score += 0.11
            factors.append(FraudFactor(factor="modifier_pattern", impact=0.11, detail="Modifier mix merits manual review for bundling concerns."))
        score = round(min(score, 0.98), 2)
        level = "low" if score < 0.35 else "medium" if score < 0.7 else "high"
        return FraudAssessment(score=score, level=level, factors=factors)

    def compute_fraud(self, claim_id: str):
        bundle = self._bundle()
        for idx, current in enumerate(bundle.claims):
            if current.id == claim_id:
                fraud = self._fraud_model(claim_id)
                updated = current.model_copy(deep=True)
                updated.fraud = fraud
                updated.updated_at = datetime.now(timezone.utc).isoformat()
                updated.audit_events.insert(0, AuditEvent(created_at=updated.updated_at, event_type="fraud_scored", actor="fraud-engine", message=f"Fraud score recalculated at {fraud.score} ({fraud.level}).", metadata={"score": fraud.score, "level": fraud.level}))
                bundle.claims[idx] = updated
                self.repository.save(bundle)
                return fraud
        raise KeyError(claim_id)

    def _evidence(self, claim: Claim):
        policy = self._policy(claim.policy_id)
        benefits = {benefit.cpt_code: benefit for benefit in self._benefits(claim.policy_id)}
        evidence = []
        for line in claim.lines:
            benefit = benefits.get(line.cpt_code)
            if benefit:
                evidence.append(EvidenceItem(source="policy_manual", title=f"{policy.plan_name} - {benefit.service_name}", snippet=benefit.notes or policy.manual_excerpt, score=0.9 if benefit.coverage_status == "covered" else 0.45, tags=[benefit.coverage_status, benefit.authorization_required, benefit.network_requirement]))
        if not evidence:
            evidence.append(EvidenceItem(source="policy_manual", title=policy.plan_name, snippet=policy.manual_excerpt, score=0.55, tags=policy.knowledge_tags))
        return evidence

    def _graph(self, claim: Claim):
        member = self._member(claim.member_id)
        policy = self._policy(claim.policy_id)
        provider = self._provider(claim.rendering_provider_id)
        graph = [
            GraphPathNode(from_node=f"Member {member.first_name} {member.last_name}", edge="covered_by", to_node=f"Policy {policy.plan_name}", status="verified"),
            GraphPathNode(from_node=f"Provider {provider.organization_name}", edge="network_status", to_node=provider.network_status, status="verified"),
        ]
        auths = {auth.cpt_code: auth for auth in self._authorizations(claim) if auth.status == "approved"}
        for line in claim.lines:
            graph.append(GraphPathNode(from_node=f"ClaimLine {line.line_number}", edge="bills", to_node=f"CPT {line.cpt_code}", status="verified"))
            if line.cpt_code in auths:
                graph.append(GraphPathNode(from_node=f"ClaimLine {line.line_number}", edge="requires_auth", to_node=auths[line.cpt_code].id, status="verified"))
        return graph

    def _completeness(self, checks: list[ValidationCheck]) -> float:
        total = sum(item.weight for item in checks) or 1.0
        earned = 0.0
        for item in checks:
            if item.status == "pass":
                earned += item.weight
            elif item.status == "warning":
                earned += item.weight * 0.5
        return round(earned / total, 2)

    def adjudicate_claim(self, claim_id: str):
        checks = self.validate_claim(claim_id)
        claim = self.get_claim(claim_id)
        evidence = self._evidence(claim)
        graph = self._graph(claim)
        fraud = self._fraud_model(claim_id)
        completeness = self._completeness(checks)
        policy_match = round(max(0.0, min(sum(item.score for item in evidence) / len(evidence) - (0.12 * sum(1 for item in checks if item.status == "fail")), 0.99)), 2)
        risk_score = round(min(0.99, fraud.score + 0.08 * sum(1 for item in checks if item.status == "fail") + 0.03 * sum(1 for item in checks if item.status == "warning")), 2)
        confidence = round(max(0.05, min(0.99, policy_match * 0.45 + completeness * 0.35 + (1 - risk_score) * 0.2)), 2)

        if any(item.name == "member_active" and item.status == "fail" for item in checks):
            status = "denied"
            reason = "Denied because member coverage was not active on the date of service."
        elif any(item.name.startswith("benefit_") and item.status == "fail" for item in checks):
            status = "denied"
            reason = "Denied because at least one billed procedure is not covered under the active policy."
        elif any(item.name.startswith("auth_") and item.status == "fail" for item in checks):
            status = "manual_review"
            reason = "Manual review required because authorization evidence is missing for an auth-gated service."
        elif fraud.level == "high":
            status = "manual_review"
            reason = "Manual review required because fraud risk exceeded the straight-through threshold."
        elif fraud.level == "medium" and confidence < 0.86:
            status = "manual_review"
            reason = "Manual review required because policy coverage is favorable, but pricing or provider risk signals remain elevated."
        else:
            status = "approved"
            reason = "Approved because policy, graph, and fraud checks all met the automation threshold."

        explanation = f"{reason} Key factors: policy match {policy_match:.2f}, fraud score {fraud.score:.2f}, data completeness {completeness:.2f}."
        adjudication = Adjudication(decision_status=status, confidence_score=confidence, risk_score=risk_score, policy_match_score=policy_match, data_completeness_score=completeness, explanation_text=explanation, rules_fired=checks, policy_evidence=evidence, graph_path=graph)

        bundle = self._bundle()
        for idx, current in enumerate(bundle.claims):
            if current.id == claim_id:
                updated = current.model_copy(deep=True)
                updated.fraud = fraud
                updated.adjudication = adjudication
                updated.status = status
                updated.updated_at = datetime.now(timezone.utc).isoformat()
                updated.audit_events.insert(0, AuditEvent(created_at=updated.updated_at, event_type="claim_adjudicated", actor="hybrid-agent", message=f"Claim {status} with confidence {confidence:.2f}.", metadata={"decision": status, "confidence": confidence, "risk_score": risk_score}))
                bundle.claims[idx] = updated
                self.repository.save(bundle)
                return adjudication
        raise KeyError(claim_id)

    def create_claim(self, payload):
        claim = self.repository.create_claim(payload)
        bundle = self._bundle()
        for idx, current in enumerate(bundle.claims):
            if current.id == claim.id:
                updated = current.model_copy(deep=True)
                updated.audit_events.insert(0, AuditEvent(created_at=updated.updated_at, event_type="claim_ingested", actor="api", message="Claim created through intake API and staged for hybrid review."))
                bundle.claims[idx] = updated
                self.repository.save(bundle)
                return updated
        return claim

    def claim_detail(self, claim_id: str):
        claim = self.get_claim(claim_id)
        member = self._member(claim.member_id)
        provider = self._provider(claim.rendering_provider_id)
        policy = self._policy(claim.policy_id)
        return {
            "id": claim.id,
            "tenant_id": claim.tenant_id,
            "external_claim_ref": claim.external_claim_ref,
            "claim_type": claim.claim_type,
            "status": claim.status,
            "date_of_service": claim.date_of_service,
            "place_of_service": claim.place_of_service,
            "total_billed_amount": claim.total_billed_amount,
            "priority": claim.priority,
            "clinical_summary": claim.clinical_summary,
            "member": member.model_dump(),
            "provider": provider.model_dump(),
            "policy": policy.model_dump(),
            "lines": [line.model_dump() for line in claim.lines],
            "attachments": [attachment.model_dump() for attachment in claim.attachments],
            "extraction": claim.extraction,
            "fraud": claim.fraud.model_dump() if claim.fraud else None,
            "adjudication": claim.adjudication.model_dump() if claim.adjudication else None,
            "validation": [item.model_dump() for item in self.validate_claim(claim_id)],
            "audit_events": [event.model_dump() for event in claim.audit_events],
        }

    def dashboard_overview(self, tenant_id: str):
        tenant = self._tenant(tenant_id)
        claims = [claim for claim in self._bundle().claims if claim.tenant_id == tenant_id]
        approved = sum(1 for claim in claims if claim.adjudication and claim.adjudication.decision_status == "approved")
        denied = sum(1 for claim in claims if claim.adjudication and claim.adjudication.decision_status == "denied")
        review = sum(1 for claim in claims if claim.adjudication and claim.adjudication.decision_status == "manual_review")
        recent_events = []
        for claim in claims:
            for event in claim.audit_events[:2]:
                recent_events.append({"claim_id": claim.id, "event_type": event.event_type, "message": event.message, "created_at": event.created_at})
        recent_events = sorted(recent_events, key=lambda item: item["created_at"], reverse=True)[:8]
        flagged_claims = [{"claim_id": claim.id, "member_id": claim.member_id, "status": claim.status, "fraud_level": claim.fraud.level if claim.fraud else "unscored", "decision": claim.adjudication.decision_status if claim.adjudication else "unadjudicated"} for claim in claims if claim.fraud and claim.fraud.level in {"medium", "high"}]
        return DashboardOverview(
            tenant=tenant,
            metrics={"claims": len(claims), "auto_approved": approved, "manual_review": review, "denied": denied, "auto_approval_rate": round((approved / len(claims)) * 100, 1) if claims else 0.0, "total_billed_amount": round(sum(claim.total_billed_amount for claim in claims), 2), "straight_through_target": "70%"},
            queue_mix=[{"label": "Straight-through", "value": approved}, {"label": "Manual review", "value": review}, {"label": "Denied", "value": denied}, {"label": "Received", "value": sum(1 for claim in claims if claim.status == "received")}],
            flagged_claims=flagged_claims,
            recent_events=recent_events,
            architecture_layers=[
                {"name": "Claims Intake", "status": "live", "detail": "X12, FHIR, and attachment intake normalized into a canonical claim object."},
                {"name": "Semantic Retrieval", "status": "live", "detail": "Policy recall over benefit notes and manual excerpts with evidence scoring."},
                {"name": "Graph Reasoning", "status": "live", "detail": "Member-policy-benefit-provider-auth relationships validate exact eligibility paths."},
                {"name": "Fraud Detection", "status": "live", "detail": "Heuristic fraud scoring simulates anomaly, provider abuse, and pricing variance checks."},
                {"name": "Decision Trace", "status": "live", "detail": "Every automated decision stores rules, evidence, graph path, confidence, and audit history."},
            ],
            ontology=[
                {"node": "Member", "edges": ["covered_by Policy", "submits Claim"]},
                {"node": "Policy", "edges": ["covers Benefit", "governs Authorization"]},
                {"node": "Provider", "edges": ["renders ClaimLine", "in Network"]},
                {"node": "ClaimLine", "edges": ["bills ProcedureCode", "requires Authorization"]},
                {"node": "FraudCase", "edges": ["flags Provider", "flags Claim"]},
            ],
        )
