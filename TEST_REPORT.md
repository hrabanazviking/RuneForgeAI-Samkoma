# Test Report — ZIP-Beta (v0.3, 2026-10-24)

The full suite result for THIS ZIP, from one clean run against
the tree this ZIP was built from (roadmap §8: a ZIP is a
promise — everything the handoff claims is covered here).

## Suite

- **673 passed, 0 failed, 0 errors** (4m38s, pytest, one
  warning: a Starlette TestClient deprecation notice).
- Collected = passed = 673. Reconciliation: 642 at ZIP-Alpha's
  gate (Phase 7) + 31 new Phase 8 tests = 673.
- Contract: 133 OpenAPI paths, 150 schemas — `OPENAPI.json` in
  this ZIP is the exact schema the snapshot test passed
  against; `frontend_types.ts` generated from it.

## Phase 8's new tests (31)

| File | Tests | Covers |
|---|---|---|
| test_notifications_core.py | 4 | B-095 outbox (no inline send), kill-the-mail-server retry + resend, B-102 dead-letter + failure list, bounce webhook |
| test_reminders.py | 11 | B-096 default rules at exact moments, facts in bodies, move-reschedule with no orphans, custom rules, withdrawal; B-100 quiet-hours goldens (New York + Auckland), urgent exemption; B-103 fact-preservation ship/fallback |
| test_change_alerts_invites.py | 5 | B-097 RSVP'd-only alerts, guest-at-invited-address, once-only approval; B-098 public face, guest RSVP attribution, tamper 404, member invite notification |
| test_digest.py | 4 | B-099 golden week in both formats, chain anchoring, settings re-anchor, alt-text law executable |
| test_inbox.py | 5 | B-101 inbox list/mark-read, privacy 404, inbox↔email agreement, SSE nudge, preference switch effect |
| test_migrations_phase8.py | 1 | Migration 0011 up/down/up on a Phase 7-era database |
| test_phase8_gate.py | 1 | B-104: invite → answer → reminder → move → change alert → digest mention, fake clock |

Three assertions in tests/test_rsvps.py were updated as
superseded (the Phase 4 pattern): they counted every `notify`
job as a promotion; since Phase 8 the queue carries all
notifications, so they now select promotion jobs by payload
kind. Their intent — promotions are notified, in line order —
is unchanged and still asserted.

## Evaluation tables (this ZIP)

Extraction (`python -m gpa.ai.evaluation`, fixture driver) —
within tolerance of the recorded baseline:

```
field                  precision  recall correct  pred  gold
--------------------------------------------------------------
decision:text               1.00    1.00       1     1     1
event:cost                  1.00    0.00       0     0     1
event:host                  1.00    1.00       1     0     1
event:place                 0.50    0.50       1     2     2
event:starts                1.00    1.00       2     2     2
event:title                 1.00    1.00       2     2     2
question:text               1.00    1.00       1     1     1
task:owner                  1.00    1.00       1     1     1
task:title                  1.00    1.00       1     1     1
```

Vision (`python -m gpa.ai.vision_evaluation`, fixture driver) —
overall accuracy 0.81 (baseline 0.81, tolerance 0.02):

```
type           cases  accuracy  baseline
clean              1      1.00      1.00
glare              1      0.75      0.75
handwriting        1      0.75      0.75
rotated            1      0.75      0.75
```

## Security posture in this ZIP

- Tokens (invites, API keys, magic links) are hashed at rest
  and shown once — the invite suite proves a tampered token
  creates nothing.
- The public invite face is the B-059 public projection, under
  the same leak discipline as the public calendar.
- Preferences and inboxes are person-only (seats refused);
  another person's inbox item is a 404.
- Migrations 0001–0011 each up/down/up clean; the suite's
  Alembic tests cover 0011 explicitly.

---

# Addendum — Phase 9 (B-112 gate, 2026-10-24; no ZIP)

