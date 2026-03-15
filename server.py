"""
server.py — FastAPI + WebSocket server for Hermes World.

Watches world_state.json and pushes diffs to all connected Three.js clients.
Also handles Telegram webhook for intervention commands.

Usage:
    python3 server.py
    python3 server.py --port 8000 --host 0.0.0.0
"""

import argparse
import asyncio
import json
import os
import time
from pathlib import Path
from typing import Set

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
import uvicorn

PROJECT_ROOT = Path(__file__).parent
WORLD_STATE_PATH = PROJECT_ROOT / "world_state.json"
FRONTEND_DIR = PROJECT_ROOT / "frontend"

app = FastAPI(title="Hermes World")

# ── Static frontend ────────────────────────────────────────────────────────────
app.mount("/static", StaticFiles(directory=str(FRONTEND_DIR)), name="static")


@app.get("/")
async def index():
    return FileResponse(str(FRONTEND_DIR / "index.html"))


# ── WebSocket manager ──────────────────────────────────────────────────────────
class ConnectionManager:
    def __init__(self):
        self.active: Set[WebSocket] = set()

    async def connect(self, ws: WebSocket):
        await ws.accept()
        self.active.add(ws)

    def disconnect(self, ws: WebSocket):
        self.active.discard(ws)

    async def broadcast(self, data: dict):
        dead = set()
        for ws in self.active:
            try:
                await ws.send_json(data)
            except Exception:
                dead.add(ws)
        self.active -= dead


manager = ConnectionManager()


@app.websocket("/ws")
async def websocket_endpoint(ws: WebSocket):
    await manager.connect(ws)
    # Send current state immediately on connect
    state = _load_state()
    if state:
        await ws.send_json({"type": "state", "data": state})
    try:
        while True:
            # Keep alive — client can send intervention commands
            msg = await ws.receive_text()
            try:
                cmd = json.loads(msg)
                if cmd.get("type") == "intervene":
                    _handle_intervention(cmd.get("command", ""))
            except Exception:
                pass
    except WebSocketDisconnect:
        manager.disconnect(ws)


# ── World state watcher ────────────────────────────────────────────────────────
_last_mtime: float = 0.0
_last_state: dict = {}


def _load_state() -> dict:
    try:
        with open(WORLD_STATE_PATH) as f:
            return json.load(f)
    except Exception:
        return {}


def _handle_intervention(command: str):
    """Apply an intervention command from the frontend."""
    import subprocess
    subprocess.Popen(
        ["python3", str(PROJECT_ROOT / "orchestrator.py"), "--intervene", command],
        cwd=str(PROJECT_ROOT),
    )


async def watch_world_state():
    """Poll world_state.json and broadcast changes to all WebSocket clients."""
    global _last_mtime, _last_state
    while True:
        await asyncio.sleep(1.0)
        try:
            mtime = WORLD_STATE_PATH.stat().st_mtime
        except FileNotFoundError:
            continue
        if mtime != _last_mtime:
            _last_mtime = mtime
            state = _load_state()
            if state != _last_state:
                _last_state = state
                await manager.broadcast({"type": "state", "data": state})


@app.on_event("startup")
async def startup():
    asyncio.create_task(watch_world_state())


# ── REST API ───────────────────────────────────────────────────────────────────
@app.get("/api/state")
async def get_state():
    return _load_state()


@app.post("/api/intervene")
async def post_intervene(body: dict):
    command = body.get("command", "")
    if not command:
        return {"error": "command required"}
    _handle_intervention(command)
    return {"ok": True, "command": command}


@app.post("/api/tick")
async def post_tick():
    """Manually trigger one simulation round."""
    import subprocess
    subprocess.Popen(
        ["python3", str(PROJECT_ROOT / "orchestrator.py"), "--tick"],
        cwd=str(PROJECT_ROOT),
    )
    return {"ok": True}


# ── Entry point ────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default="0.0.0.0")
    parser.add_argument("--port", type=int, default=8000)
    args = parser.parse_args()
    uvicorn.run("server:app", host=args.host, port=args.port, reload=False)
