from __future__ import annotations

from datetime import datetime, timezone

from app.models import Adjudication, Attachment, AuditEvent, Authorization, Benefit, Claim, ClaimLine, DataBundle, EvidenceItem, FraudAssessment, FraudFactor, GraphPathNode, Member, Policy, Provider, Tenant, ValidationCheck


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


NOW = utc_now()


def build_seed_bundle() -> DataBundle:
    tenant = Tenant(
        id="tenant_aegis",
        name="Aegis Health Plans",
        payer_code="AHP",
        region="Midwest",
        primary_line_of_business="Commercial PPO",
    )

    policy = Policy(
        id="policy_ppo_plus",
        tenant_id=tenant.id,
        plan_name="PPO Plus 500",
        policy_number="AHP-PPO-500",
        product_type="Commercial PPO",
        effective_date="2026-01-01",
        termination_date="2026-12-31",
        requires_referral="conditional",
        manual_excerpt=(
            "Orthopedic arthroscopy is covered when medically necessary. Prior authorization is required "
            "for CPT 29881. Emergency evaluation and ambulance transport are covered without prior authorization."
        ),
        knowledge_tags=["orthopedic", "surgery", "emergency", "authorization", "network"],
    )

    members = [
        Member(
            id="member_1001",
            tenant_id=tenant.id,
            member_number="M-778120",
            first_name="Nina",
            last_name="Patel",
            dob="1989-04-14",
            policy_id=policy.id,
            coverage_status="active",
            risk_tier="standard",
            plan_type="PPO",
        ),
        Member(
            id="member_1002",
            tenant_id=tenant.id,
            member_number="M-778121",
            first_name="Marcus",
            last_name="Green",
            dob="1976-11-02",
            policy_id=policy.id,
            coverage_status="active",
            risk_tier="high",
            plan_type="PPO",
        ),
    ]

    providers = [
        Provider(
            id="provider_ortho",
            tenant_id=tenant.id,
            npi="1649213001",
            organization_name="Great Lakes Orthopedic Center",
            specialty="Orthopedics",
            network_status="in_network",
            fraud_watch_level="baseline",
            average_claim_amount=4200.0,
            state="IL",
        ),
        Provider(
            id="provider_er",
            tenant_id=tenant.id,
            npi="1124099910",
            organization_name="Lakeside Emergency Associates",
            specialty="Emergency Medicine",
            network_status="out_of_network",
            fraud_watch_level="elevated",
            average_claim_amount=1800.0,
            state="IL",
        ),
    ]

    benefits = [
        Benefit(
            id="benefit_1",
            policy_id=policy.id,
            cpt_code="29881",
            service_name="Arthroscopy, knee, meniscectomy",
            coverage_status="covered",
            authorization_required="required",
            network_requirement="in_network",
            annual_limit=2,
            notes="Requires active prior authorization and orthopedic diagnosis support.",
        ),
        Benefit(
            id="benefit_2",
            policy_id=policy.id,
            cpt_code="99284",
            service_name="Emergency department visit, high severity",
            coverage_status="covered",
            authorization_required="not_required",
            network_requirement="any",
            annual_limit=12,
            notes="Emergency services are covered regardless of network status.",
        ),
        Benefit(
            id="benefit_3",
            policy_id=policy.id,
            cpt_code="A0429",
            service_name="Ambulance service, basic life support",
            coverage_status="covered",
            authorization_required="not_required",
            network_requirement="any",
            annual_limit=6,
            notes="Emergency transportation covered when medically necessary.",
        ),
    ]

    authorizations = [
        Authorization(
            id="auth_2001",
            tenant_id=tenant.id,
            member_id="member_1001",
            provider_id="provider_ortho",
            cpt_code="29881",
            status="approved",
            approved_units=1,
            valid_from="2026-02-01",
            valid_to="2026-04-30",
        )
    ]

    approved_claim = Claim(
        id="claim_3001",
        tenant_id=tenant.id,
        external_claim_ref="837P-2026-0001",
        claim_type="professional",
        status="approved",
        member_id="member_1001",
        policy_id=policy.id,
        billing_provider_id="provider_ortho",
        rendering_provider_id="provider_ortho",
        date_of_service="2026-03-02",
        place_of_service="22",
        total_billed_amount=6800.0,
        intake_channel="x12_837",
        priority="high",
        clinical_summary="Post-injury knee locking and MRI-confirmed medial meniscus tear.",
        lines=[
            ClaimLine(
                line_number=1,
                cpt_code="29881",
                icd10_code="S83.241A",
                description="Knee arthroscopy with meniscectomy",
                units=1,
                billed_amount=6800.0,
                modifier="RT",
                requires_authorization=True,
            )
        ],
        attachments=[
            Attachment(
                attachment_type="operative_note",
                file_name="op-note-patel.pdf",
                extracted_text=(
                    "Arthroscopic partial medial meniscectomy completed after conservative treatment failure. "
                    "Prior authorization reference AHP-ORTHO-2001 attached."
                ),
            )
        ],
        extraction={
            "confidence": 0.94,
            "entities": {
                "cpt_codes": ["29881"],
                "icd10_codes": ["S83.241A"],
                "document_indicators": ["authorization_reference", "clinical_supporting_docs"],
                "attachment_types": ["operative_note"],
            },
        },
        fraud=FraudAssessment(score=0.18, level="low", factors=[]),
        adjudication=Adjudication(
            decision_status="approved",
            confidence_score=0.93,
            risk_score=0.18,
            policy_match_score=0.94,
            data_completeness_score=0.98,
            explanation_text=(
                "Approved because the member is active, CPT 29881 is covered, required authorization auth_2001 "
                "was present, and the rendering provider is in network."
            ),
            rules_fired=[
                ValidationCheck(name="member_active", status="pass", detail="Coverage active on DOS.", weight=0.25),
                ValidationCheck(name="prior_authorization", status="pass", detail="Authorization auth_2001 matched CPT 29881.", weight=0.25),
                ValidationCheck(name="network_status", status="pass", detail="Rendering provider is in network.", weight=0.15),
            ],
            policy_evidence=[
                EvidenceItem(source="policy_manual", title="PPO Plus 500 Surgical Benefits", snippet="Orthopedic arthroscopy is covered when medically necessary.", score=0.95, tags=["coverage", "orthopedic"]),
                EvidenceItem(source="policy_manual", title="Authorization Requirement", snippet="Prior authorization is required for CPT 29881.", score=0.97, tags=["authorization"]),
            ],
            graph_path=[
                GraphPathNode(from_node="Member Nina Patel", edge="covered_by", to_node="Policy PPO Plus 500", status="verified"),
                GraphPathNode(from_node="Policy PPO Plus 500", edge="allows", to_node="CPT 29881", status="verified"),
                GraphPathNode(from_node="ClaimLine 1", edge="requires_auth", to_node="Authorization auth_2001", status="verified"),
            ],
        ),
        audit_events=[
            AuditEvent(created_at=NOW, event_type="claim_ingested", actor="system", message="Claim normalized from X12 and staged for hybrid adjudication."),
            AuditEvent(created_at=NOW, event_type="claim_adjudicated", actor="hybrid-agent", message="Claim auto-approved with attached policy and graph evidence.", metadata={"decision": "approved", "confidence": 0.93}),
        ],
        ingestion_payload={"channel": "x12_837", "document_type": "professional claim"},
        created_at=NOW,
        updated_at=NOW,
    )

    review_claim = Claim(
        id="claim_3002",
        tenant_id=tenant.id,
        external_claim_ref="FHIR-2026-0177",
        claim_type="emergency",
        status="manual_review",
        member_id="member_1002",
        policy_id=policy.id,
        billing_provider_id="provider_er",
        rendering_provider_id="provider_er",
        date_of_service="2026-03-05",
        place_of_service="23",
        total_billed_amount=2450.0,
        intake_channel="fhir_claim",
        priority="standard",
        clinical_summary="ED evaluation for chest pain; discharge after negative cardiac workup.",
        lines=[
            ClaimLine(line_number=1, cpt_code="99284", icd10_code="R07.9", description="Emergency department visit", units=1, billed_amount=1950.0),
            ClaimLine(line_number=2, cpt_code="A0429", icd10_code="R07.9", description="Emergency ambulance transport", units=1, billed_amount=500.0),
        ],
        attachments=[
            Attachment(
                attachment_type="clinical_note",
                file_name="ed-note-green.txt",
                extracted_text="Patient arrived by ambulance with chest pain. High-severity workup negative. Observation under two hours, discharged home stable.",
            )
        ],
        extraction={
            "confidence": 0.89,
            "entities": {
                "cpt_codes": ["99284", "A0429"],
                "icd10_codes": ["R07.9"],
                "document_indicators": ["emergency_context"],
                "attachment_types": ["clinical_note"],
            },
        },
        fraud=FraudAssessment(
            score=0.67,
            level="medium",
            factors=[
                FraudFactor(factor="out_of_network_provider", impact=0.23, detail="Provider is out of network but billed emergency codes."),
                FraudFactor(factor="provider_watchlist", impact=0.19, detail="Provider has elevated watch level due to peer-group variance."),
                FraudFactor(factor="billing_variance", impact=0.11, detail="Billed amount exceeds provider average by 36%."),
            ],
        ),
        adjudication=Adjudication(
            decision_status="manual_review",
            confidence_score=0.74,
            risk_score=0.67,
            policy_match_score=0.91,
            data_completeness_score=0.9,
            explanation_text="Manual review required because emergency coverage is likely valid, but pricing variance and provider watchlist signals exceeded the auto-approval threshold.",
            rules_fired=[
                ValidationCheck(name="member_active", status="pass", detail="Coverage active on DOS.", weight=0.25),
                ValidationCheck(name="emergency_coverage", status="pass", detail="Emergency services covered regardless of network status.", weight=0.25),
                ValidationCheck(name="provider_risk", status="warning", detail="Provider watchlist and billing variance require analyst review.", weight=0.2),
            ],
            policy_evidence=[
                EvidenceItem(source="policy_manual", title="Emergency Coverage", snippet="Emergency evaluation and ambulance transport are covered without prior authorization.", score=0.94, tags=["emergency", "coverage"]),
            ],
            graph_path=[
                GraphPathNode(from_node="Member Marcus Green", edge="covered_by", to_node="Policy PPO Plus 500", status="verified"),
                GraphPathNode(from_node="Policy PPO Plus 500", edge="allows", to_node="CPT 99284", status="verified"),
                GraphPathNode(from_node="Provider Lakeside Emergency Associates", edge="network_status", to_node="out_of_network", status="exception_allowed"),
            ],
        ),
        audit_events=[
            AuditEvent(created_at=NOW, event_type="claim_ingested", actor="system", message="FHIR claim intake accepted and normalized."),
            AuditEvent(created_at=NOW, event_type="fraud_flagged", actor="fraud-engine", message="Claim routed to review queue due to elevated provider risk and pricing variance.", metadata={"fraud_level": "medium"}),
        ],
        ingestion_payload={"channel": "fhir_claim", "document_type": "emergency claim"},
        created_at=NOW,
        updated_at=NOW,
    )

    return DataBundle(
        tenants=[tenant],
        members=members,
        providers=providers,
        policies=[policy],
        benefits=benefits,
        authorizations=authorizations,
        claims=[approved_claim, review_claim],
    )