Phase 9 cut no ZIP (it folds into ZIP-RC at B-138, per the
roadmap's train), so this addendum carries its numbers until
the RC report supersedes it.

## Suite

- **704 passed, 0 failed, 0 errors** — the reconciled clean
  run against the final Phase 9 tree (pytest, one warning: a
  Starlette TestClient deprecation notice). Told plainly, it
  took two runs to earn this line: the first gate run came
  back **703 passed / 1 failed** — the failure was in the
  B-110 test itself, not the code under it (the dry-run test
  asserted the roster was the owner alone, forgetting its own
  fixture's accepted member; the dry run had changed exactly
  nothing, as designed). The same run exposed a latent
  logging defect from the foundation: the request-id filter
  sat on the root LOGGER, whose filters never run for records
  propagated from child loggers, so third-party records
  (httpx) reached the root handler's formatter without a
  request_id and the formatter raised on them; the filter now
  rides the handler, where every emitted record meets it.
  Both fixes landed, and the re-run — temp base on the
  workspace overlay after a /tmp-full run died at 100% tmpfs,
  the standing hazard — is the clean 704 above.
- Collected = passed = 704. Reconciliation: 673 at ZIP-Beta's
  gate (Phase 8) + 31 new Phase 9 tests = 704.
- Contract: 151 OpenAPI paths, 179 schemas (was 133 / 150) —
  `OPENAPI.json` regenerated at this gate is the exact schema
  the snapshot test passed against; `frontend_types.ts`
  generated from it.

## Phase 9's new tests (31)

| File | Tests | Covers |
|---|---|---|
| test_subgroups.py | 5 | B-105 create/enrol/roles, scoping leak tests (list, detail 404, tasks, calendar), delete-refused-while-scoped 409 |
| test_announcements.py | 4 | B-106 organiser-only posting (member 403), seat refused in the service, pinned-first order, expiry + organiser include_expired |
| test_shifts.py | 4 | B-107 headcount slots with windows, claim/release via B-088, gap report golden ("Saturday still needs a driver and a door person.") |
| test_resources.py | 3 | B-108 keeper items, booking rules (cancelled 422, duplicate 409), golden double-booking → resource_overlap flag |
| test_attendance.py | 3 | B-109 marking + idempotence, counts-only reads, the refusal itself (per-person routes 404/405, no identity in aggregates) |
| test_member_io.py | 5 | B-110 messy-CSV golden (dupes, blanks, stray commas) report, dry-run changes nothing, re-import counts, CSV round-trip of a comma name, admin doors |
| test_settings_pack.py | 5 | B-111 defaults, settings change → audit row → two-approver behaviour in one test, review floor opens/closes, validation + doors, budget set/clear |
| test_migrations_phase9.py | 1 | Migration 0012 up/down/up on a Phase 8-era database |
| test_phase9_gate.py | 1 | B-112: import → flyer in → event out → scoped → shifts claimed → attendance → digest sent |

One Phase 4 assertion was updated as superseded (the Phase 8
pattern): tests/test_calendar_views.py's conflict note now
asserts "resource_overlap" — B-108 made Phase 4's deferred
resource-conflict flag real; intent unchanged.

---

# Addendum — Phase 10 (B-122 gate, 2026-10-25; no ZIP)

Phase 10 cut no ZIP (it folds into ZIP-RC at B-138, per the
roadmap's train), so this addendum carries its numbers until
the RC report supersedes it.

## Suite

- **735 passed, 0 failed, 0 errors** — the reconciled clean
  run against the final Phase 10 tree (pytest, one warning:
  a Starlette TestClient deprecation notice), temp base on
  the workspace overlay per the standing /tmp practice.
- Collected = passed = 735. Reconciliation: 704 at the
  Phase 9 gate + 31 new Phase 10 tests = 735.
- Contract: 160 OpenAPI paths, 189 schemas (was 151 / 179) —
  `OPENAPI.json` regenerated at this gate is the exact schema
  the snapshot test passed against; `frontend_types.ts`
  generated from it. The Bruno collections remain the B-010
  skeleton, unchanged (as at the Phase 9 gate).
- Two defects were found and fixed inside the phase's own
  work, both covered by its tests: two `AppError` calls
  passed a `status=` kwarg the error chassis does not take
  (the registry owns statuses — the cross-group purge test
  caught it as a 500), and the recap service's viewer-less
  discussion read met the visibility bright line (a
  viewer-less read sees no events at all); the recap now
  reads at the organiser role its door guarantees.

## Phase 10's new tests (31)

| File | Tests | Covers |
|---|---|---|
| test_pruning.py | 4 | B-113 golden 500-message corpus (recall floor 100%, kept ≤25% of tokens), approved-history-only corpus scope, PruneRun written, the not-embedding-RAG wording + import audit |
| test_migrations_phase10.py | 1 | Migration 0013 up/down/up |
| test_pruning_multipass.py | 5 | B-114 pass-2 recovery of a dropped landmine, pass cap, ceiling, token-budget stop (zero calls, all dropped, flagged), settings round-trip + refusals |
| test_ask.py | 5 | B-115 verified answer with chunk-linked citations, the unverifiable-answer acceptance (fabricated quote → the refusal), gap-pass rescue, nothing-relevant refusal, stranger 404 |
| test_summaries.py | 2 | B-116 summary → 2 pending candidates (system:summary, from_summary), zero Decision/Task rows written; empty thread refused plainly |
| test_briefings.py | 1 | B-117 golden briefing carries the August landmine; role gaps from data; the run's kept set names the landmine chunk |
| test_recaps.py | 1 | B-118 the loop closes: recap draft → approval → newsletter draft → approval → newsletter is a Source and its golden phrase survives a later prune; drafts are not memory; double approval 409 |
| test_local_driver.py | 5 | B-119 wire shape + honest provenance (local model id, zero cost), text-only refusals, config refusals, per-group selection with no silent fallback, driver-swap same-survivors |
| test_memory_runs.py | 3 | B-120 runs inspectable (kept/dropped/model/cost), purge one then all with summaries surviving, organiser door + cross-group purge is a not-found |
| test_pruning_evaluation.py | 2 | B-121 golden set scored through the engine; floors; the deliberate miss asserted by name; table renders |
| test_phase10_gate.py | 2 | B-122 the three demos (ask, briefing, recap) in mock mode (honest refusal) and live mode (live wire path, content-aware stub transport) |

## Pruning evaluation (B-121)

The golden pruning set — human-marked relevant chunks,
scored through the real engine against a recorded judge
(deliberately imperfect, so the table measures rather than
flatters):

| Question | Chunks | Relevant | Kept | Recall | Precision |
| --- | ---: | ---: | ---: | ---: | ---: |
| Where do club nights happen? | 8 | 2 | 2 | 1.00 | 1.00 |
| What did we decide about food for the supper? | 10 | 3 | 4 | 1.00 | 0.75 |
| Who is bringing the marquee and when? | 9 | 2 | 1 | 0.50 | 1.00 |
| What warnings were given about the venue? | 12 | 3 | 3 | 1.00 | 1.00 |
| **Mean** | | | | **0.88** | **0.94** |

## The honest boundary

No real Meta model endpoint or credential exists in this
environment. The gate's "live mode" is the hosted driver's
real code path — wire shape, headers, retries, parsing —
exercised against a stub transport whose answers are
content-aware (it reads the prompt it was sent and judges
the chunks in it). Fixture and mock remain the demo drivers;
nothing in this phase pretends a real model judged anything.
