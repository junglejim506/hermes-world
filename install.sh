#!/usr/bin/env bash
# install.sh — Hermes World setup
# Run once after cloning. Installs Python deps, symlinks skills into Hermes,
# and creates a fresh world_state.json.

set -e
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
HERMES_SKILLS="${HOME}/.hermes/skills"

echo "=== Hermes World — Install ==="
echo ""

# ── 1. Python deps ────────────────────────────────────────────────────────────
echo "[1/4] Installing Python dependencies..."
pip3 install fastapi uvicorn httpx pyyaml --quiet
echo "      Done."

# ── 2. Skill dirs ─────────────────────────────────────────────────────────────
echo "[2/4] Creating local skill directories..."
mkdir -p "${SCRIPT_DIR}/skills/agents"
echo "      Done."

# ── 3. Symlink agent skills into Hermes ───────────────────────────────────────
echo "[3/4] Linking agent skills into ~/.hermes/skills/hermes-world ..."
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

# ── 4. Reset world state ──────────────────────────────────────────────────────
echo "[4/4] Initialising world_state.json..."
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
echo "  1. Start the backend:   python3 server.py"
echo "  2. Run the orchestrator: python3 orchestrator.py \"Your scenario here\""
echo "  3. Open the frontend:   http://localhost:8000"
echo ""
echo "Optional — Telegram round summaries:"
echo "  Hermes World uses your existing Hermes Telegram gateway."
echo "  Make sure it's running before starting the simulation:"
echo "    hermes gateway start"
echo ""
