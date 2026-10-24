"""Source schemas: sources and their chunks (Phase 2, B-023+).

The create shape carries the permission record with it — a caller
cannot create a source without saying who grants it (the caller's
own label, filled by the router from the principal) and what scope
was granted. Chunk input is how text-native ingests (paste, B-024)
hand ordered content to the core.
"""

from pydantic import BaseModel, Field


class ChunkIn(BaseModel):
    """One chunk of content handed to the sources core."""

    text: str = Field(default="", max_length=100_000)
    sender: str | None = Field(default=None, max_length=160)
    # The raw timestamp words from the export, kept verbatim; parsing
    # relative dates is the date resolver's job (Phase 3), not ingest's.
    timestamp_text: str | None = Field(default=None, max_length=120)


class ChunkResponse(BaseModel):
    """One chunk as read back, in source order."""

    id: str
    position: int
    text: str
    sender: str | None = None
    sent_at: str | None = None
    timestamp_text: str | None = None


class SourceCreateRequest(BaseModel):
    """Create a text-native source with its chunks (B-023)."""

    kind: str = Field(max_length=24)
    title: str = Field(default="", max_length=240)
    # What the granting member allowed, in their flow's own words.
    granted_scope: str = Field(default="", max_length=240)
    chunks: list[ChunkIn] = Field(default_factory=list)


class SourceResponse(BaseModel):
    """A source as lists show it: the container + permission record."""

    id: str
    group_id: str
    kind: str
    title: str
    granted_by: str
    granted_scope: str
    status: str
    chunk_count: int
    storage_key: str | None = None
    file_asset_id: str | None = None
    created_at: str


class SourceDetailResponse(SourceResponse):
    """A source with its chunks, in order (B-023)."""

    chunks: list[ChunkResponse] = Field(default_factory=list)


class PasteIngestRequest(BaseModel):
    """Paste a chat export or plain text as a source (B-024)."""

    title: str = Field(default="", max_length=240)
    text: str = Field(min_length=1, max_length=2_000_000)
    granted_scope: str = Field(default="", max_length=240)
