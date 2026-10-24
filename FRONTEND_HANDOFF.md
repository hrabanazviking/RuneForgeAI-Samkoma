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

**New in Phase 2 (so far): sources.** `POST/GET /groups/{id}/sources`,
`GET/DELETE /groups/{id}/sources/{source_id}` (delete is organiser+),
`POST /groups/{id}/sources/paste` (chat exports — WhatsApp, Discord,
Slack, Messenger, `Name:` lines — parsed into speaker chunks), and
`POST /groups/{id}/sources/upload?filename=<name>` (raw file bytes as
the request body; text/HTML/PDF-text-layer/Markdown/.ics; 10 MiB cap;
executables refused by content sniffing). Every source carries its
permission record (`granted_by`, `granted_scope`) and ordered chunks
with `sender`, `sent_at` (only when unambiguous), and the raw
`timestamp_text`. You can now build the upload + paste screens and a
source list. Still ahead in Phase 2: newsletter/image/board/link/
email-in/voice kinds and ingest progress (B-026 → B-034).

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
