# Project Memory Map — Group Planning Assistant Backend

*The living map of this project. Updated in the same session as any
architectural change (roadmap §3). Ground truth for design: the
team roadmap `GROUP_PLANNING_ASSISTANT_PYTHON_BACKEND_ROADMAP_2026-10-24.md`
in the goal files; the docs set (18 documents) travels with it.*

## What this is

The Python backend for the Group Planning Assistant (Meta Global AI
Developer Hackathon team entry; build window Oct 26 → Nov 4, 2026).
Volmarr + Yrsa build the backend; Geoffrey + Henry build the
frontend against `OPENAPI.json`. Releases travel as ZIPs on the
roadmap's train (ZIP-0 → Alpha → Beta → RC → Final).

## How to run / how to test

```sh
uv sync --extra dev     # install the exact locked environment
./run.sh                # server on http://127.0.0.1:8000  (--demo seeds first)
./test.sh               # full pytest suite + one-page report
uv run alembic upgrade head   # migration path (GPA_DATABASE_URL)
```

Verified 2026-10-24: fresh `uv sync` → `./run.sh` → `/health` ok;
Alembic up/down/up clean; **472 tests, all passing** (48/340 slices:
Phases 0, 1, 2, and 3 complete). Demo verified offline on the mock
driver (seed + health + demo login, no API key, no network).

## Slice status

### Phase 0 — Foundation (B-001 → B-010): COMPLETE
- B-001 repo+tooling (uv lockfile committed, run.sh/run.ps1 parity,
  protective .gitignore) · B-002 create_app + pydantic-settings
  (GPA_ prefix, prod refuses dev secret in plain words) + JSON/text
  structured logging + request-id middleware · B-003 SQLite WAL +
  synchronous=FULL + foreign_keys=ON + busy_timeout on every
  connection; Alembic wired; migration 0001_initial · B-004
  problem+json chassis + ERROR_CODES registry in errors.py · B-005
  pytest chassis + test.sh one-page report · B-006 export_openapi.py
  + generate_ts_types.py + snapshot contract test · B-007 storage
  protocol + local sha256 content-addressed driver (atomic writes,
  strict key pattern = traversal-proof) · B-008 job chassis
  (enqueue/claim-by-update/backoff/dead-letter, GET /jobs/{id},
  standalone `gpa-worker`) · B-009 idempotent seed loader (natural
  keys) · B-010 health+meta, demo seed (1 group + 1 user),
  make_release_zip.py → **ZIP-0 built** (releases/, sha256 sidecar),
  Bruno skeleton (bruno.json + health.bru + local env).

### Phase 1 — Identity, groups, permissions (B-011 → B-022): COMPLETE
- B-011 users + Argon2id (see Decisions) · B-012 magic links
  (hashed, 30-min, single-use, dev mail = file outbox in
  services/mail.py) · B-013 sessions: hand-rolled HS256 JWT access
  (15 min) + rotating refresh families, reuse-of-old revokes the
  family · B-014 API keys (hashed, prefix shown, scopes
  read/draft/publish/admin, last-used) · B-015 groups + slug
  collisions + private-group 404 rule · B-016 memberships: invite
  (creates claimable passwordless account), accept/decline, role
  changes (owner-only for owner/admin moves), last-owner rule ·
  B-017 deps.py is the only door (require_group_role /
  require_scope); verified: **no router imports any model** ·
  B-018 agent seats: seat keys, seat audit labels, candidate stub —
  seat can draft, can never approve (403 seat_cannot_approve,
  enforced in the service) · B-019 append-only audit, same-transaction
  writer, GET /groups/{id}/audit (admin+) · B-020 password reset +
  password change + email change (token to the NEW address); all
  revoke existing sessions · B-021 per-IP token-bucket on auth
  routes, 429 + Retry-After · B-022 role-matrix suite green
  (tests/test_permissions.py: 5 roles × 8 actions, parametrized).

### Phase 2 — Sources and ingest (B-023 → B-034): ✅ COMPLETE (2026-10-24)
- B-023 sources core: `Source`/`SourceChunk`/`Provenance` models
  (models/sources.py), services/sources.py, routers/sources.py —
  create/list/get/delete under `/groups/{id}/sources`, permission
  record (granted_by = caller label, granted_scope verbatim) on
  every source, chunks ordered by position, source ids never leak
  across groups. Deletion law: chunks + their provenance are
  removed; candidates are NEVER deleted — a candidate naming the
  source keeps its `source_id` and gains `source_deleted_at`
  (tombstone columns on Candidate, plain values, no cascade FK).
