# Build History & Provenance — Group Planning Assistant Backend

**Read this first if you are judging, reviewing, or inheriting this code.**

This backend was directed by **Volmarr Wyrd** and designed and implemented
by **Yrsa Freydisdottir** (Mythic Engineering), working for Volmarr. That is
not a claim printed on top of the work — it is what the repository's own
history records: **every one of the 211 commits** in this tree is authored
by Yrsa ("Yrsa (for Volmarr)" / "Yrsa Freydisdottir"). No other author appears
anywhere in the history.

- Build window recorded by the commits: **2026-10-24 → 2026-10-26**
- First commit: `671efa6` — Phase 0: foundation chassis (B-001 to B-010)
- Latest commit at the time this record was embedded: `10e4b98` — B-220 Phase 19 gate (built; full-suite proof DEFERRED) + build HALT at Volmarr's order 2026-10-26
- Roadmap progress at that point: **219 of 350 slices** (Phases 0–18 complete,
  Phase 19 in progress); full suite at the Phase 18 gate: **1056 passed,
  7 skipped, 0 failed**.
- Method: roadmap-driven vertical slices, each built, tested, and committed
  in order (B-001 … B-220), under the project's Forge Protocol — the human
  directs what and why; the builder decides implementation and proves each
  slice with its own acceptance tests before the next begins.

This record is embedded in twelve locations and forms across the tree
(root narrative, hidden verbatim log, docs chapter, JSON, CSV, HTML, a
Python data module, the releases folder, the submission folder, and
appendices in RESULTS.md, CHANGELOG.md and PROJECT_MEMORY_MAP.md) so that
the history travels with the code wherever any part of it is copied.

## Milestones

