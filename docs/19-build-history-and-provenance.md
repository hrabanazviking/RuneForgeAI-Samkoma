# 19 — Build history and provenance

This chapter records how this backend came to be, in the tree's own evidence.

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

The complete commit-by-commit record stands in `BUILD_HISTORY.md` at the repository root and, verbatim, in `.build-history/`.