- B-024 paste ingest: services/paste.py — speaker-line parsers for
  WhatsApp (bracket + dash), Discord headers, Slack headers,
  Messenger blocks (bare name + trailing timestamp line), generic
  `Name:` lines; unparsed/wrapped lines join the previous message
  and leading text becomes a senderless chunk — nothing is dropped.
  Timestamps are kept raw (`timestamp_text`) and parsed to
  `sent_at` only for unambiguous numeric formats; relative words
  are Phase 3's date resolver's job. `POST /groups/{id}/sources/paste`.
- B-025 file ingest: services/files.py — raw-body upload at
  `POST /groups/{id}/sources/upload?filename=` (no multipart
  dependency); size limit `GPA_MAX_UPLOAD_BYTES` (default 10 MiB);
  virus hook (`virus_scan`: EICAR signature + executable magics);
  content sniffing decides the kind (PDF/HTML/ICS/text) — a
  disguised executable is refused whatever its extension says;
  stdlib extraction (HTML via html.parser with script/style
  skipped, PDF text layer via FlateDecode + Tj/TJ strings, ICS one
  chunk per VEVENT, text by paragraphs). Bytes go to B-007 storage,
  a `FileAsset` row and the source land in one transaction.
- B-026 newsletter ingest: services/newsletter.py — HTML email →
  one chunk per section (h1/h2/h3/hr), links inline as
  `anchor text (URL)`, images → alt text or the marked placeholder
  `[image: no description]`, script/style/head never chunked.
  `POST /groups/{id}/sources/newsletter` (raw body, like upload).
  Golden fixture tests/golden/newsletter.html: twelve events stay
  twelve ordered sections behind the greeting preamble chunk.
