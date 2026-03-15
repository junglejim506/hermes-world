"""
orchestrator.py — Main Hermes World entry point.

Usage:
    python3 orchestrator.py "10 people stranded on a raft. Supplies for 7. Storm lasts 3 days."
    python3 orchestrator.py "10 people stranded on a raft." --agents 6 --rounds 3 --interval 2
    python3 orchestrator.py --tick   # run a single round tick (called by cron)
    python3 orchestrator.py --reset  # wipe world state and start fresh
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
import yaml

# ── Hermes path setup ─────────────────────────────────────────────────────────
_hermes_home = Path(os.environ.get("HERMES_HOME", Path.home() / ".hermes"))
_hermes_agent = _hermes_home / "hermes-agent"
if str(_hermes_agent) not in sys.path:
    sys.path.insert(0, str(_hermes_agent))

PROJECT_ROOT = Path(__file__).parent
WORLD_STATE_PATH = PROJECT_ROOT / "world_state.json"

# ── Load Hermes config ─────────────────────────────────────────────────────────
def _load_hermes_config() -> tuple[str, str | None]:
    """Return (model, base_url) from ~/.hermes/config.yaml."""
    config_path = _hermes_home / "config.yaml"
    if config_path.exists():
        with open(config_path) as f:
            cfg = yaml.safe_load(f) or {}
        model_cfg = cfg.get("model", {})
        return (
            model_cfg.get("default", "openrouter/hunter-alpha"),
            model_cfg.get("base_url"),
        )
    return "openrouter/hunter-alpha", None


# Global model config for scene generation
model, base_url = _load_hermes_config()

# ── World state helpers ────────────────────────────────────────────────────────
def load_state() -> dict:
    if WORLD_STATE_PATH.exists():
        with open(WORLD_STATE_PATH) as f:
            return json.load(f)
    return {}


def save_state(state: dict):
    with open(WORLD_STATE_PATH, "w") as f:
        json.dump(state, f, indent=2)
    print(f"[orchestrator] State saved — round {state.get('round', 0)}")


# ── Scene Auto-Generation ────────────────────────────────────────────────────
def _ensure_scene_exists(scenario: str, scene_type: str) -> str:
    """If scene doesn't exist, generate it via Hermes subagent before starting."""
    from scene_classifier import SCENE_TYPES, DEFAULT_SCENE
    
    if scene_type != DEFAULT_SCENE:
        return scene_type  # Known scene, all good
    
    # Check if scenario actually matches the default scene's keywords
    from scene_classifier import classify_scene
    text = scenario.lower()
    default_keywords = SCENE_TYPES[DEFAULT_SCENE]["keywords"]
    if any(kw in text for kw in default_keywords):
        return DEFAULT_SCENE  # Actually matches raft scenario
    
    # Unknown scene — generate it
    print(f"[orchestrator] Unknown scene type for: {scenario[:60]}...")
    print(f"[orchestrator] Generating scene via Hermes subagent...")
    
    # Use Python to generate scene config directly
    import re
    scene_slug = re.sub(r'[^a-z0-9]+', '_', scenario.lower().split('.')[0].split(',')[0])[:30].strip('_')
    if not scene_slug:
        scene_slug = "custom"
    
    # Generate scene config via LLM
    from run_agent import AIAgent
    agent = AIAgent(
        model=model,
        base_url=base_url,
        max_iterations=3,
        skip_context_files=True,
        skip_memory=True,
        quiet_mode=True,
    )
    
    prompt = f"""Generate a JSON config for a simulation scene. Return ONLY valid JSON.

Scenario: {scenario}

Required JSON format:
{{
  "scene_type": "{scene_slug}",
  "keywords": ["keyword1", "keyword2", ...],
  "world_stats": {{"stat1": value, "stat2": value}},
  "available_skills": ["skill1", "skill2", ...],
  "stat_labels": {{"stat1": "Display Label", "stat2": "Display Label"}}
}}

Make the stats, skills, and keywords specific to this scenario. Include 4-6 world stats, 5-7 skills, 5-10 keywords."""

    result = agent.run_conversation(
        user_message="Generate the scene config JSON.",
        system_message=prompt,
    )
    
    raw = result.get("response", "")
    match = re.search(r'\{[\s\S]*\}', raw)
    if match:
        try:
            config = json.loads(match.group(0))
            # Add to scene_classifier dynamically
            SCENE_TYPES[scene_slug] = {
                "keywords": config.get("keywords", []),
                "world_stats": config.get("world_stats", {}),
                "available_skills": config.get("available_skills", []),
                "stat_labels": config.get("stat_labels", {}),
            }
            print(f"[orchestrator] Generated scene: {scene_slug}")
            
            # Generate Three.js scene file
            _generate_frontend_scene(scene_slug, scenario)
            
            return scene_slug
        except json.JSONDecodeError:
            pass
    
    print(f"[orchestrator] Scene generation failed, using default: {DEFAULT_SCENE}")
    return DEFAULT_SCENE


