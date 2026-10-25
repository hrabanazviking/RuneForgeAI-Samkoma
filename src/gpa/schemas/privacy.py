"""Privacy wire shapes (Phase 13): group export + erasure
(B-143) and the per-person / per-group privacy surfaces
(B-144). Kept apart from the domain schemas because these
shapes answer to privacy law, not to a domain.
"""

from pydantic import BaseModel, Field


class EraseRequest(BaseModel):
    """The double confirmation (B-143): the group's EXACT
    name, typed back, and the word ERASE. Anything less is a
    422 and the group stands untouched — a destructive act
    must be impossible to perform by accident or by a stray
    client retry with a stale body."""

    confirm_name: str = Field(min_length=1, max_length=160)
    confirm_word: str = Field(min_length=1, max_length=16)


class EraseResponse(BaseModel):
    """What an erasure reports: the fact, the per-table row
    counts that were destroyed, and how many stored files went
    with them. Never any content — the content is gone, and
    the receipt must not become a copy of it."""

    group_id: str
    erased: bool
    deleted: dict[str, int]
    storage_objects_removed: int
