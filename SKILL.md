---
name: hermes-world
description: Install and run the Hermes World simulation framework — a living multi-agent social simulation with Three.js visualisation, cron heartbeat, and Telegram updates.
version: 1.0.0
author: Hermes World
license: MIT
dependencies: []
metadata:
  hermes:
    tags: [simulation, agents, threejs, hackathon, hermes-world]
    related_skills: []
---

# Hermes World

A universal agent simulation framework. Given a scenario in natural language, it spawns
Hermes subagents as distinct human personas that reason and act each round, mutating a
shared world state visualised in a Three.js 3D scene.

## Installation

The repo lives at a user-provided path (or wherever they cloned it). Run:

```bash
cd /path/to/hermes-world
bash install.sh
```

`install.sh` will:
1. Install Python deps (`fastapi`, `uvicorn`, `httpx`, `pyyaml`) via pip3
2. Create `skills/agents/` directory
3. Symlink `skills/` into `~/.hermes/skills/hermes-world/` so agent-learned skills are picked up by Hermes

## Running

### Start the backend server (keep running in background)

```bash
cd /path/to/hermes-world
python3 server.py
```

This serves the Three.js frontend at http://localhost:8000 and watches `world_state.json`
for changes to push to the browser over WebSocket.

### Start a simulation

```bash
python3 orchestrator.py "Your scenario here" --agents 6 --rounds 2 --interval 5
```

Examples:
- `python3 orchestrator.py "10 people stranded on a raft. Supplies for 7. Storm lasts 3 days."`
- `python3 orchestrator.py "A 5-person startup with $50k runway and 3 competing product visions." --agents 5`
- `python3 orchestrator.py "A Mars colony crew of 6 dealing with a hull breach." --rounds 3`

### Manually tick one round

```bash
python3 orchestrator.py --tick
```

### Apply an intervention

```bash
python3 orchestrator.py --intervene "A rescue boat appears on the horizon"
python3 orchestrator.py --intervene "Reduce supplies by 30%"
python3 orchestrator.py --intervene "fast forward 2 rounds"
```

## Cron

When `orchestrator.py` starts a simulation, it automatically registers a Hermes cron job
to advance rounds every N minutes (default 5). Round summaries are delivered to Telegram
via the Hermes gateway (must be running: `hermes gateway start`).

## Architecture

- `orchestrator.py` — bootstrap, cron tick, intervention handler
- `round_runner.py` — spawns parallel Hermes subagents, collects JSON decisions, mutates world
- `persona_generator.py` — LLM call to generate N agent personas from scenario text
- `scene_classifier.py` — maps scenario → scene type (raft/office/village/space/courtroom)
- `skill_writer.py` — writes `SKILL.md` files for agent-learned skills into `skills/agents/`
- `telegram_reporter.py` — formats and sends round summaries via Hermes gateway
- `server.py` — FastAPI + WebSocket, serves frontend, handles `/api/tick` and `/api/intervene`
- `frontend/` — Three.js scene engine, character animations, HUD, WebSocket client

## File layout

```
hermes-world/
├── orchestrator.py
├── round_runner.py
├── world_state.json          ← live simulation state (watched by server.py)
├── server.py
├── scene_classifier.py
├── persona_generator.py
├── skill_writer.py
├── telegram_reporter.py
├── requirements.txt
├── install.sh
├── SKILL.md                  ← this file
├── frontend/
│   ├── index.html
│   ├── world.js
│   ├── characters.js
│   ├── hud.js
│   ├── ws-client.js
│   └── scenes/
│       ├── raft.js
│       ├── office.js
│       ├── village.js
│       ├── space.js
│       └── courtroom.js
└── skills/
    └── agents/               ← agent-learned skills written here at runtime
```

## Notes

- Requires Hermes agent installed at `~/.hermes/` (default) or `$HERMES_HOME`
- Telegram summaries use the Hermes gateway — no separate bot token needed
- The model used for subagents is whatever is configured in `~/.hermes/config.yaml`
- Scene type is auto-detected from scenario text; override not currently supported via CLI