| Commit | Date | Milestone |
|--------|------|-----------|
| `671efa6` | 2026-10-24 | Phase 0: foundation chassis (B-001 to B-010) |
| `bb4c49b` | 2026-10-24 | Phase 1: identity, groups, permissions (B-011 to B-022) |
| `03017c4` | 2026-10-24 | B-034: Phase 2 gate — golden ingest corpus test (chat + newsletter + 3 flyers + board + voice in one group), OPENAPI.json/fronten… |
| `4e2178a` | 2026-10-24 | Phase 3 (part 1): AI adapter protocol + mock/fixture/live drivers (B-035, B-036, B-037) |
| `18b1113` | 2026-10-24 | Phase 3 (part 2): versioned prompt library (B-038) |
| `def46fe` | 2026-10-24 | Phase 3 (part 3): deterministic date resolver (B-039, D-22) |
| `bf356bf` | 2026-10-24 | Phase 3 (part 4): extraction pipeline (B-040, B-041, B-042) |
| `a9a1427` | 2026-10-24 | Phase 3 (part 5): review queue, extraction jobs, budget (B-043/044/045/047) |
| `40e65a5` | 2026-10-24 | Phase 3 (part 6): evaluation harness v1 (B-046) |
| `35e78bd` | 2026-10-24 | Phase 3 (part 7): phase gate + contract + handoff (B-048) |
| `6843c22` | 2026-10-24 | Phase 3: verified counts (472 tests green, mock-driver suite + offline demo verified) |
| `3197d2d` | 2026-10-25 | Phase 4 (part 1): events core — minting, direct entry, change history, cancel/clone (B-049, B-050, B-051) |
| `afdbb40` | 2026-10-25 | Phase 4 (part 2): recurrence API, iCal engine + secret feeds + links, calendar views, projections (B-052, B-053, B-054, B-055, B-… |
| `aa96e45` | 2026-10-25 | Phase 4 (part 3): Facebook Event drafts (B-058) |
| `07df019` | 2026-10-25 | Phase 4 (part 4): phase gate + contract + handoff (B-062) |
| `6d75823` | 2026-10-25 | Phase 4 (correction): superseded Phase 3 security test + verified counts |
| `3fe209c` | 2026-10-25 | Phase 5 (part 1): vision pipeline + segmentation boundary (B-063/B-064 cores, B-066/B-067 adapter side) |
| `dd70bb1` | 2026-10-25 | Phase 5 (part 2): vision service, boards, wall, print, generated images (B-063..B-067, B-069..B-072) |
| `19b1c7a` | 2026-10-25 | Phase 5 (part 3): real transcription through the adapter (B-068) |
| `44de774` | 2026-10-25 | Phase 5 (part 4): vision evaluation, phase gate, contract (B-073, B-074) |
| `d704c3c` | 2026-10-25 | Phase 5 close-out: verified counts in the memory map (553 tests, 74/340) |
| `4f4b4e1` | 2026-10-25 | Phase 6 (part 1): cross-source matching (B-075) |
| `645e2e8` | 2026-10-25 | Phase 6 (part 2): merge service + contradictions (B-076, B-079) |
| `343bf01` | 2026-10-25 | Phase 6 (part 3): change candidates (B-077) |
| `424cdcb` | 2026-10-25 | Phase 6 (part 4): re-announce drafts, tombstones, quality report (B-078, B-080, B-081) |
| `e0f6bbd` | 2026-10-25 | Phase 6 (part 5a): the phase gate (B-082) |
| `03321be` | 2026-10-25 | Phase 6 close-out: memory map + frontend handoff (B-082) |
| `14d6c47` | 2026-10-25 | Phase 7 foundation + B-083 tasks (B-083..B-093 services/routers, migration 0010) |
| `d06fc97` | 2026-10-25 | B-094 phase gate: Flow B (40-message trip argument) end-to-end into event + tasks + decisions + open questions |
| `1960f8e` | 2026-10-25 | Phase 7 complete in the map: 94/340 slices, 642 tests, slice notes + boundaries |
| `9e77e2e` | 2026-10-25 | Phase 8 (part 1): notification schema + outbox core + mail boundary (B-095, B-102) |
| `5f624f1` | 2026-10-25 | Phase 8 (part 2): reminder engine + AI wording (B-096, B-103) |
| `e77e5b6` | 2026-10-25 | Phase 8 (part 3): change alerts + invites (B-097, B-098) |
| `f5336d5` | 2026-10-25 | Phase 8 (part 4): digest + preferences + inbox + stream (B-099, B-100, B-101) |
| `a56666d` | 2026-10-25 | Phase 8 (part 5): tests — 31 new (642 → 673) |
| `5755a93` | 2026-10-25 | B-104 gate: ZIP-Beta artefacts — contract, changelog, test report, handoff, map, release tooling |
| `88900de` | 2026-10-25 | B-112: Phase 9 gate — the nonprofit story end-to-end; contract regenerated (151 paths / 179 schemas); changelog, handoff, memory… |
| `cb4ba10` | 2026-10-25 | B-112 gate corrections: dry-run test asserted its own fixture wrong (roster is owner + fixture member); request-id filter moved o… |
| `b618f1c` | 2026-10-25 | Map: record the B-112 gate findings (test defect, logging filter, /tmp basetemp practice) |
| `9e0b43d` | 2026-10-25 | B-122: Phase 10 gate — the three memory demos (ask, briefing, recap) run on the golden corpus in mock mode (honest refusal; the m… |
| `0754ae5` | 2026-10-25 | B-130: Phase 11 gate — the bridge walked end to end in one scripted test (Samtal hall synced from the fixture double → fixture ex… |
| `f1c0338` | 2026-10-25 | B-138: Phase 12 gate — one event's full outward life in a single scripted test (draft → press → sync → move → both doors repair →… |
| `5722299` | 2026-10-25 | Phase 14 checkpoint papers: B-147..B-149 in the memory map, README progress in place (149/350, 841 tests) |
| `7527bbd` | 2026-10-25 | Phase 13 gate papers: TEST_REPORT Phase 13 addendum — suite reconciliation (835 = 797 + 38), pip-audit output verbatim (ran for r… |
| `c41d693` | 2026-10-25 | Phase 14 gate papers: FREEZE_DRILL.md (the four drill runs, both defects, timings — ships inside ZIP-Final), TEST_REPORT Phase 14… |
| `eb33d70` | 2026-10-25 | Phase 14 checkpoint papers (Yrsa): README status refreshed in place — 151/350, 853 tests, contract 187 paths / 217 schemas, Phase… |
| `4ca7caa` | 2026-10-25 | Phase 15 / B-152: PostgreSQL promotion — real parity suite, verified mover |
| `f24c5a2` | 2026-10-25 | Phase 15 / B-153: native service packaging — systemd units + plain installer |
| `7e9b551` | 2026-10-25 | Phase 15 / B-154: reverse-proxy + TLS guide — followed literally, live |
| `22c08cd` | 2026-10-25 | Phase 15 / B-155: observability — deep /health, the runbook, the requeue fix |
| `fa09b2e` | 2026-10-25 | Phase 15 / B-156: upgrade path — backup, migrate, smoke, swap; rollback is restore |
| `9d8d7cd` | 2026-10-25 | Phase 15 gate fix: /health deep checks are signed-in-only — B-155 reconciled with the Phase 13 threat model |
| `ce9028d` | 2026-10-25 | Phase 15 gate: regenerate the contract snapshot for the /health docstring |
| `9263ca4` | 2026-10-25 | Phase 15 gate: test_sqlite_pragmas joins the PG-mode skip set |
| `f9ce3a2` | 2026-10-25 | Phase 15 gate: PG-mode isolation learns module-scoped worlds |
| `612ba7d` | 2026-10-25 | Phase 15 gate: Alembic's fileConfig must not silence the host's loggers |
| `187477f` | 2026-10-25 | Phase 15 checkpoint papers: memory map, TEST_REPORT Phase 15 addendum, CHANGELOG |
| `4d552f5` | 2026-10-25 | Checkpoint papers (Phase 16 gate): memory map, TEST_REPORT addendum, CHANGELOG, FRONTEND_HANDOFF |
| `d02d8dd` | 2026-10-25 | Phase 17 enabler: cryptography dependency (AES-256-GCM + Ed25519 for B-163/B-167, wheels on every Tier-1 target) |
| `b0dfe3e` | 2026-10-25 | B-176 Comment + documentation gate: AST checker (purpose headers, migration/prompt whys, env comments, no restatement docstrings)… |
| `b0d7ec2` | 2026-10-25 | B-180 Phase 17 gate drill: resumable-upload flyer -> worker dies mid-vision-job -> startup recovery requeues -> job completes ->… |
| `0ed3dcd` | 2026-10-26 | Phase 17 gate repair: first PG-mode run of the Phase 17 tests found four SQLite-bound tests (B-167 raw-file greps x2, B-169 bundl… |
| `66f88fb` | 2026-10-26 | Phase 17 gate fix (production): audit chain head race on PostgreSQL — B-170's read-prev/hash/advance dance in audit.record was se… |
| `50b15bd` | 2026-10-26 | Phase 17 gate repair 2 (test isolation): PG per-test reset now also drops alembic_version — the table is not a model table, so th… |
| `7547930` | 2026-10-26 | Phase 17 gate papers: drill totals filled from the runs' own logs (SQLite 1026/7/0 in two declared halves, PG 1006/27/0 + parity… |
| `9cd6524` | 2026-10-26 | B-200 Documentation proof — Phase 18 gate: three cold reads as executable/audit legs (guide I checklist parsed from docs/01 and i… |
| `6fd1cf2` | 2026-10-26 | Phase 18 gate papers (checkpoint): README refreshed in place (200/350, 1056 passing SQLite — tests line had lagged two gates, cor… |
| `10e4b98` | 2026-10-26 | B-220 Phase 19 gate (built; full-suite proof DEFERRED) + build HALT at Volmarr's order 2026-10-26 |

## Every commit, in order

| # | Commit | Date | Subject |
|---|--------|------|---------|
| 1 | `671efa6` | 2026-10-24 | Phase 0: foundation chassis (B-001 to B-010) |
| 2 | `bb4c49b` | 2026-10-24 | Phase 1: identity, groups, permissions (B-011 to B-022) |
| 3 | `dcfa56b` | 2026-10-24 | Tests, frozen contract, and project docs |
| 4 | `2db337c` | 2026-10-24 | B-023: sources core — Source/SourceChunk/Provenance, permission record, chunk ordering, tombstone delete |
| 5 | `b0ca1fa` | 2026-10-24 | B-024: paste ingest golden tests — WhatsApp/Discord/Slack/Messenger/Name-colon parsers, never-drop law |
| 6 | `2fbe7bf` | 2026-10-24 | B-025: file ingest — content sniffing over extension, virus hook, FileAsset + storage + extracted chunks, siz… |
| 7 | `6b1d412` | 2026-10-24 | Docs: memory map + handoff for Phase 2 slices B-023 to B-025 |
| 8 | `6527cab` | 2026-10-24 | B-026: newsletter ingest — HTML email to ordered section chunks, links kept with anchor text, images as alt t… |
| 9 | `f20d31b` | 2026-10-24 | B-027+B-028: image ingest — EXIF-upright flyer normalisation + thumbnails + Flyer row with awaiting-descripti… |
| 10 | `c47a40f` | 2026-10-24 | B-029: link ingest — one SSRF-guarded fetch helper (public-address-only, per-hop redirect revalidation, metad… |
| 11 | `8a1fe02` | 2026-10-24 | B-030: email-in ingest — per-group inbound token (hashed, shown once), webhook-shaped receiver creating email… |
| 12 | `4c18820` | 2026-10-24 | B-031 + B-032: voice-note ingest (magic-byte audio sniff, stored asset, awaiting-transcription source, transc… |
| 13 | `6e938a0` | 2026-10-24 | B-033: ingest status + progress — sources report stage/progress (since B-027); jobs gain a real progress colu… |
| 14 | `03017c4` | 2026-10-24 | B-034: Phase 2 gate — golden ingest corpus test (chat + newsletter + 3 flyers + board + voice in one group),… |
| 15 | `4e2178a` | 2026-10-24 | Phase 3 (part 1): AI adapter protocol + mock/fixture/live drivers (B-035, B-036, B-037) |
| 16 | `18b1113` | 2026-10-24 | Phase 3 (part 2): versioned prompt library (B-038) |
| 17 | `def46fe` | 2026-10-24 | Phase 3 (part 3): deterministic date resolver (B-039, D-22) |
| 18 | `bf356bf` | 2026-10-24 | Phase 3 (part 4): extraction pipeline (B-040, B-041, B-042) |
| 19 | `a9a1427` | 2026-10-24 | Phase 3 (part 5): review queue, extraction jobs, budget (B-043/044/045/047) |
| 20 | `40e65a5` | 2026-10-24 | Phase 3 (part 6): evaluation harness v1 (B-046) |
| 21 | `35e78bd` | 2026-10-24 | Phase 3 (part 7): phase gate + contract + handoff (B-048) |
| 22 | `6843c22` | 2026-10-24 | Phase 3: verified counts (472 tests green, mock-driver suite + offline demo verified) |
| 23 | `3197d2d` | 2026-10-25 | Phase 4 (part 1): events core — minting, direct entry, change history, cancel/clone (B-049, B-050, B-051) |
| 24 | `afdbb40` | 2026-10-25 | Phase 4 (part 2): recurrence API, iCal engine + secret feeds + links, calendar views, projections (B-052, B-0… |
| 25 | `aa96e45` | 2026-10-25 | Phase 4 (part 3): Facebook Event drafts (B-058) |
| 26 | `07df019` | 2026-10-25 | Phase 4 (part 4): phase gate + contract + handoff (B-062) |
| 27 | `6d75823` | 2026-10-25 | Phase 4 (correction): superseded Phase 3 security test + verified counts |
| 28 | `3fe209c` | 2026-10-25 | Phase 5 (part 1): vision pipeline + segmentation boundary (B-063/B-064 cores, B-066/B-067 adapter side) |
| 29 | `dd70bb1` | 2026-10-25 | Phase 5 (part 2): vision service, boards, wall, print, generated images (B-063..B-067, B-069..B-072) |
| 30 | `19b1c7a` | 2026-10-25 | Phase 5 (part 3): real transcription through the adapter (B-068) |
| 31 | `44de774` | 2026-10-25 | Phase 5 (part 4): vision evaluation, phase gate, contract (B-073, B-074) |
| 32 | `d704c3c` | 2026-10-25 | Phase 5 close-out: verified counts in the memory map (553 tests, 74/340) |
| 33 | `4f4b4e1` | 2026-10-25 | Phase 6 (part 1): cross-source matching (B-075) |
| 34 | `645e2e8` | 2026-10-25 | Phase 6 (part 2): merge service + contradictions (B-076, B-079) |
| 35 | `343bf01` | 2026-10-25 | Phase 6 (part 3): change candidates (B-077) |
| 36 | `424cdcb` | 2026-10-25 | Phase 6 (part 4): re-announce drafts, tombstones, quality report (B-078, B-080, B-081) |
| 37 | `e0f6bbd` | 2026-10-25 | Phase 6 (part 5a): the phase gate (B-082) |
| 38 | `03321be` | 2026-10-25 | Phase 6 close-out: memory map + frontend handoff (B-082) |
| 39 | `14d6c47` | 2026-10-25 | Phase 7 foundation + B-083 tasks (B-083..B-093 services/routers, migration 0010) |
| 40 | `0f3ac6a` | 2026-10-25 | B-085/B-086 tests: decisions supersede chain + settled truth; questions assign/resolve-mints-decision; gaps g… |
| 41 | `162ee0f` | 2026-10-25 | B-087 tests: polls vote/change/close, commit-before-answer proof, concurrent-vote invariant, date-poll winner… |
| 42 | `1e6dea3` | 2026-10-25 | B-088/B-089/B-090 tests: checklist claims, merged-supplies golden, budget integer-cents golden + float refusa… |
| 43 | `3d3ccd2` | 2026-10-25 | B-084/B-091 tests: one thread system four parents (same rows both paths, moderation on tasks); templates star… |
| 44 | `1677426` | 2026-10-25 | B-092/B-093 tests: search golden ranking + source links; digest golden snapshot at fixed moment |
| 45 | `d06fc97` | 2026-10-25 | B-094 phase gate: Flow B (40-message trip argument) end-to-end into event + tasks + decisions + open questions |
| 46 | `ccb7053` | 2026-10-25 | B-094: FRONTEND_HANDOFF planning screens (Phase 7) |
| 47 | `1960f8e` | 2026-10-25 | Phase 7 complete in the map: 94/340 slices, 642 tests, slice notes + boundaries |
| 48 | `9e77e2e` | 2026-10-25 | Phase 8 (part 1): notification schema + outbox core + mail boundary (B-095, B-102) |
| 49 | `5f624f1` | 2026-10-25 | Phase 8 (part 2): reminder engine + AI wording (B-096, B-103) |
| 50 | `e77e5b6` | 2026-10-25 | Phase 8 (part 3): change alerts + invites (B-097, B-098) |
| 51 | `f5336d5` | 2026-10-25 | Phase 8 (part 4): digest + preferences + inbox + stream (B-099, B-100, B-101) |
| 52 | `a56666d` | 2026-10-25 | Phase 8 (part 5): tests — 31 new (642 → 673) |
| 53 | `5755a93` | 2026-10-25 | B-104 gate: ZIP-Beta artefacts — contract, changelog, test report, handoff, map, release tooling |
| 54 | `517354b` | 2026-10-24 | Docs: the full README — what it is, how it works, the laws it lives by (Volmarr's commission, 2026-10-24) |
| 55 | `37c7386` | 2026-10-25 | B-105: sub-groups + chapters — named sub-groups, inherited membership, per-sub-group roles, scoped events/tas… |
| 56 | `5759c4a` | 2026-10-25 | B-106: announcements board — organiser-posted, pinned + expiring, seat-refused in the service |
| 57 | `2e217ce` | 2026-10-25 | B-107: volunteer shifts — B-088 role slots generalised with start/end + headcount, gap report |
| 58 | `fab0834` | 2026-10-25 | B-108: resources — items with a keeper, bookings per event, double-booking as a B-057 flag |
| 59 | `48034d7` | 2026-10-25 | B-109: attendance — organiser-marked, aggregates only, the refusal is a test |
| 60 | `b32803c` | 2026-10-25 | B-110: member import/export — messy-CSV golden survives, dry-run reports then rolls back, roster out as CSV/J… |
| 61 | `bfe5984` | 2026-10-25 | B-111: group settings pack — one validated schema (review rules, reminders, digest, template set, AI budget),… |
| 62 | `88900de` | 2026-10-25 | B-112: Phase 9 gate — the nonprofit story end-to-end; contract regenerated (151 paths / 179 schemas); changel… |
| 63 | `f661232` | 2026-10-25 | B-112: test report addendum + memory map header — 704 passed, reconciled (673 + 31) |
| 64 | `cb4ba10` | 2026-10-25 | B-112 gate corrections: dry-run test asserted its own fixture wrong (roster is owner + fixture member); reque… |
| 65 | `b618f1c` | 2026-10-25 | Map: record the B-112 gate findings (test defect, logging filter, /tmp basetemp practice) |
| 66 | `182d78a` | 2026-10-25 | Papers: licence aligned to GPLv2 (Volmarr's ruling, 2026-10-24) — README licence line + status refreshed to P… |
| 67 | `cb5d7ed` | 2026-10-25 | B-113: pruning core — Geoffrey's engine (a full model judges relevance; NOT embedding RAG, said plainly in th… |
| 68 | `971c534` | 2026-10-25 | B-114: multi-pass pruning — pass 2 re-judges the dropped set and rescues what pass 1 missed (golden recovery… |
| 69 | `0779a28` | 2026-10-25 | B-115: ask-the-group-memory — POST /groups/{id}/ask: prune over approved history, draft from survivors only,… |
| 70 | `88baa27` | 2026-10-25 | B-116: discussion summaries — a thread summarised into a draft Summary; the decisions/next actions it names a… |
| 71 | `fc17b69` | 2026-10-25 | B-117: event briefings — POST /groups/{id}/events/{id}/briefing weaves the structured present (past decisions… |
| 72 | `8936068` | 2026-10-25 | B-118: recaps + newsletter loop — recap drafts from discussion + attendance count + COMPLETE alt text only; a… |
| 73 | `da7f206` | 2026-10-25 | B-119: local-inference driver — OpenAI-compatible chat-completions driver (text only, plain refusals for medi… |
| 74 | `7ee2521` | 2026-10-25 | B-120: memory transparency — GET /groups/{id}/memory/runs lists every prune/ask/brief run with kept/dropped c… |
| 75 | `fc810c0` | 2026-10-25 | B-121: pruning evaluation — golden questions with human-marked relevant chunks scored through the real engine… |
| 76 | `9e0b43d` | 2026-10-25 | B-122: Phase 10 gate — the three memory demos (ask, briefing, recap) run on the golden corpus in mock mode (h… |
| 77 | `83904a4` | 2026-10-25 | Checkpoint papers: Phase 10 verified — 122/350 slices, 735 tests, 160 paths / 189 schemas |
| 78 | `179b8a1` | 2026-10-25 | B-123: Samtal source connector — a Samtal hall as a chat_live source: poll intake through the Samtal client b… |
| 79 | `a1879ac` | 2026-10-25 | B-124: Samtal calendar return path — published events push to the hall's calendar (ExternalEventLink + payloa… |
| 80 | `a2d2939` | 2026-10-25 | B-125: Messenger source (read path) ships as the honest fallback — platform access was never granted, so regi… |
| 81 | `7085646` | 2026-10-25 | B-126: generic webhook source — a signed door onto any source: URL token hashed at rest, HMAC signing secret… |
| 82 | `87dfed3` | 2026-10-25 | B-127: integration framework — Integration model made general (kind vocabulary, name, health record with plai… |
| 83 | `3f30f6f` | 2026-10-25 | B-128: outbound webhooks — group acts (event.published/changed/cancelled, candidate.pending) announced to reg… |
| 84 | `a689fbb` | 2026-10-25 | B-129: agent API pack — the seat's working surface (sources read, queue read/draft, events read, ask, summari… |
| 85 | `0754ae5` | 2026-10-25 | B-130: Phase 11 gate — the bridge walked end to end in one scripted test (Samtal hall synced from the fixture… |
| 86 | `13d970d` | 2026-10-25 | B-126 repair: replay exactly-once holds under any timing |
| 87 | `e628b15` | 2026-10-25 | Checkpoint papers: Phase 11 verified after B-126 replay repair — 130/350 slices, 769 tests, 174 paths / 204 s… |
| 88 | `17a3aff` | 2026-10-25 | B-131: Facebook Event creation — the press: from B-058's draft, on an organiser's explicit call (organiser +… |
| 89 | `81fa0af` | 2026-10-25 | B-132: Google Calendar sync (one-way out) — OAuth connect per group (the sealed credentials a deployment's co… |
| 90 | `c594c9c` | 2026-10-25 | B-133: real mail provider — the SMTP driver behind B-095's boundary (stdlib smtplib, STARTTLS + login when co… |
| 91 | `83d240c` | 2026-10-25 | B-134: Messenger notifications — ships the roadmap's clean driver_unavailable: B-125's access was never grant… |
| 92 | `e3f5e96` | 2026-10-25 | B-135: embed + public page data — a group registers the web origins allowed to embed its page (admin write, o… |
| 93 | `248c985` | 2026-10-25 | B-136: integration health board — GET /groups/{id}/integrations/health-board (organiser+, registered before /… |
| 94 | `9ee5d11` | 2026-10-25 | B-137: reconciliation job — nightly (02:30 group-local) and on an admin's demand, the group's Facebook/Google… |
| 95 | `f1c0338` | 2026-10-25 | B-138: Phase 12 gate — one event's full outward life in a single scripted test (draft → press → sync → move →… |
| 96 | `82393b9` | 2026-10-25 | Checkpoint papers: Phase 12 verified, ZIP-RC in hand — 138/350 slices, 797 tests, 182 paths / 212 schemas |
| 97 | `05b34ce` | 2026-10-25 | B-139: threat-model pass — THREAT_MODEL.md in-repo (assets, actors, Henry's-first-version as Case #1, one abu… |
| 98 | `68f056a` | 2026-10-25 | B-140: authorisation fuzz — two marked groups, 8 attacker principals (foreign owner/admin/organiser/member, s… |
| 99 | `5b34948` | 2026-10-25 | B-141: upload hardening — sniffing proofs, image re-encode strips payloads, per-group storage quota (quota_ex… |
| 100 | `af641e8` | 2026-10-25 | B-142: injection + output safety — one-pass prompt render (values never rescanned; placeholder smuggling clos… |
| 101 | `82623de` | 2026-10-25 | B-143: group export + hard erasure — one schema-derived deletion plan serves both acts (seed group_id tables,… |
| 102 | `f993b09` | 2026-10-25 | B-144: privacy surfaces — GET /users/me/data (whole footprint in plain sections; no hash/secret by constructi… |
| 103 | `34e9242` | 2026-10-25 | B-145: secrets + config audit — prod startup refuses known-default secrets (denylist) and secrets under 32 ch… |
| 104 | `c294706` | 2026-10-25 | B-147: demo data, final — demo story seed (nonprofit + hiking club, cast via seed memberships, 40-message tri… |
| 105 | `0a4cba1` | 2026-10-25 | B-148: demo script to tests — Flows C (newsletter: 12 drafts, re-extraction supersedes not doubles, reviewer… |
| 106 | `05f8d92` | 2026-10-25 | B-149: numbers page — scripts/make_results.py regenerates RESULTS.md from the three evaluation harnesses (ext… |
| 107 | `5722299` | 2026-10-25 | Phase 14 checkpoint papers: B-147..B-149 in the memory map, README progress in place (149/350, 841 tests) |
| 108 | `aced215` | 2026-10-25 | B-146: backup + restore drill — scripts/backup.py (online backup + storage + sha256 manifest), restore.py (ve… |
| 109 | `7527bbd` | 2026-10-25 | Phase 13 gate papers: TEST_REPORT Phase 13 addendum — suite reconciliation (835 = 797 + 38), pip-audit output… |
| 110 | `3357f44` | 2026-10-25 | B-150: submission pack (backend's half) — submission/ cover, honest Meta-model mapping (tiers spark/wonder by… |
| 111 | `69908aa` | 2026-10-25 | B-151 (code): freeze drill prep — make_release_zip.py now ships RESULTS.md at the top level, as roadmap §8's… |
| 112 | `53ad1c5` | 2026-10-25 | B-151 (drill fix): release ZIPs now carry Unix permissions — the freeze drill's first run failed at './demo.s… |
| 113 | `05ec22b` | 2026-10-25 | B-151 (guard test fix): test_release_zip passed a 1970 mtime that ZipInfo itself refuses (ZIP timestamps star… |
| 114 | `d951f81` | 2026-10-25 | B-151 (drill fix 2): Database guarantees its file's parent directory — freeze drill run 2 got past permission… |
| 115 | `c41d693` | 2026-10-25 | Phase 14 gate papers: FREEZE_DRILL.md (the four drill runs, both defects, timings — ships inside ZIP-Final),… |
| 116 | `eb33d70` | 2026-10-25 | Phase 14 checkpoint papers (Yrsa): README status refreshed in place — 151/350, 853 tests, contract 187 paths… |
| 117 | `4ca7caa` | 2026-10-25 | Phase 15 / B-152: PostgreSQL promotion — real parity suite, verified mover |
| 118 | `f24c5a2` | 2026-10-25 | Phase 15 / B-153: native service packaging — systemd units + plain installer |
| 119 | `7e9b551` | 2026-10-25 | Phase 15 / B-154: reverse-proxy + TLS guide — followed literally, live |
| 120 | `22c08cd` | 2026-10-25 | Phase 15 / B-155: observability — deep /health, the runbook, the requeue fix |
| 121 | `fa09b2e` | 2026-10-25 | Phase 15 / B-156: upgrade path — backup, migrate, smoke, swap; rollback is restore |
| 122 | `9d8d7cd` | 2026-10-25 | Phase 15 gate fix: /health deep checks are signed-in-only — B-155 reconciled with the Phase 13 threat model |
| 123 | `ce9028d` | 2026-10-25 | Phase 15 gate: regenerate the contract snapshot for the /health docstring |
| 124 | `9263ca4` | 2026-10-25 | Phase 15 gate: test_sqlite_pragmas joins the PG-mode skip set |
| 125 | `f9ce3a2` | 2026-10-25 | Phase 15 gate: PG-mode isolation learns module-scoped worlds |
| 126 | `612ba7d` | 2026-10-25 | Phase 15 gate: Alembic's fileConfig must not silence the host's loggers |
| 127 | `187477f` | 2026-10-25 | Phase 15 checkpoint papers: memory map, TEST_REPORT Phase 15 addendum, CHANGELOG |
| 128 | `1380326` | 2026-10-25 | Checkpoint papers (Yrsa): README refreshed in place — Phase 15 complete, 156/350, 877 SQLite / 865 PostgreSQL |
| 129 | `6f7c7d2` | 2026-10-25 | B-157 Multi-instance jobs: claim scan + handled collisions, queue interface with arq adapter |
| 130 | `417fb1e` | 2026-10-25 | B-158 Second-wave sources: Discord + Slack drivers behind the unchanged framework |
| 131 | `e5826e4` | 2026-10-25 | B-157 follow-up: the live arq leg ran — two defects fixed at root |
| 132 | `9cd8904` | 2026-10-25 | B-159 Two-way Google (revisited): inbound edits arrive as change candidates |
| 133 | `14bfd22` | 2026-10-25 | B-160 Public API + developer pack: versioned surface, key self-service, generated SDK, published types |
| 134 | `4d552f5` | 2026-10-25 | Checkpoint papers (Phase 16 gate): memory map, TEST_REPORT addendum, CHANGELOG, FRONTEND_HANDOFF |
| 135 | `f038008` | 2026-10-25 | README: Phase 16 checkpoint refresh (160/350, 904 SQLite / 888 PG, contract 188/218) |
| 136 | `d02d8dd` | 2026-10-25 | Phase 17 enabler: cryptography dependency (AES-256-GCM + Ed25519 for B-163/B-167, wheels on every Tier-1 targ… |
| 137 | `96f3d62` | 2026-10-25 | B-161 Module boundaries: module map + architecture checker, pinned edge inventories, private imports and sche… |
| 138 | `2ad79fd` | 2026-10-25 | B-162 Internal API core: typed envelope, operation registry with caller scopes, handlers in the caller's tran… |
| 139 | `e72161d` | 2026-10-25 | B-163 Encrypted internal transport: AES-256-GCM + Ed25519 (HMAC profile) wire form, Unix socket + loopback mT… |
| 140 | `c3fa8a8` | 2026-10-25 | B-164 Service identities + replay protection: per-module Ed25519 identities with key ids and rotation overlap… |
| 141 | `f9b0d65` | 2026-10-25 | B-165 Internal API audit: every dispatch writes its B-019 line (caller, key id, operation, scope, module, res… |
| 142 | `a9b6784` | 2026-10-25 | B-166 In-process profile honestly: wire-mode internal client (split profile is composition, not code), execut… |
| 143 | `8dd536b` | 2026-10-25 | B-167 Field-level encryption: gpa/crypto envelope scheme (master wraps per-group data keys, enc:v1: seals bou… |
| 144 | `be33370` | 2026-10-25 | B-168 Encrypted file storage: EncryptedStorage driver (per-file keys wrapped under the master, GPAE1 header,… |
| 145 | `bcbe910` | 2026-10-25 | B-169 Key management: master rotation by re-wrap (one transaction, crypto.rotate_master job), owner recovery… |
| 146 | `6f3626b` | 2026-10-25 | B-170 Tamper-evident audit hash chain: prev/row hashes extended inside the writer's transaction, one-row chai… |
| 147 | `adb2241` | 2026-10-25 | B-171 Durability manager: structural commit-before-answer (write tracker + guard middleware, 500 uncommitted_… |
| 148 | `87afb0a` | 2026-10-25 | B-172 Startup recovery & self-healing: assess_and_repair (serve/repaired/refuse verdicts, WAL checkpoint, stu… |
| 149 | `725ef65` | 2026-10-25 | B-173 Error-correction services: circuit breakers + bulkheads per dependency enforced by the job chassis (def… |
| 150 | `8801554` | 2026-10-25 | B-174 Advanced account security: TOTP MFA (sealed secret, single-use steps, 5-min challenge), password policy… |
| 151 | `b0dfe3e` | 2026-10-25 | B-176 Comment + documentation gate: AST checker (purpose headers, migration/prompt whys, env comments, no res… |
| 152 | `16c64b1` | 2026-10-25 | B-176 correction: regression batch total is 23 passed per its own log (gate 6 + architecture/threat/submissio… |
| 153 | `cbca7ec` | 2026-10-25 | B-177 Cross-platform verification matrix: portability audit (pathlib-only, explicit encodings, no OS branchin… |
| 154 | `de9e3f2` | 2026-10-25 | B-178 Production-quality pipeline: ruff+mypy+pytest-cov+pre-commit as locked dev deps, enforced ruff E9+F bro… |
| 155 | `9fdd812` | 2026-10-25 | Papers: memory map B-177 + B-178 entries (178/350) |
| 156 | `a1f9977` | 2026-10-25 | B-179 Signed releases + SBOM: SPDX 2.3 bill of materials generated from uv.lock inside every train ZIP, Ed255… |
| 157 | `b0d7ec2` | 2026-10-25 | B-180 Phase 17 gate drill: resumable-upload flyer -> worker dies mid-vision-job -> startup recovery requeues… |
| 158 | `0ed3dcd` | 2026-10-26 | Phase 17 gate repair: first PG-mode run of the Phase 17 tests found four SQLite-bound tests (B-167 raw-file g… |
| 159 | `66f88fb` | 2026-10-26 | Phase 17 gate fix (production): audit chain head race on PostgreSQL — B-170's read-prev/hash/advance dance in… |
| 160 | `50b15bd` | 2026-10-26 | Phase 17 gate repair 2 (test isolation): PG per-test reset now also drops alembic_version — the table is not… |
| 161 | `8d06c9c` | 2026-10-26 | README checkpoint refresh (in place): Phase 17 complete — 180/350 slices, contract 201 paths / 229 schemas, P… |
| 162 | `7547930` | 2026-10-26 | Phase 17 gate papers: drill totals filled from the runs' own logs (SQLite 1026/7/0 in two declared halves, PG… |
| 163 | `b6fa85f` | 2026-10-26 | B-181 Documentation architecture: docs/ tree + reader-ordered index + docs-as-code rules, stdlib Mermaid gate… |
| 164 | `7980b82` | 2026-10-26 | B-182 User guide I: start + groups (account, sign-in incl. MFA, group creation, invites, roles in plain words… |
| 165 | `fca9b2c` | 2026-10-26 | B-183 User guide II: sources — every way in (paste, file, newsletter, flyer, board, link, email-in, voice, li… |
| 166 | `504317a` | 2026-10-26 | B-184 User guide III: the review queue — reading a candidate, confidence and the closed flag vocabulary, prov… |
| 167 | `47b529a` | 2026-10-26 | B-185 User guide IV: calendar + events — agenda/month/tonight views (tonight 15:00-03:00 group-local, pinned… |
| 168 | `39031d2` | 2026-10-26 | B-186 User guide V: planning — tasks and the owner law (AI words land only as a suggested label), decisions l… |
| 169 | `9137a1e` | 2026-10-26 | B-187 User guide VI: reminders, digests, memory — materialised reminders (7d/1d 09:00 + morning-of 08:00 even… |
| 170 | `1117a55` | 2026-10-26 | B-188 Admin + operator guide: every dangerous button with consequence before instructions — settings pack (on… |
| 171 | `3a35af9` | 2026-10-26 | B-189 Architecture diagram pack: six lengthy Mermaid diagrams each with a prose walking tour naming every box… |
| 172 | `f923cf2` | 2026-10-26 | B-189 correction: regression batch total is 31 passed per its own logs (docs gate/architecture/submission 25… |
| 173 | `5eea552` | 2026-10-26 | B-190 Module atlas: one chapter per B-161 module (22 chapters) — job, public surface, tables owned, internal… |
| 174 | `bdbf83f` | 2026-10-26 | B-191 Internal encrypted API document: the §6A.4 protocol in full — envelope field-by-field (request/result +… |
| 175 | `d61be4b` | 2026-10-26 | B-192 Data-model document + ER pack: six erDiagram packs (identity, sources, events, planning, comms, system)… |
| 176 | `f22d4b0` | 2026-10-26 | B-193 AI pipeline documents: extraction, flyer reading, board segmentation, de-duplication, change detection,… |
| 177 | `11597b6` | 2026-10-26 | B-194 Security + cryptography document: threat model in prose (assets, actors, Case #1 decided at the review… |
| 178 | `8f80980` | 2026-10-26 | B-194 correction: regression batch total is 70 passed per its own log, not 80 as first recorded |
| 179 | `ffdd968` | 2026-10-26 | B-195 Durability + recovery document: §6A.5 machinery as diagrams and drills (WAL/FULL foundation, WriteTrack… |
| 180 | `b864e20` | 2026-10-26 | B-196 API + frontend guide: three auth sequence diagrams (password+MFA challenge, magic link, refresh-family… |
| 181 | `7ac622d` | 2026-10-26 | B-196 correction: regression batch total is 57 passed per its own delivered log, not 72 as first recorded |
| 182 | `c291b1e` | 2026-10-26 | B-197 Per-code-file atlas: generated docs/16 chapter with one entry per code file (391 files: purpose from th… |
| 183 | `55bd984` | 2026-10-26 | B-198 Testing + quality document: how to run (test.sh anatomy — Mermaid gate then suite, one-page report, bas… |
| 184 | `e901c98` | 2026-10-26 | B-199 Deployment + release document: native install (Linux systemd road rehearsed — dedicated user, non-edita… |
| 185 | `9cd6524` | 2026-10-26 | B-200 Documentation proof — Phase 18 gate: three cold reads as executable/audit legs (guide I checklist parse… |
| 186 | `6fd1cf2` | 2026-10-26 | Phase 18 gate papers (checkpoint): README refreshed in place (200/350, 1056 passing SQLite — tests line had l… |
| 187 | `ba84f5f` | 2026-10-26 | B-201 API parity audit + checker: 256-action register (route + internal operation per action, reverse drift c… |
| 188 | `83efd67` | 2026-10-26 | B-202 agent-seat equality pack + B-203 the one approval law: seat profile (name/description/avatar, migration… |
| 189 | `13bad8c` | 2026-10-26 | B-204 MCP server core: official SDK server package (src/gpa/mcp) talking only through the internal encrypted… |
| 190 | `e34f0a7` | 2026-10-26 | B-204 atlas: regenerated per-file atlas for the MCP package (402 files, B-197 checker green via docs gate 25… |
| 191 | `508a09c` | 2026-10-26 | B-204 correction: MCP SDK version is 1.30.0 per uv.lock and the installed environment, not 1.29.1 as first re… |
| 192 | `182f2ff` | 2026-10-26 | B-205 MCP authentication + authorisation: seat-key local road (re-resolved per call, revocation lands on next… |
| 193 | `faf77a3` | 2026-10-26 | B-206 MCP tool registry from one source of truth: catalogue generated from the internal operation registry (g… |
| 194 | `a7759c1` | 2026-10-26 | B-207 MCP tools — groups, members, profile: first domain family on the generated catalogue — five new interna… |
| 195 | `a74ec57` | 2026-10-26 | B-208 MCP tools — candidates and the review queue: second domain family — five new internal operations (candi… |
| 196 | `ee57fac` | 2026-10-26 | B-209 MCP tools — events, RSVPs, and the calendar: third domain family — six new internal operations (events.… |
| 197 | `f5f43cf` | 2026-10-26 | B-210 MCP tools — sources and extraction requests: fourth domain family — five new internal operations (sourc… |
| 198 | `5618026` | 2026-10-26 | B-211 MCP tools — planning (tasks, decisions, questions): fifth domain family — six new internal operations (… |
| 199 | `8f23346` | 2026-10-26 | B-212 MCP tools — notifications, digests, and announcements: sixth and last domain family of the B-207→B-212… |
| 200 | `9618de4` | 2026-10-26 | B-213 MCP resources: read-only gpa:// shelf — six group templates (calendar as JSON + iCalendar rendered in-m… |
| 201 | `05043de` | 2026-10-26 | B-214 MCP subscriptions + notifications: resources/subscribe + unsubscribe protocol handlers for the calendar… |
| 202 | `0e8493f` | 2026-10-26 | B-215 MCP prompts: curated versioned workflow templates — five roadmap jobs (plan_event, brief_before_event,… |
| 203 | `16d6892` | 2026-10-26 | B-216 MCP elicitation bridge: server may ask the human for one missing fact (place/time/yes_no/free_text, clo… |
| 204 | `de1bddf` | 2026-10-26 | B-216 correction: combined batch total is 140 passed per its own log (batch2.log, 300.70s), not 146 as first… |
| 205 | `055eb49` | 2026-10-26 | B-217 MCP sampling policy: server-initiated sampling off by default (GPA_MCP_SAMPLING_ENABLED, reason in Doc… |
| 206 | `ac96db6` | 2026-10-26 | B-217 correction: tests/test_mcp_sampling.py passed 10/10 on its first full-file run per that run's own deliv… |
| 207 | `b13af71` | 2026-10-26 | B-218 MCP security hardening: truthful tool annotations on every served tool (readOnly = the read scope; dest… |
| 208 | `bd1554c` | 2026-10-26 | B-218 correction: the combined batch's own log (batch.log, 427.16s) reads 154 passed / 3 failed — the '155 pa… |
| 209 | `3df9236` | 2026-10-26 | B-219 MCP conformance + client pack: generated tool catalogue (every tool's credential + internal scopes, B-2… |
| 210 | `f71c26b` | 2026-10-26 | B-219 correction: the combined batch's own log (batch.log, 320.18s) reads 117 passed / 0 failed for all tests… |
| 211 | `10e4b98` | 2026-10-26 | B-220 Phase 19 gate (built; full-suite proof DEFERRED) + build HALT at Volmarr's order 2026-10-26 |

*The full, untruncated history — complete commit messages included — is preserved verbatim in `.build-history/git-log-full.txt` and in structured form under `provenance/`.*
