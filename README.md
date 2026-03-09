# ClaimSphere AI

ClaimSphere AI is a fresh greenfield demo repo for an enterprise healthcare insurance claims processor built from the supplied PRD. It implements a modular hybrid-adjudication workflow with seeded claims, policy evidence, graph-style reasoning paths, fraud scoring, reviewer actions, and a browser workbench served by FastAPI.

## Repo Layout

- `backend/app/main.py`: FastAPI entrypoint and static app hosting.
- `backend/app/models.py`: Domain models for tenants, members, policies, claims, fraud, adjudication, and audit events.
- `backend/app/services/repository.py`: File-backed demo repository for seeded and API-created claims.
- `backend/app/services/claims_engine.py`: Validation, fraud scoring, adjudication, dashboard metrics, and decision trace logic.
- `backend/app/api/routes.py`: Claims, overview, validation, fraud-check, adjudication, and explanation endpoints.
- `frontend/index.html`: Static reviewer shell.
- `frontend/src/`: Modular browser-side API, state, and view renderers.

## Implemented Product Capabilities

- Claims intake for seeded and API-created claims.
- Deterministic validation for coverage, completeness, authorization, and network exceptions.
- Hybrid-style adjudication that combines policy evidence, graph path generation, and fraud scoring.
- Fraud scoring with provider/network/pricing heuristics.
- Audit trail for ingestion and adjudication events.
- Reviewer workbench showing queue, detail, evidence, graph path, fraud signals, and architecture blueprint.
- New claim intake form to exercise the platform end to end.

## Suggested Production Stack

This demo keeps infrastructure lightweight, but the PRD-oriented production recommendation remains:

- Backend services: FastAPI for AI services, Java/Kotlin Spring Boot for heavy adjudication and policy services at scale.
- Orchestration: Temporal.
- Streaming: Kafka.
- Data: PostgreSQL, S3, Redis, Snowflake, Neo4j/Neptune, and Qdrant/Weaviate.
- AI/ML: ClinicalBERT/BioClinicalBERT, BGE/OpenAI embeddings, reranking, XGBoost, Isolation Forest.
- Platform: Kubernetes, Terraform, Helm, Argo CD, OpenTelemetry, Grafana, Datadog.
- Security: Okta/Entra, Vault/Secrets Manager, KMS, OPA, immutable audit logging.

## Run Locally

1. Create and activate a Python 3.11+ virtual environment.
2. Install backend dependencies:
   `pip install -e ./backend`
3. Start the app:
   `uvicorn app.main:app --app-dir backend --reload`
4. Open [http://localhost:8000](http://localhost:8000)

## API Surface

- `GET /api/tenants`
- `GET /api/overview?tenant_id=tenant_aegis`
- `GET /api/claims?tenant_id=tenant_aegis`
- `POST /api/claims`
- `GET /api/claims/{id}`
- `POST /api/claims/{id}/validate`
- `POST /api/claims/{id}/fraud-check`
- `POST /api/claims/{id}/adjudicate`
- `GET /api/claims/{id}/explanation`

## Notes

- The repository persists demo state to `backend/app/data/claimsphere_demo.json` at runtime.
- The current implementation is intentionally lightweight and deterministic enough to run locally without external infrastructure.
- The UI is static-module based to keep the project self-contained and easy to run in restricted environments.
