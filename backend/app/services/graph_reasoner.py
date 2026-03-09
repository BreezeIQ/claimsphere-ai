from __future__ import annotations

from app.models import GraphInsight, GraphPathNode, GraphReasoningResult


class GraphReasoner:
    def analyze(self, claim, member, policy, provider, benefits, authorizations) -> GraphReasoningResult:
        benefit_map = {benefit.cpt_code: benefit for benefit in benefits}
        auth_map = {auth.cpt_code: auth for auth in authorizations if auth.status == "approved"}

        path: list[GraphPathNode] = [
            GraphPathNode(
                from_node=f"Member {member.first_name} {member.last_name}",
                edge="covered_by",
                to_node=f"Policy {policy.plan_name}",
                status="verified",
            ),
            GraphPathNode(
                from_node=f"Provider {provider.organization_name}",
                edge="network_status",
                to_node=provider.network_status,
                status="verified",
            ),
        ]
        insights: list[GraphInsight] = []
        decision_hint = "approve"
        confidence = 0.78

        if member.coverage_status != "active":
            decision_hint = "deny"
            confidence -= 0.28
            insights.append(
                GraphInsight(
                    title="Coverage relationship missing",
                    status="blocked",
                    detail="The member-to-policy relationship is present, but coverage is not active on the service date.",
                    evidence=[member.member_number, policy.policy_number],
                )
            )
        else:
            insights.append(
                GraphInsight(
                    title="Coverage relationship verified",
                    status="supported",
                    detail="Member enrollment links to an active policy record.",
                    evidence=[member.member_number, policy.policy_number],
                )
            )
            confidence += 0.06

        for line in claim.lines:
            benefit = benefit_map.get(line.cpt_code)
            if benefit is None:
                path.append(
                    GraphPathNode(
                        from_node=f"ClaimLine {line.line_number}",
                        edge="mapped_to",
                        to_node=f"CPT {line.cpt_code}",
                        status="missing_benefit",
                    )
                )
                insights.append(
                    GraphInsight(
                        title=f"Procedure {line.cpt_code} missing from ontology",
                        status="blocked",
                        detail="The claim line cannot traverse to a policy benefit node, so the platform should not auto-adjudicate it.",
                        evidence=[f"ClaimLine {line.line_number}", line.cpt_code],
                    )
                )
                decision_hint = "deny"
                confidence -= 0.22
                continue

            path.append(
                GraphPathNode(
                    from_node=f"Policy {policy.plan_name}",
                    edge="covers",
                    to_node=f"Benefit {benefit.service_name}",
                    status="verified" if benefit.coverage_status == "covered" else "blocked",
                )
            )
            path.append(
                GraphPathNode(
                    from_node=f"Benefit {benefit.service_name}",
                    edge="allows",
                    to_node=f"CPT {line.cpt_code}",
                    status="verified" if benefit.coverage_status == "covered" else "blocked",
                )
            )

            if benefit.coverage_status != "covered":
                insights.append(
                    GraphInsight(
                        title=f"Benefit exclusion for {line.cpt_code}",
                        status="blocked",
                        detail="The policy-to-benefit edge exists but the benefit is not covered for this CPT code.",
                        evidence=[policy.policy_number, benefit.service_name],
                    )
                )
                decision_hint = "deny"
                confidence -= 0.2
            else:
                insights.append(
                    GraphInsight(
                        title=f"Benefit match for {line.cpt_code}",
                        status="supported",
                        detail="The line item successfully traverses from policy to benefit to procedure code.",
                        evidence=[benefit.service_name, line.cpt_code],
                    )
                )
                confidence += 0.04

            auth_required = benefit.authorization_required == "required" or line.requires_authorization
            if auth_required:
                auth = auth_map.get(line.cpt_code)
                path.append(
                    GraphPathNode(
                        from_node=f"ClaimLine {line.line_number}",
                        edge="requires_auth",
                        to_node=auth.id if auth else "missing_authorization",
                        status="verified" if auth else "missing",
                    )
                )
                if auth:
                    insights.append(
                        GraphInsight(
                            title=f"Authorization resolved for {line.cpt_code}",
                            status="supported",
                            detail="The claim line traverses to an approved authorization record.",
                            evidence=[auth.id, line.cpt_code],
                        )
                    )
                    confidence += 0.05
                else:
                    insights.append(
                        GraphInsight(
                            title=f"Authorization missing for {line.cpt_code}",
                            status="warning",
                            detail="The benefit requires prior authorization, but no approved authorization node was found.",
                            evidence=[line.cpt_code],
                        )
                    )
                    if decision_hint != "deny":
                        decision_hint = "review"
                    confidence -= 0.12

            network_ok = benefit.network_requirement == "any" or provider.network_status == "in_network"
            path.append(
                GraphPathNode(
                    from_node=f"Provider {provider.organization_name}",
                    edge="eligible_for",
                    to_node=f"Benefit {benefit.service_name}",
                    status="verified" if network_ok else "exception",
                )
            )
            if network_ok:
                insights.append(
                    GraphInsight(
                        title=f"Network rule satisfied for {line.cpt_code}",
                        status="supported",
                        detail="The provider-to-benefit relationship satisfies the network requirement for this line.",
                        evidence=[provider.network_status, benefit.network_requirement],
                    )
                )
                confidence += 0.02
            else:
                insights.append(
                    GraphInsight(
                        title=f"Network exception for {line.cpt_code}",
                        status="warning",
                        detail="The provider is outside the preferred network path for this benefit and should be reviewed with policy context.",
                        evidence=[provider.network_status, benefit.network_requirement],
                    )
                )
                if decision_hint == "approve":
                    decision_hint = "review"
                confidence -= 0.08

        confidence = round(max(0.05, min(confidence, 0.99)), 2)
        return GraphReasoningResult(
            entry_point=f"Claim {claim.external_claim_ref}",
            confidence=confidence,
            decision_hint=decision_hint,
            path=path,
            insights=insights,
            ontology_nodes=[
                "Member",
                "Policy",
                "Benefit",
                "Provider",
                "ClaimLine",
                "Authorization",
                "ProcedureCode",
            ],
        )
