"""Candidate quality flags (roadmap B-044).

The API — not the UI — decides what is wrong with a draft. Flags
are computed here, server-side, from the draft's own evidence, in
a closed vocabulary the frontend renders verbatim:

- ``low_confidence:<field>``   a supported field the model itself
                               scored under 0.6
- ``missing_required:<field>`` a field the kind cannot publish
                               without (event: title + starts;
                               task: title; decision/question:
                               text) is absent or unsupported
- ``unsupported:<field>``      the field has a value but no quote
                               in the source backs it (B-040)
- ``ambiguous_date:<field>``   the date resolver returned more
                               than one reading (D-22)
- ``unresolved_date:<field>``  a date phrase the resolver does not
                               know — stated, never guessed
- ``conflicting:<field>``      another source's candidate in this
                               group, same kind and same subject,
                               disagrees on this field (B-044's
                               "conflicting across sources")
- ``shared_chunk_unflagged``   the pipeline's coverage flag
                               (B-041) — computed in ai/, merged
                               in by the extraction service

Pure functions over draft dicts: the extraction service calls
this when candidates are persisted, and the candidates service
calls it again after a human edit (an edit can cure a flag or
earn one — either way the API recomputes, the UI never edits
flags directly).
"""

# Below this, a supported field is "the model is not sure".
LOW_CONFIDENCE_THRESHOLD = 0.6

# Fields a kind cannot be approved-as-complete without (the queue
# may still approve a flagged draft — flags inform the human; the
# human decides. Publishing rules belong to Phase 4).
REQUIRED_FIELDS: dict[str, list[str]] = {
    "event": ["title", "starts"],
    "task": ["title"],
    "decision": ["text"],
    "question": ["text"],
}

# The field that names a candidate's subject, per kind — the key
# cross-source conflict detection compares.
SUBJECT_FIELD: dict[str, str] = {
    "event": "title", "task": "title", "decision": "text", "question": "text",
}

# Fields compared for cross-source disagreement, per kind.
CONFLICT_FIELDS: dict[str, list[str]] = {
    "event": ["starts", "place"],
    "task": ["owner", "due"],
    "decision": [],
    "question": [],
}


def _subject(draft: dict) -> str:
    """Normalised subject text of a draft ("" when it has none)."""
    kind = draft.get("kind", "")
    name = SUBJECT_FIELD.get(kind, "title")
    value = draft.get("fields", {}).get(name, {}).get("value")
    return " ".join(str(value).lower().split()) if value else ""


def _comparable(field_entry: dict, field_name: str) -> str | None:
    """The value conflict detection compares for one field: for a
    date field, the RESOLVED date (two drafts agree when they
    resolve alike, even if the raw phrases differed); otherwise
    the normalised value. None = nothing to compare."""
    if field_entry is None:
        return None
    if "resolved_date" in field_entry or "date_readings" in field_entry:
        return field_entry.get("resolved_date")
    value = field_entry.get("value")
    return " ".join(str(value).lower().split()) if value else None


def compute_flags(
    draft: dict,
    *,
    siblings: list[tuple[str | None, dict]] = (),
    own_source_id: str | None = None,
) -> list[str]:
    """Every flag one draft earns.

    ``siblings`` are (source_id, draft) pairs of the group's other
    live candidates of the same kind, for cross-source conflict
    detection; a sibling from the SAME source never conflicts (a
    source disagreeing with itself is a splitting question, which
    B-041's coverage flag already covers).
    """
    kind = draft.get("kind", "")
    fields = draft.get("fields", {})
    flags: list[str] = []

    for name, entry in fields.items():
        value = entry.get("value")
        if value is not None and not entry.get("supported", False):
            flags.append(f"unsupported:{name}")
        if (
            entry.get("supported")
            and (entry.get("confidence") or 0.0) < LOW_CONFIDENCE_THRESHOLD
        ):
            flags.append(f"low_confidence:{name}")
        if entry.get("date_ambiguous"):
            flags.append(f"ambiguous_date:{name}")
        if entry.get("date_phrase") and entry.get("date_matched") is False:
            flags.append(f"unresolved_date:{name}")

    for name in REQUIRED_FIELDS.get(kind, []):
        entry = fields.get(name)
        if entry is None or entry.get("value") is None or not entry.get("supported", False):
            flags.append(f"missing_required:{name}")

    subject = _subject(draft)
    if subject:
        for sibling_source, sibling_draft in siblings:
            if sibling_source == own_source_id:
                continue
            if _subject(sibling_draft) != subject:
                continue
            sibling_fields = sibling_draft.get("fields", {})
            for name in CONFLICT_FIELDS.get(kind, []):
                mine = _comparable(fields.get(name), name)
                theirs = _comparable(sibling_fields.get(name), name)
                if mine is not None and theirs is not None and mine != theirs:
                    flag = f"conflicting:{name}"
                    if flag not in flags:
                        flags.append(flag)
    return flags
