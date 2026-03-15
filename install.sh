#!/usr/bin/env bash
# install.sh — Hermes World setup
# Run once after cloning. Installs Python deps and creates initial state.
#
# Prerequisites: Hermes Agent installed at ~/.hermes/

set -e
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
HERMES_HOME="${HERMES_HOME:-$HOME/.hermes}"
HERMES_VENV="${HERMES_HOME}/hermes-agent/venv/bin/python3"

echo "=== Hermes World — Install ==="
echo ""

# ── 0. Check prerequisites ───────────────────────────────────────────────────
echo "[0/5] Checking prerequisites..."

if [ ! -d "$HERMES_HOME" ]; then
  echo "      ERROR: Hermes not found at $HERMES_HOME"
  echo "      Install Hermes first: https://github.com/NousResearch/hermes-agent"
  exit 1
fi
echo "      Hermes found at $HERMES_HOME"

# Use Hermes venv Python if available (has all deps), otherwise system Python
if [ -f "$HERMES_VENV" ]; then
  PYTHON="$HERMES_VENV"
  echo "      Using Hermes venv Python: $PYTHON"
else
  PYTHON="python3"
  echo "      Using system Python (may need additional deps)"
fi

# ── 1. Python deps ────────────────────────────────────────────────────────────
echo "[1/5] Installing Python dependencies..."
$PYTHON -m pip install fastapi uvicorn httpx pyyaml --quiet 2>/dev/null || \
  pip3 install fastapi uvicorn httpx pyyaml --quiet
echo "      Done."

# ── 2. .env setup ─────────────────────────────────────────────────────────────
echo "[2/5] Setting up environment..."
if [ ! -f "$SCRIPT_DIR/.env" ]; then
  cp "$SCRIPT_DIR/.env.example" "$SCRIPT_DIR/.env"
  echo "      Created .env from .env.example — edit to add your settings"
else
  echo "      .env already exists — skipping"
fi

# ── 3. Skill dirs ─────────────────────────────────────────────────────────────
echo "[3/5] Creating local skill directories..."
mkdir -p "${SCRIPT_DIR}/skills/agents"
echo "      Done."

# ── 4. Symlink agent skills into Hermes ───────────────────────────────────────
echo "[4/5] Linking agent skills into Hermes..."
HERMES_SKILLS="${HERMES_HOME}/skills"
mkdir -p "$HERMES_SKILLS"
LINK_TARGET="${HERMES_SKILLS}/hermes-world"
if [ -L "${LINK_TARGET}" ]; then
  echo "      Symlink already exists — skipping."
elif [ -e "${LINK_TARGET}" ]; then
  echo "      WARNING: ${LINK_TARGET} exists and is not a symlink — skipping."
  echo "      To link manually: ln -s ${SCRIPT_DIR}/skills ${LINK_TARGET}"
else
  ln -s "${SCRIPT_DIR}/skills" "${LINK_TARGET}"
  echo "      Linked ${SCRIPT_DIR}/skills → ${LINK_TARGET}"
fi

# ── 5. Reset world state ──────────────────────────────────────────────────────
echo "[5/5] Initialising world_state.json..."
cat > "${SCRIPT_DIR}/world_state.json" <<'JSON'
{
  "scenario": "",
  "scene_type": "raft",
  "round": 0,
  "next_round_at": null,
  "round_interval_minutes": 5,
  "status": "idle",
  "world": {
    "supplies": 100,
    "morale": 75,
    "time_elapsed_hours": 0,
    "weather": "calm",
    "events": []
  },
  "agents": [],
  "influence_graph": [],
  "skill_registry": {},
  "round_log": []
}
JSON
echo "      Done."

echo ""
echo "=== Installation complete ==="
echo ""
echo "Next steps:"
echo "  1. Edit .env with your Telegram channel ID (optional)"
echo "  2. Start the backend:   $PYTHON server.py"
echo "  3. Run a simulation:    $PYTHON orchestrator.py \"Your scenario here\""
echo "  4. Open the frontend:   http://localhost:8000"
echo ""
echo "Telegram (optional):"
echo "  Hermes World uses your existing Hermes Telegram gateway."
echo "  Make sure it's running: hermes gateway start"
echo ""
