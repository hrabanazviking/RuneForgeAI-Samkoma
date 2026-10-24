# Group Planning Assistant — Backend

The Python backend for the Group Planning Assistant: it turns a
group's conversation, newsletters, and flyers into drafted plans —
events, tasks, decisions — that only become real when a person in
the group approves them in the review queue. Humans and AI agent
seats use it as equals, through the REST API, MCP, or the terminal.

Licence: to be decided by the team — all rights reserved.

## Run it

```sh
uv sync            # install the exact locked environment
./run.sh           # start the server (http://127.0.0.1:8000)
curl http://127.0.0.1:8000/health
```

Windows: `uv sync` then `.\run.ps1`.

## Test it

```sh
./test.sh          # full suite + a one-page report
```

## Where things are

- `src/gpa/` — the code. Routers are thin; rules live in `services/`.
- `PROJECT_MEMORY_MAP.md` — what exists, slice by slice, and why.
- `OPENAPI.json` — the frozen API contract for the frontend crew.
- `docs/` set + roadmap — the design this code implements.
