"""Source routes (roadmap B-023, B-024).

Sources and their chunks, nested under their group. Every handler
authorises through gpa.deps — ``require_group_role`` for role gates,
``require_scope`` for credential gates — and defers every rule to
services/sources.py (paste parsing lives in services/paste.py).
Routers never touch a model directly (B-017).
"""

from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from gpa.db import get_db
from gpa.deps import GroupContext, Principal, require_group_role, require_scope
from gpa.schemas.sources import (
    ChunkResponse,
    PasteIngestRequest,
    SourceCreateRequest,
    SourceDetailResponse,
    SourceResponse,
)
from gpa.services import paste as paste_service
from gpa.services import sources as source_service

router = APIRouter(prefix="/api/v1/groups", tags=["sources"])


def _source_response(db: Session, source) -> SourceResponse:
    """Shape a source for list views (with its chunk count)."""
    return SourceResponse(
        id=source.id, group_id=source.group_id, kind=source.kind,
        title=source.title, granted_by=source.granted_by,
        granted_scope=source.granted_scope, status=source.status,
        chunk_count=source_service.chunk_count(db, source),
        storage_key=source.storage_key, file_asset_id=source.file_asset_id,
        created_at=source.created_at.isoformat(),
    )


def _detail_response(db: Session, source) -> SourceDetailResponse:
    """Shape a source with all of its chunks, in order."""
    base = _source_response(db, source)
    chunks = [
        ChunkResponse(
            id=c.id, position=c.position, text=c.text, sender=c.sender,
            sent_at=c.sent_at.isoformat() if c.sent_at else None,
            timestamp_text=c.timestamp_text,
        )
        for c in source_service.list_chunks(db, source)
    ]
    return SourceDetailResponse(**base.model_dump(), chunks=chunks)


@router.post("/{group_id}/sources", response_model=SourceDetailResponse, status_code=201)
def create_source(
    body: SourceCreateRequest,
    context: GroupContext = Depends(require_group_role("member")),
    principal: Principal = Depends(require_scope("draft")),
    db: Session = Depends(get_db),
):
    """Create a text-native source with its chunks (member+).

    The permission record's ``granted_by`` is the caller — filled
    here from the principal, never trusted from the request body.
    """
    source = source_service.create_source(
        db, actor_label=principal.label, group=context.group,
        kind=body.kind, title=body.title, granted_scope=body.granted_scope,
        chunks=[c.model_dump() for c in body.chunks],
    )
    return _detail_response(db, source)


@router.post(
    "/{group_id}/sources/paste", response_model=SourceDetailResponse, status_code=201
)
def paste_source(
    body: PasteIngestRequest,
    context: GroupContext = Depends(require_group_role("member")),
    principal: Principal = Depends(require_scope("draft")),
    db: Session = Depends(get_db),
):
    """Paste a chat export or plain text; it is parsed into chunks
    by the speaker-line parser (B-024) and stored as one source."""
    chunks = paste_service.parse_paste(body.text)
    source = source_service.create_source(
        db, actor_label=principal.label, group=context.group,
        kind="chat_paste", title=body.title, granted_scope=body.granted_scope,
        chunks=chunks,
    )
    return _detail_response(db, source)


@router.get("/{group_id}/sources", response_model=list[SourceResponse])
def list_sources(
    context: GroupContext = Depends(require_group_role("member")),
    db: Session = Depends(get_db),
):
    """Every source in the group, oldest first (member+)."""
    return [_source_response(db, s) for s in source_service.list_sources(db, context.group)]


@router.get("/{group_id}/sources/{source_id}", response_model=SourceDetailResponse)
def read_source(
    source_id: str,
    context: GroupContext = Depends(require_group_role("member")),
    db: Session = Depends(get_db),
):
    """One source with its chunks, in order (member+)."""
    source = source_service.get_source(db, context.group, source_id)
    return _detail_response(db, source)


@router.delete("/{group_id}/sources/{source_id}", status_code=204)
def delete_source(
    source_id: str,
    context: GroupContext = Depends(require_group_role("organiser")),
    principal: Principal = Depends(require_scope("draft")),
    db: Session = Depends(get_db),
):
    """Delete a source (organiser+). Its chunks and provenance go
    with it; anything drafted from it stays, as a tombstone."""
    source_service.delete_source(
        db, actor_label=principal.label, group=context.group, source_id=source_id
    )
    return None


# --- File upload (B-025) ---------------------------------------------------
# Imported here so the upload route mounts with the sources router;
# the handler itself stays thin and defers to services/files.py.


@router.post(
    "/{group_id}/sources/upload", response_model=SourceDetailResponse, status_code=201
)
async def upload_source(
    request: Request,
    filename: str = "",
    title: str = "",
    granted_scope: str = "",
    context: GroupContext = Depends(require_group_role("member")),
    principal: Principal = Depends(require_scope("draft")),
    db: Session = Depends(get_db),
):
    """Upload one file as a source (member+).

    The file's BYTES are the request body (no multipart form): the
    frontend sends the file with ``filename`` as a query parameter.
    Content is sniffed, never trusted by extension (B-025).
    """
    from gpa.services import files as file_service

    data = await request.body()
    settings = request.app.state.settings
    storage = request.app.state.storage
    source = file_service.ingest_file(
        db, settings=settings, storage=storage,
        actor_label=principal.label, group=context.group,
        filename=filename, data=data,
        title=title, granted_scope=granted_scope,
    )
    return _detail_response(db, source)
