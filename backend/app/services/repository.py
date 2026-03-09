from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from app.core.config import DATA_FILE
from app.data.seed import build_seed_bundle
from app.models import Claim, ClaimCreate, DataBundle


class FileRepository:
    def __init__(self, file_path: Path = DATA_FILE):
        self.file_path = file_path
        self.file_path.parent.mkdir(parents=True, exist_ok=True)
        if not self.file_path.exists():
            self.save(build_seed_bundle())

    def load(self) -> DataBundle:
        if not self.file_path.exists():
            bundle = build_seed_bundle()
            self.save(bundle)
            return bundle
        payload = json.loads(self.file_path.read_text())
        return DataBundle.model_validate(payload)

    def save(self, bundle: DataBundle) -> None:
        self.file_path.write_text(json.dumps(bundle.model_dump(mode="json"), indent=2))

    def create_claim(self, payload: ClaimCreate) -> Claim:
        bundle = self.load()
        now = datetime.now(timezone.utc).isoformat()
        member = next(member for member in bundle.members if member.id == payload.member_id)
        claim = Claim(
            id=f"claim_{uuid4().hex[:10]}",
            tenant_id=payload.tenant_id,
            external_claim_ref=payload.external_claim_ref,
            claim_type=payload.claim_type,
            status="received",
            member_id=payload.member_id,
            policy_id=member.policy_id,
            billing_provider_id=payload.billing_provider_id,
            rendering_provider_id=payload.rendering_provider_id,
            date_of_service=payload.date_of_service,
            place_of_service=payload.place_of_service,
            total_billed_amount=round(sum(line.billed_amount for line in payload.lines), 2),
            intake_channel=payload.intake_channel,
            priority=payload.priority,
            clinical_summary=payload.clinical_summary,
            lines=payload.lines,
            attachments=payload.attachments,
            extraction={},
            fraud=None,
            adjudication=None,
            audit_events=[],
            ingestion_payload={"channel": payload.intake_channel, "created_via": "api"},
            created_at=now,
            updated_at=now,
        )
        bundle.claims.insert(0, claim)
        self.save(bundle)
        return claim