- B-027 images: services/images.py — magic-byte sniff (PNG/JPEG/
  GIF/WebP), Pillow EXIF transpose, ≤2400px normalise, 320px JPEG
  thumbnail, `Flyer` row (models/sources.py) whose `alt_text` starts
  as the literal "awaiting description" with `alt_text_status`
  exposed — an undescribed image is a visible defect. Source gained
  `stage`/`progress` (B-033's read model). Migration 0002.
- B-028 board photos: same route with `board=true` — ONE source,
  kind `board_photo`, status/stage `awaiting_segmentation`, exactly
  one placeholder chunk (`region_json {"placeholder": true}`); the
  `Flyer.parent_flyer_id`/`region_json` columns await Phase 5.
- B-029 link ingest: services/linkfetch.py is the ONE guarded fetch
  road — http/https only, every resolved IP must be `is_global`
  (metadata IPs + metadata hostnames blocked), redirects followed
  manually (≤5) with each hop re-validated, 2 MiB cap. Transport +
  resolver are injectable seams; tests use a fake internet and
  never touch the real one. services/links.py archives the page
  (bytes + FileAsset + chunks, final URL on `Source.url`,
  migration 0003). Refusals: 422 `fetch_blocked`, 502
  `fetch_failed`; a failed fetch archives nothing.
- B-030 email-in: services/emailin.py — per-group `InboundAddress`
  (token hashed via `hash_secret`, shown once, prefix kept);
  admin+ `POST /groups/{id}/inbound-address`; webhook-shaped
  receiver `POST /api/v1/email-in/{token}` making `email` sources
  with `granted_by = "system:email-in"` and the sender on every
  chunk. Forged token → 401 `token_invalid` + `email_in.rejected`
  audit row (group NULL) + log line. Provider wiring is Phase 12.
- B-031 voice: services/voice.py — audio magic-sniff (WAV/MP3/
  Ogg/FLAC/M4A), stored asset, `voice` source in stage
  `awaiting_transcription` with one plain-words note chunk, and a
  `transcribe` job enqueued via B-008 (id in the response; status
  via `GET /api/v1/jobs/{id}`). The handler (services/transcribe.py)
  is an honest stub — verifies the note exists, completes, and
  leaves the status awaiting; the real driver is Phase 5.
- B-032 live-chat registration: services/live.py guards the only
  door — granting principal must be a PERSON (seats refused 403),
  scope non-empty (else 422), connector kind + external id
  required. `chat_live` source, status `registered`, binding on
  `Source.connector_kind`/`external_id` (migration 0004). The
  receiver that fills it is Phase 12.
- B-033 status + stream: sources report `stage` + `progress`
  (since B-027); `Job.progress` added (migration 0005 — the
  chassis sets 100 on completion; exposed in JobResponse);
  `GET /groups/{id}/stream` (member+) serves SSE from
  services/stream.py — one `snapshot` frame, then `job.progress`
  frames — POLLED FROM THE JOB TABLE, the durable record, never
  an in-memory bus. Honest boundary: synchronous ingests
  (paste/file/newsletter/image/link) land final stage/progress in
  the create response and never pass through a job; the stream
  carries job-driven work (transcription today).
- B-034 phase gate: tests/test_ingest_corpus.py runs the whole
  corpus (chat paste + golden newsletter + 3 flyers incl. a
  sideways EXIF photo + board photo + voice note) through the API
  in one group — 7 sources, kinds/counts/states/permissions
  asserted. OPENAPI.json + frontend_types.ts regenerated
  (42 paths, 40 schemas); FRONTEND_HANDOFF.md carries the
  upload-screen notes. Phase 2 folds into ZIP-Alpha (Wed Oct 28)
  per the roadmap train — no ZIP cut at this gate.

### Phase 3 — The AI adapter and the extraction engine (B-035 → B-048): ✅ COMPLETE (2026-10-24)

- **B-035 adapter protocol** (`ai/client.py`): `MetaModelClient`
  (complete_text / complete_json / read_image / transcribe,
  keyword-only args), tiers spark/wonder, `ModelResult` (text,
  data, model_id, tokens, integer `cost_micros`). Process-wide
  registry; `build_client(settings)` factory — driver swap is
  config only. No vendor SDK imports anywhere in domain code
  (the live driver speaks httpx directly).
- **B-036 mock + fixture drivers**: mock synthesises the smallest
  schema-valid instance; fixture replays recordings keyed by
  sha256(prompt + canonical schema + media hash), missing =
  loud `FixtureMissError`, never an invented answer.
- **B-037 live driver**: POST `{GPA_AI_API_BASE}/chat/completions`,
  env-only secrets, retries with jitter on 429/5xx + transport
  errors only, a succeeded call never duplicated (parse happens
  outside the retry loop), per-call usage/cost into `ai_usage`
  (migration `0006_phase3_ai` also grew `Candidate`
  (draft_json/confidence/flags/prompt/job/merge/resulting-entity)
  and `groups.ai_daily_budget_micros`). **Stubbed-transport tests
  only — never run against a real endpoint.**
- **B-038 prompt library** (`ai/prompts/`): 9 templates + output
  JSON Schema beside each; `manifest.json` pins version + SHA-256
  per template — editing a prompt without a version bump fails
  load + tests; every candidate records its prompt name/version.
- **B-039 date resolver** (`ai/dates.py`, D-22): deterministic;
  "this weekday" passed → BOTH readings flagged; slash dates
  both readings; ordinals skip short months; unknown = matched
  False, never a guess. 268-case golden suite incl. the two
  demo lines (Wed 2026-10-21 → Sat 10-24; 2026-10-28 → Sat 10-31).
- **B-040/B-041/B-042 extraction pipeline** (`ai/extraction.py`):
  one pipeline, four kinds; chunk windows (≤40 chunks, ≤12k
  chars); per-field quote verification (unmatched quote →
  `supported: false`, no provenance, confidence excluded); dates
  resolved from the provenance chunk's sent-at in the group tz;
  one repair retry on malformed output, then ModelError; the
  12-section newsletter yields 12 candidates; coverage check
  flags unflagged shared chunks on all claimants.
- **B-043 review queue API** (`routers/candidates.py`,
  `services/candidates.py`): list (kind/status/min_confidence),
  detail with full provenance, PATCH edit (status `edited`,
  flags recomputed by the API), reject, merge (loser kept whole,
  `merged_into_id` set). Approve extended to `edited` drafts in
  services/groups.py. Security suite: no direct event-create
  route exists (404/405), member approve 403, draft-scoped key
  approve 403 insufficient_scope, seat approval still refused
  in-service (B-018). **Boundary: approval records the decision;
  `resulting_entity_*` stays NULL — Phase 4 (B-049) mints.**
- **B-044 quality flags** (`services/quality.py`): closed
  vocabulary computed server-side — low_confidence /
  missing_required / unsupported / ambiguous_date /
  unresolved_date / conflicting (cross-source, flagged on BOTH
  sides) / shared_chunk_unflagged. Clients never send flags.
- **B-045 extraction jobs** (`services/extraction.py`): `extract`
  job per source (202 + job id, organiser+); machine author
  `system:extraction`, requester on job/audit; re-runs supersede
  the same source+kind's undecided drafts only — decided rows
  are never touched; sources awaiting transcription/segmentation
  are skipped with an audit row, not failed.
- **B-046 evaluation harness** (`ai/evaluation.py` +
  `eval_corpus.json` + `eval_baseline.json`): per-field
  precision/recall over the golden corpus (dates scored on the
  RESOLVED date); corpus deliberately imperfect (place 0.50,
  cost recall 0.00) so the gate can see red; >2-point drop vs
  baseline fails the gate test; `python -m gpa.ai.evaluation`
  prints the table.
- **B-047 budget** (`services/usage.py`): per-group daily cap
  (`ai_daily_budget_micros`, set via group PATCH — settable and
  changeable, not clearable to null under the route's
  exclude_none convention), usage ledger, gate checked before
  each kind's step (per model call for single-window sources);
  at cap the run defers to next UTC midnight as a new job and
  `GET /candidates/status` reports `paused` / `"budget"` /
  spend / cap in plain words. The gate re-reads the cap fresh
  (session-expire) — a long-lived worker never paces by stale
  settings.
- **B-048 gate**: `tests/test_phase3_gate.py` — golden chat →
  candidates (quotes/confidences/flags) → approval; golden
  newsletter → exactly 12 candidates. OPENAPI.json +
  frontend_types.ts regenerated (**47 paths, 47 schemas**);
  FRONTEND_HANDOFF.md carries the review-queue notes. Phase 3
  folds into ZIP-Alpha (Wed Oct 28) — no ZIP cut at this gate.

### Later phases: NOT STARTED (per roadmap order)
Phase 4 begins at B-049 (events minted from approvals — it fills
the `resulting_entity_*` link Phase 3 deliberately left NULL).

## Decisions & deviations (from the roadmap defaults)

- **Password hashing: argon2-cffi** (the roadmap allowed pwdlib or
  argon2-cffi; chose the direct reference binding — fewer layers,
  Argon2id via PasswordHasher defaults). Recorded here per B-011.
- **JWT: implemented in-house** on stdlib hmac/hashlib (security.py)
  instead of adding PyJWT — the format is three base64url parts and
  an HMAC; owning it keeps the dependency list exactly the
  roadmap's and the behaviour fully testable (D-46 spirit).
- **Email validation: in-house** small validator
  (services/identity.normalize_email) instead of pydantic EmailStr,
  which would have required the extra email-validator package.
- **Initial Alembic migration** builds from model metadata
  (create_all/drop_all) rather than op-by-op DDL — at revision 0001
  the models are the reviewed schema; later migrations are
  hand-written as usual. Noted in the migration file itself.
- **Seats' group context**: an invited (not yet active) person can
  reach a private group with role=None so accept/decline works;
  everyone else gets the 404. Implemented in deps.get_group_context.
- Test suite takes ~1 minute, almost all of it Argon2 hashing in
  registrations — acceptable; revisit only if it slows the train.
- **No new dependencies in Phase 2** — the roadmap's B-025 escape
  hatch (add pypdf) was NOT needed: B-025's stdlib PDF text-layer
  reader (FlateDecode + Tj/TJ) covers text-layer PDFs, and
  scanned-image PDFs are refused in plain words until Phase 5
  OCR. Pillow (already locked for B-027) is the only imaging lib.
- **Uploads are raw request bodies** (+ `filename` query param),
  uniformly — file, newsletter, image, voice. No multipart
  anywhere; the frontend handoff says so in bold.
- **Migrations 0002–0005 are inspector-guarded** add/drop: 0001
  builds from live model metadata, so a fresh database already
  has every column when the later revisions run; the guards keep
  up/down/up clean on both fresh and pre-Phase-2 databases
  (tests/test_migrations_phase2.py).
- **Concurrency note (2026-10-24)**: B-023→B-025 were built by
  the 10-minute forge cron and B-026→B-034 by a subagent in one
  sitting; one overlapping edit (candidate tombstone columns) was
  absorbed cleanly by the cron's slice. The `.forge-lock` file
  was accidentally committed once — it is removed again; treat a
  lock in the tree as stale if its timestamp is old.

## Standing laws in force here

- No Docker, anywhere, ever (native installs + uv only).
- All code is the team's own original work (D-46); third-party
  software enters only as installed, locked dependencies.
- Licence: **undecided** — "Licence: to be decided by the team — all
  rights reserved." No file may presume one (no licence field in
  pyproject, no classifiers). Business/licence decisions rest with
  Geoffrey & Henry.
- Commit-before-answer (services commit, then routers respond);
  entered data is sacred (WAL + FULL).
- Heavy plain-words comments (D-26): header on every file,
  docstrings everywhere.
- Local git commits only. No remote, no push, ever, unless Volmarr
  says otherwise in so many words.
