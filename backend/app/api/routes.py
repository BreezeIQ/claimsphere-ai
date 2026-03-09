from fastapi import APIRouter, HTTPException

from app.models import ClaimCreate
from app.services.claims_engine import ClaimsEngine

router = APIRouter()
engine = ClaimsEngine()


@router.get("/tenants")
def tenants():
    return engine.list_tenants()


@router.get("/overview")
def overview(tenant_id: str):
    return engine.dashboard_overview(tenant_id)


@router.get("/claims")
def claims(tenant_id: str, status: str | None = None):
    return engine.list_claims(tenant_id, status)


@router.post("/claims")
def create_claim(payload: ClaimCreate):
    return engine.create_claim(payload)


@router.get("/claims/{claim_id}")
def claim_detail(claim_id: str):
    try:
        return engine.claim_detail(claim_id)
    except StopIteration as exc:
        raise HTTPException(status_code=404, detail="Claim not found") from exc


@router.post("/claims/{claim_id}/validate")
def validate_claim(claim_id: str):
    try:
        return engine.validate_claim(claim_id)
    except StopIteration as exc:
        raise HTTPException(status_code=404, detail="Claim not found") from exc


@router.post("/claims/{claim_id}/fraud-check")
def fraud_check(claim_id: str):
    try:
        return engine.compute_fraud(claim_id)
    except (StopIteration, KeyError) as exc:
        raise HTTPException(status_code=404, detail="Claim not found") from exc


@router.post("/claims/{claim_id}/adjudicate")
def adjudicate_claim(claim_id: str):
    try:
        return engine.adjudicate_claim(claim_id)
    except (StopIteration, KeyError) as exc:
        raise HTTPException(status_code=404, detail="Claim not found") from exc


@router.get("/claims/{claim_id}/explanation")
def explanation(claim_id: str):
    try:
        claim = engine.claim_detail(claim_id)
    except StopIteration as exc:
        raise HTTPException(status_code=404, detail="Claim not found") from exc
    return {
        "claim_id": claim_id,
        "adjudication": claim.get("adjudication"),
        "fraud": claim.get("fraud"),
        "audit_events": claim.get("audit_events"),
    }