def _generate_frontend_scene(scene_type: str, scenario: str):
    """Generate a Three.js scene file for the frontend."""
    scene_path = PROJECT_ROOT / "frontend" / "scenes" / f"{scene_type}.js"
    if scene_path.exists():
        return
    
    # Create a basic scene that works with the existing engine
    scene_code = f'''// {scene_type.title()} Scene — Auto-generated
export function create{scene_type.title().replace("_", "")}Scene(scene, THREE) {{
  // Ground
  const groundGeo = new THREE.PlaneGeometry(20, 20);
  const groundMat = new THREE.MeshStandardMaterial({{ 
    color: 0x1a1a2e,
    roughness: 0.8 
  }});
  const ground = new THREE.Mesh(groundGeo, groundMat);
  ground.rotation.x = -Math.PI / 2;
  ground.position.y = -0.5;
  scene.add(ground);
  
  // Ambient lighting
  const ambient = new THREE.AmbientLight(0x404060, 0.5);
  scene.add(ambient);
  
  // Directional light
  const dirLight = new THREE.DirectionalLight(0xffffff, 0.8);
  dirLight.position.set(5, 10, 5);
  scene.add(dirLight);
  
  // Background
  scene.background = new THREE.Color(0x0a0a1a);
  scene.fog = new THREE.Fog(0x0a0a1a, 10, 30);
}}
'''
    scene_path.write_text(scene_code)
    
    # Update world.js to include the new scene
    world_js = PROJECT_ROOT / "frontend" / "world.js"
    if world_js.exists():
        content = world_js.read_text()
        import_line = f"import {{ create{scene_type.title().replace('_', '')}Scene }} from './scenes/{scene_type}.js';"
        if import_line not in content:
            # Add import at top
            content = import_line + "\\n" + content
            world_js.write_text(content)
    
    print(f"[orchestrator] Generated frontend scene: {scene_path.name}")


# ── Bootstrap ─────────────────────────────────────────────────────────────────
def bootstrap(scenario: str, n_agents: int, round_interval: int) -> dict:
    """Build initial world state from scenario text."""
    from scene_classifier import classify_scene, get_scene_config
    from persona_generator import generate_personas

    print(f"[orchestrator] Classifying scenario...")
    scene_type = classify_scene(scenario)
    scene_type = _ensure_scene_exists(scenario, scene_type)
    scene_cfg = get_scene_config(scene_type)
    print(f"[orchestrator] Scene type: {scene_type}")

    print(f"[orchestrator] Generating {n_agents} personas...")
    agents = generate_personas(scenario, n_agents=n_agents)
    # Ensure all agents have required keys
    for a in agents:
        a.setdefault("memory_summary", "")
        a.setdefault("last_action", None)
        a.setdefault("skills", scene_cfg["available_skills"][:2])
        a.setdefault("position", {"x": 0.0, "z": 0.0})

    state = {
        "scenario": scenario,
        "scene_type": scene_type,
        "round": 0,
        "next_round_at": None,
        "round_interval_minutes": round_interval,
        "status": "running",
        "world": dict(scene_cfg["world_stats"]),
        "agents": agents,
        "influence_graph": [],
        "skill_registry": {},
        "round_log": [],
    }
    print(f"[orchestrator] Bootstrap complete — {len(agents)} agents in {scene_type} scene.")
    return state


# ── Cron tick ─────────────────────────────────────────────────────────────────
def tick():
    """Run one simulation round. Called by Hermes cron."""
    state = load_state()
    if not state or state.get("status") != "running":
        print("[orchestrator] Simulation not running — tick skipped.")
        return

    model, base_url = _load_hermes_config()

    from round_runner import run_round
    state = run_round(state, model=model, base_url=base_url)
    save_state(state)

    # Send Telegram summary
    try:
        from telegram_reporter import send_round_summary
        send_round_summary(state)
    except Exception as e:
        print(f"[orchestrator] Telegram send failed: {e}", file=sys.stderr)


