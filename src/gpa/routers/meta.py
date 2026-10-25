"""Meta routes: health and deployment info (roadmap B-010, §5).

``GET /health`` is deliberately at the root, unauthenticated —
a load balancer or an operator's curl must be able to ask
without a login. It began as process + database; B-155
deepened it (services/health.py): the same small answer now
carries the job queue's shape, the configured drivers, and a
storage probe, and it answers 503 when the database is down,
because "process up, database dead" is not healthy.
"""

from fastapi import APIRouter, Depends, Request
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from gpa import __version__
from gpa.db import get_db
from gpa.schemas.core import HealthResponse, MetaResponse
from gpa.services import health as health_service

router = APIRouter(tags=["meta"])


@router.get("/health", response_model=HealthResponse)
def health(request: Request, db: Session = Depends(get_db)):
    """Liveness, deepened: database, jobs, drivers, storage."""
    result = health_service.deep_health(
        db,
        database=request.app.state.db,
        settings=request.app.state.settings,
        storage=request.app.state.storage,
    )
    body = HealthResponse(
        status=result["status"],
        version=__version__,
        database=result["checks"]["database"]["status"],
        checks=result["checks"],
    )
    if result["status"] == "down":
        # The body stays the health shape; the CODE says down.
        return JSONResponse(status_code=503, content=body.model_dump())
    return body


@router.get("/api/v1/meta", response_model=MetaResponse)
def meta(request: Request) -> MetaResponse:
    """Public facts about this deployment for clients and tooling."""
    return MetaResponse(
        name="Group Planning Assistant",
        version=__version__,
        api="v1",
        openapi="/openapi.json",
    )
