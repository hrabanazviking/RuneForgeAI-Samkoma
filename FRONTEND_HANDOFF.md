# Frontend Handoff — ZIP-0 (Foundation) + Phase 1

*Regenerated at each release. Read this first.*

## What you have

A running backend with the full identity + groups + permissions
layer working and tested (92 tests green). You can now build:

- **Sign-in screens** — register, password login, magic-link login,
  refresh, logout, password reset, email change.
- **Group home** — create/read/update groups, visibility rules.
- **Member management** — invites (accept/decline), roles, removal,
  the agent-seat list, and the group audit view (admin+).

**New in Phase 2: sources — all ingest kinds are in.**
`POST/GET /groups/{id}/sources`, `GET/DELETE /groups/{id}/sources/{source_id}`
(delete is organiser+; deleting a source that feeds a candidate
tombstones the link — the candidate is never silently orphaned).
Every source carries its permission record (`granted_by`,
`granted_scope`), a `stage` + `progress`, and ordered chunks with
`sender`, `sent_at` (only when unambiguous), the raw
`timestamp_text`, and `region_json` where a chunk maps to a place
in a picture. The ingest doors, all under `/groups/{id}/sources/`:

- `paste` (JSON `{text}`) — chat exports (WhatsApp, Discord, Slack,
  Messenger, `Name:` lines) parsed into speaker chunks; unparsed
  lines are preserved verbatim, never dropped.
- `upload?filename=<name>` — **raw file bytes as the request body
  (not multipart)**; text/HTML/PDF-text-layer/Markdown/.ics;
  10 MiB cap; executables refused by content sniffing, not by
  extension. Scanned-image PDFs (no text layer) are refused in
  plain words — OCR is Phase 5.
- `newsletter?filename=<name>` — raw HTML email body; one chunk
  per section, links kept whole as `anchor text (URL)`, images
  become their alt text or the marked placeholder
  `[image: no description]`.
- `image?filename=<name>[&board=true]` — flyer/photo upload (raw
  body). The response's `flyer` object carries the normalised
  picture (EXIF orientation applied, ≤2400px, thumbnail stored)
  and — build your UI around this — `alt_text` +
  `alt_text_status`: an image starts as the literal text
  "awaiting description" with status `awaiting_description`.
  **An undescribed image is a visible defect**: show that state
  plainly (it clears when the Phase 5 vision pass writes a real
  description). With `board=true` the upload is a whiteboard
  photo: ONE source, status `awaiting_segmentation`, one
  placeholder chunk — region crops arrive in Phase 5; do not
  build region UI yet.
- `link` (JSON `{url}`) — the server fetches and ARCHIVES the
  page's text as chunks and records the final URL in `url`
  (redirects followed). Private/LAN/cloud-metadata addresses are
  refused with 422 `fetch_blocked`; an unreadable page is 502
  `fetch_failed` and archives nothing. Show the archived state,
  not a live embed — the archive is the point.
- `voice?filename=<name>` — raw audio (WAV/MP3/Ogg/FLAC/M4A,
  sniffed by content). The response adds `transcription_job_id` +
  `transcription_status`; the source sits in stage
  `awaiting_transcription` until the Phase 5 driver lands. Poll
  `GET /api/v1/jobs/{id}` or watch the stream (below).
- `live` (JSON `{connector_kind, external_id, granted_scope}`) —
  registers a live-chat source: the permission record itself.
  **Scope is mandatory** (empty → 422) and **seats cannot grant**
  (403) — the grant UI is people-only. No chunks flow yet; the
  receiver is Phase 12.
- `POST /groups/{id}/inbound-address` (admin+) — opens the
  group's email-in channel; the response shows the `token` and
  `address` **once only** (only a hash is kept — a lost token
  means re-issue). Mail delivered to `POST /api/v1/email-in/{token}`
  becomes an `email` source with `granted_by: "system:email-in"`.

**Ingest progress:** synchronous ingests (paste/upload/newsletter/
image/link) return final `stage`/`progress` in the create
response. Job-driven work streams: `GET /groups/{id}/stream`
(SSE, member+) emits one `snapshot` frame on connect, then
`job.progress` frames (`job_id`, `kind`, `status`, `progress`,
`source_id`) as the group's jobs move. Jobs also carry `progress`
in `GET /api/v1/jobs/{id}` (100 when done).

Not yet built (later phases): the full review queue,
events/calendar, notifications. The `candidates` endpoints
are a Phase 1 stub that exists to prove the seat permission rule.

## The contract

- `OPENAPI.json` in this ZIP is the exact contract the tests passed
  against. `frontend_types.ts` is generated from it — use the types.
- Base path `/api/v1`. Health at `GET /health` (no auth).
- Auth: `Authorization: Bearer <access token>` (15 min) for people;
  `X-Api-Key: gpa_...` for agent seats and integrations.
- Every error is RFC 9457 problem+json with a stable `code` field —
  branch on `code`, never on message text. Codes live in
  `src/gpa/errors.py` (the registry is the contract).
- Private groups return **404** (not 403) to non-members. Build
  your "group not found" state accordingly.
- Agent seats can draft candidates and can **never** approve them —
  the API returns 403 `seat_cannot_approve`. Approval UI is for
  people (organiser+) only.

## Run it

```sh
uv sync
./run.sh            # or: ./run.sh --demo  (loads the demo seed)
curl http://127.0.0.1:8000/health
```

Demo account (from `seeds/demo.json`): `demo@example.org` /
`demo-password-123`. Bruno collection skeleton in `collections/` —
the health request runs against a fresh server as-is.
