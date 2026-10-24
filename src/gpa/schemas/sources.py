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
    # A board-photo region box / placeholder marker (B-028), JSON
    # text exactly as stored; null for ordinary text chunks.
    region_json: str | None = None


class FlyerResponse(BaseModel):
    """An image source's picture record (B-027/B-028).

    ``alt_text_status`` is the visible-defect flag: it reads
    ``awaiting_description`` — and ``alt_text`` is the literal
    placeholder — until a real description of the image exists.
    """

    id: str
    source_id: str
    width: int
    height: int
    thumbnail_key: str = ""
    alt_text: str
    alt_text_status: str
    transcript: str = ""


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
    # Ingest stage + 0-100 progress (B-033): the frontend renders
    # an honest progress bar from these two fields alone.
    stage: str = "done"
    progress: int = 100
    chunk_count: int
    storage_key: str | None = None
    file_asset_id: str | None = None
    created_at: str


class SourceDetailResponse(SourceResponse):
    """A source with its chunks, in order (B-023)."""

    chunks: list[ChunkResponse] = Field(default_factory=list)
    # The picture record, when this source is an image (B-027).
    flyer: FlyerResponse | None = None


class PasteIngestRequest(BaseModel):
    """Paste a chat export or plain text as a source (B-024)."""

    title: str = Field(default="", max_length=240)
    text: str = Field(min_length=1, max_length=2_000_000)
    granted_scope: str = Field(default="", max_length=240)
