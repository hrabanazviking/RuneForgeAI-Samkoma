# RuneForgeAI-Samkoma

Samkoma is your gathering place, a free and open home for planning together. Built on shared trust, it holds calendars, events, and RSVPs where every voice can be heard and every change returns to the community. Private by nature, warm by design, it lets people gather, decide, and keep their plans alive without walls locking them out.

# Samkoma — the gathering, planned together

**Samkoma** (Old Norse: *a coming-together, a gathering*) is Volmarr Wyrd's
group-planning commons: a backend that reads the places a group's plans
already hide — a chat thread three hundred messages deep, a newsletter
nobody finished reading, a paper flyer photographed crooked on a
corkboard — fishes the plan out of the noise, writes it down as a draft
*with its receipts*, and then waits for a human being to say yes.

> **The machine drafts. The human decides.**

Everything the AI reads becomes a **candidate** — a draft sitting in a
**review queue**, never a fact. A candidate turns into a real event, task,
or decision only when a *person in the group* approves it. And every
proposed value carries **provenance**: the exact quote, from the exact
source, that it was read from. If the quote doesn't actually support the
value, the value is marked `unsupported` and shown that way. The system
would rather display an honest gap than invent a fact.

| Where we are | Phases 0–18 complete · Phase 19 built through B-220 · **220 of 350 roadmap slices banked** |
|---|---|
| Tests | **1,056 passing** at the Phase 18 full-suite gate (SQLite; 1,013 on PostgreSQL at the Phase 17 gate). Phase 19's slices each passed their own batches as built; its closing full-suite proof is still owed |
| API contract | **202 paths · 230 schemas**, frozen in [`OPENAPI.json`](OPENAPI.json), with generated TypeScript types in [`frontend_types.ts`](frontend_types.ts) |
| MCP bus | A full MCP server over the same API — 44 tools / 42 operations, with consent gates, truthful tool annotations, and a generated tool catalogue |
| Stack | Python 3.12 · FastAPI · Pydantic v2 · SQLAlchemy 2.0 · SQLite (WAL) and PostgreSQL, both proven by the same suite. **No Docker** — native installs only |

## What it can do today

- **Feed it anything.** Paste a chat export (WhatsApp, Discord, Slack,
  Messenger, or plain `Name:` lines — the parsers never drop a line),
  upload a file (contents sniffed, not trusted by extension: PDF, HTML,
  ICS, plain text), photograph a flyer or a whole corkboard, forward a
  newsletter (split into sections, each read on its own), drop a link
  (fetched behind an SSRF guard), email it in, or speak a voice note.
- **It reads like a careful clerk.** Extraction proposes events, tasks,
  decisions, and questions — each field with its quote and confidence. A
  deterministic date resolver turns *"this Saturday"* into the right
  Saturday relative to when the message was *sent*, pinned by 268 golden
  cases; a genuinely ambiguous phrase returns every reading, flagged —
  it never guesses.
- **The review queue.** Approve, edit, or reject. Approval mints the real
  thing in the same transaction — there is no half-state where a plan is
  "approved but not created."
- **A calendar that keeps its promises.** Hand-rolled recurrence and iCal
  engines that pass the daylight-saving trap; per-group iCal feeds
  (token shown once, stored hashed, revocable); cancelled events stay
  visible *as cancelled*; a tonight view that runs 3 pm → 3 am in the
  group's own timezone.
- **Planning, not just events.** Tasks, decisions with supersede chains,
  questions, polls (commit-before-answer, proven from the outside),
  checklists that merge across events, budgets in integer cents only —
  a float is refused at the door.
- **Reminders, invites, and the weekly digest.** Notifications travel by
  outbox, never inline, so a dead mail server loses nothing. Reminders
  are materialised per person and superseded when an event moves; guests
  are invited by signed link and can RSVP without an account; the digest
  renders from in-repo templates as HTML and plain text.
- **Seats for AI agents.** An agent seat is a first-class user of the
  API, with its own scoped key (`read` / `draft` / `publish` / `admin`)
  — it may draft freely and is audited like everyone else, but **a seat
  can never approve**. Approval is a person's act, refused to seats in
  the service layer, not merely hidden in an interface.

## The laws the code lives by

These are not aspirations. Each is enforced by a mechanism and pinned
by tests.

1. **Commit before answer.** SQLite runs WAL with `synchronous=FULL`,
   and a handler never sends its response before its transaction
   commits — proven from outside the process, with a second database
   session watching.
2. **A quote, or it didn't happen.** Every extracted value must produce
   the source words that support it. No quote, no confidence.
3. **The AI never assigns people.** It may repeat the name a human
   wrote. Turning that name into an assignment is a person's act.
4. **Seats can't approve.** See above — enforced in the service layer.
5. **Nothing is deleted in anger.** Tombstones, snapshots, and a 30-day
   restore window; even a deleted source keeps its provenance trail.
6. **Money is integer cents.** Floats are refused at the door.
7. **Alt text is law.** Every image carries a description state,
   enforced in both directions: thin machine-written alt text never
   counts as finished, and a human's real words are never overwritten
   by the machine afterwards.