# ── Intervention parser ────────────────────────────────────────────────────────
def apply_intervention(state: dict, command: str) -> dict:
    """
    Parse a natural-language intervention from Telegram and mutate world state.
    Examples:
      "reduce supplies by 30%"
      "add a new agent — a grieving mother"
      "introduce a rescue boat on the horizon"
      "fast forward 3 rounds"
    """
    import re
    cmd = command.lower()

    # Supply reduction
    m = re.search(r'reduce supplies by (\d+)%', cmd)
    if m and "supplies" in state["world"]:
        pct = int(m.group(1)) / 100
        state["world"]["supplies"] = max(0, int(state["world"]["supplies"] * (1 - pct)))
        state["world"]["events"].append(f"Supplies reduced by {m.group(1)}%")
        return state

    # Add event
    m = re.search(r'introduce (.+)', cmd)
    if m:
        event = m.group(1).strip().rstrip('.')
        state["world"]["events"].append(event.capitalize())
        return state

    # Fast forward
    m = re.search(r'fast forward (\d+) rounds?', cmd)
    if m:
        n = int(m.group(1))
        model, base_url = _load_hermes_config()
        from round_runner import run_round
        for _ in range(n):
            state = run_round(state, model=model, base_url=base_url)
        return state

    # Generic: treat as world event
    state["world"]["events"].append(command.strip())
    return state


# ── Cron registration ─────────────────────────────────────────────────────────
def register_cron(interval_minutes: int):
    """Tell Hermes cron to tick this simulation every N minutes."""
    try:
        from tools.cronjob_tools import schedule_cronjob
        prompt = (
            f"Run one Hermes World simulation round. "
            f"Use the terminal tool to execute: "
            f"cd {PROJECT_ROOT} && python3 orchestrator.py --tick"
        )
        result = schedule_cronjob(
            prompt=prompt,
            schedule=f"every {interval_minutes}m",
            name="hermes-world-tick",
            deliver="telegram",
        )
        print(f"[orchestrator] Cron registered: {result}")
    except Exception as e:
        print(f"[orchestrator] Cron registration failed (gateway may not be running): {e}", file=sys.stderr)
        print(f"[orchestrator] To run manually: python3 orchestrator.py --tick")


# ── CLI ───────────────────────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(description="Hermes World Orchestrator")
    parser.add_argument("scenario", nargs="?", help="Scenario description to start a new simulation")
    parser.add_argument("--agents", type=int, default=None, help="Number of agents (default: inferred from scenario)")
    parser.add_argument("--rounds", type=int, default=None, help="Run N rounds immediately then stop")
    parser.add_argument("--interval", type=int, default=5, help="Minutes between cron rounds (default: 5)")
    parser.add_argument("--tick", action="store_true", help="Run a single round tick (used by cron)")
    parser.add_argument("--reset", action="store_true", help="Reset world state to blank")
    parser.add_argument("--intervene", type=str, help="Apply a natural-language intervention to the running simulation")
    args = parser.parse_args()

    if args.reset:
        save_state({
            "scenario": "", "scene_type": "raft", "round": 0,
            "next_round_at": None, "round_interval_minutes": 5, "status": "idle",
            "world": {"supplies": 100, "morale": 75, "time_elapsed_hours": 0, "weather": "calm", "events": []},
            "agents": [], "influence_graph": [], "skill_registry": {}, "round_log": [],
        })
        print("[orchestrator] World state reset.")
        return

    if args.tick:
        tick()
        return

    if args.intervene:
        state = load_state()
        if not state:
            print("[orchestrator] No active simulation.")
            return
        state = apply_intervention(state, args.intervene)
        save_state(state)
        print(f"[orchestrator] Intervention applied: {args.intervene}")
        return

    if args.scenario:
        model, base_url = _load_hermes_config()
        state = bootstrap(args.scenario, n_agents=args.agents, round_interval=args.interval)
        save_state(state)

        # Register cron heartbeat
        register_cron(args.interval)

        # Run N rounds immediately if requested
        if args.rounds:
            from round_runner import run_round
            for i in range(args.rounds):
                print(f"\n{'─'*50}")
                state = run_round(state, model=model, base_url=base_url)
                save_state(state)
                try:
                    from telegram_reporter import send_round_summary
                    send_round_summary(state)
                except Exception as e:
                    print(f"[orchestrator] Telegram: {e}", file=sys.stderr)
                if i < args.rounds - 1:
                    time.sleep(2)  # brief pause between immediate rounds
        else:
            print(f"\n[orchestrator] Simulation bootstrapped. Cron will advance rounds every {args.interval} min.")
            print(f"[orchestrator] Or run now: python3 orchestrator.py --tick")
        return

    parser.print_help()


if __name__ == "__main__":
    main()