8. **Honest stubs.** Anything not truly wired is labelled *stubbed* or
   *not yet* in plain words — in the code, in the release papers, and
   in this README. A claim the evidence doesn't support is a bug.
9. **Budgets are real.** Extraction runs against a per-group daily AI
   budget; when it is spent, the state reads *paused — budget* in
   plain words.

## Architecture

Three ideas hold the whole building up: **routers are thin** (they speak
HTTP and nothing else — a test verifies no router imports a model),
**rules live in services** (every business decision is in `services/`,
callable and testable without HTTP), and **`deps.py` is the only door**
(every authentication and role check passes through it). All model
access passes through **one AI adapter** with three interchangeable
drivers — *live* (real HTTP to a model endpoint, secrets from the
environment only), *fixture* (recorded answers, so tests and demos are
repeatable), and *mock* (schema-valid synthesis, honest about its
limits) — so **the demo runs fully offline**, with no network and no
key. Above the API sits the **MCP server**: the same operations, exposed
as tools, behind consent gates and an encrypted internal bus.

Security, briefly: Argon2id password hashes; hashed, single-use magic
links; rotating refresh-token families with theft detection (present a
retired token and the whole family is revoked); a private group returns
**404** to a non-member — the API will not even confirm the group
exists; and an append-only audit written in the *same transaction* as
the act it records.

## Run it

**You need:** Python 3.12+ and [uv](https://docs.astral.sh/uv/).

```sh
uv sync --extra dev     # install the exact locked environment
./run.sh                # server on http://127.0.0.1:8000
./run.sh --demo         # …with the demo group + user seeded first
curl http://127.0.0.1:8000/health
```

Windows is a first-class citizen: `uv sync` then `.\run.ps1`.

- **Configuration** is environment variables with a `GPA_` prefix; every
  one is documented in [`.env.example`](.env.example). Production mode
  refuses a development secret, in plain words, at startup.
- **Migrations:** `uv run alembic upgrade head`. Up, down, and up again
  is part of the test ritual.
- **Tests:** `./test.sh` — the whole suite plus a one-page report. A
  test total is only ever quoted from one clean run against the final
  committed tree; a number from a mid-edit run is a rumour, not a count.

> **An honest note on the rename.** Under the hood, the Python package
> is still named `gpa` and the settings still carry the `GPA_` prefix —
> Samkoma is the project's name and home first. Deeper renaming is
> roadmap work, not claimed here.

## The roadmap

Samkoma is built to a written roadmap of **350 slices in 29 phases** —
small, individually tested, individually committed steps, built strictly
in order. Phases 0–18 are complete; Phase 19 (equal principals, total
API parity, the advanced MCP server) is built through B-220. Phases
20–28 remain ahead: the terminal app, multi-user networking, universal
platform support, calendar and office-suite interoperability,
evidence-based development machinery, being built to be built in —
Samtal first — and the MCP / database-bus topology work. The full table
and the living, slice-by-slice map live in
[`PROJECT_MEMORY_MAP.md`](PROJECT_MEMORY_MAP.md).

## Provenance

Samkoma is the continuation, under its own name and in Volmarr's own
house, of the **Group Planning Assistant** backend — built by Volmarr
Wyrd and Yrsa through October 2026, first as a team entry for the Meta
Global AI Developer Hackathon. When that road closed, Volmarr's standing
plan took over: the work was already wholly in our hands, so it carries
on here as his own renamed project (his word, 2026-10-29). The full,
unbroken commit history came with it — every slice, every correction,
every honest count. Nothing was rewritten and nothing was hidden.

## Licence

Samkoma is free software under the **GNU General Public License** —
see the [`LICENSE`](LICENSE) file in this repo.

One honest wrinkle, stated plainly until Volmarr settles it: the
`LICENSE` file here is the GPL **version 3** text, placed by Volmarr
when he created this repo, while the carried-over codebase's own
recorded licence declaration (in `pyproject.toml`, decided by Volmarr
on 2026-10-24) reads **GPL-2.0-only**. Both facts stand in the open;
the reconciliation is his word to give, and this note comes out the
day he gives it.

## Repository map

| Path | What it is |
|---|---|
| `PROJECT_MEMORY_MAP.md` | The living map: what exists, slice by slice, and *why*. Start here after this README. |
| `FRONTEND_HANDOFF.md` | Everything a frontend needs, screen by screen. |
| `OPENAPI.json` · `frontend_types.ts` | The frozen contract and its generated TypeScript types. |
| `docs/` | The numbered design documents, including Doc 13 (the MCP server). |
| `collections/` | A Bruno collection that fires the API's core calls. |
| `migrations/` | Alembic migrations — the database's own versioned history. |
| `seeds/` | The idempotent seed data, demo group included. |
| `scripts/` | The contract, catalogue, and release tooling. |
| `run.sh` · `run.ps1` · `test.sh` | One command to run it, on either side of the OS fence; one command to test it. |
| `pyproject.toml` · `uv.lock` | The project's definition and its exact, locked environment. |

---

*Built the slow way on purpose: one slice, one test run, one commit at a
time — so that at any moment, anyone can ask "what do we actually
have?" and get an answer that is true.*
