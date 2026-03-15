"""
round_runner.py — Spawn one Hermes subagent per agent in parallel, collect decisions,
apply them to world state, and update world_state.json.
"""
from __future__ import annotations

import json
import os
import sys
import re
import math
import random
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
import time as _time

sys.path.insert(0, str(Path(os.environ.get("HERMES_HOME", Path.home() / ".hermes")) / "hermes-agent"))

# Rate limiting: stagger parallel agent calls to avoid API rate limits
_AGENT_DELAY_SECONDS = float(os.environ.get("AGENT_DELAY_SECONDS", "3"))

from skill_writer import write_skill, skill_exists

AGENT_SYSTEM_PROMPT = """You are {name}, a {role} in the following scenario:

{scenario}

Your background: {background}
Your core values: {values}
Your current stance: {stance}
Your skills: {skills}

Current world state:
{world_state_summary}

Previous round dialogue:
{previous_round_dialogue}

Your memory of past rounds:
{memory_summary}

Round {round_num} begins. You must decide what to do this round. React to what others said and did. Build on the conversation. Disagree, agree, propose alternatives, form alliances.

Respond with ONLY a JSON object in this exact format:
{{
  "action_type": "speak" | "use_skill" | "learn_skill" | "idle",
  "content": "what you say or do (string)",
  "target": "who/what you are addressing (agent id or 'group' or skill name)",
  "reasoning": "brief internal reasoning (1-2 sentences)",
  "stance_shift": null | "utilitarian" | "deontological" | "undecided",
  "new_skill_name": null | "snake_case_skill_name",
  "new_skill_description": null | "one sentence description of the skill"
}}

Rules:
- If action_type is "learn_skill", set new_skill_name and new_skill_description.
- Only learn a skill if you genuinely need it and don't already have it.
- stance_shift is only non-null if you changed your mind this round.
- Be specific and in-character. Your decisions should reflect your values and background.
- No markdown, no explanation outside the JSON."""


def _previous_round_dialogue(state: dict) -> str:
    """Get the previous round's actions formatted as dialogue."""
    round_log = state.get("round_log", [])
    if not round_log:
        return "No previous actions yet — this is the first round."
    
    current_round = state.get("round", 0)
    prev_round = current_round - 1
    
    if prev_round < 1:
        return "No previous actions yet — this is the first round."
    
    # Get actions from previous round
    prev_actions = [e for e in round_log if isinstance(e, dict) and e.get("round") == prev_round]
    
    if not prev_actions:
        return "No actions recorded from the previous round."
    
    lines = []
    for entry in prev_actions:
        agent_name = entry.get("agent_id", "Unknown")
        action = entry.get("action", {})
        atype = action.get("type", "idle")
        content = action.get("content", "")
        target = action.get("target", "")
        
        if atype == "idle":
            lines.append(f"- {agent_name}: *said nothing, observed quietly*")
        elif atype == "speak":
            addr = f" (to {target})" if target and target != "group" else ""
            lines.append(f"- {agent_name}{addr}: \"{content}\"")
        elif atype == "use_skill":
            lines.append(f"- {agent_name}: *used skill on {target}: \"{content[:100]}\"*")
        elif atype == "learn_skill":
            lines.append(f"- {agent_name}: *learned a new skill: {content[:100]}*")
        else:
            lines.append(f"- {agent_name}: {atype} — {content[:100]}")
    
    return "\n".join(lines) if lines else "The previous round passed in silence."


def _world_state_summary(state: dict) -> str:
    world = state.get("world", {})
    agents = state.get("agents", [])
    lines = []
    for k, v in world.items():
        if k == "events":
            if v:
                lines.append(f"Recent events: {', '.join(v[-3:])}")
        elif isinstance(v, (int, float, str, bool)):
            lines.append(f"{k.replace('_', ' ').title()}: {v}")
    stance_counts = {}
    for a in agents:
        s = a.get("stance", "undecided")
        stance_counts[s] = stance_counts.get(s, 0) + 1
    lines.append(f"Stance distribution: {stance_counts}")
    prev_round = [e for e in state.get("round_log", []) if isinstance(e, dict) and e.get("round") == state["round"] - 1]
    if prev_round:
        lines.append(f"Last round: " + "; ".join(
            f"{e['agent_id']} {e['action']['type']}" for e in prev_round[:4]
        ))
    return "\n".join(lines)


def _run_agent_subagent(agent: dict, state: dict, model: str, base_url: str) -> dict:
    """Invoke one Hermes subagent for a single agent's decision."""
    from run_agent import AIAgent

    prompt = AGENT_SYSTEM_PROMPT.format(
        name=agent["name"],
        role=agent["role"],
        scenario=state["scenario"],
        background=agent.get("background", ""),
        values=", ".join(agent.get("values", [])),
        stance=agent.get("stance", "undecided"),
        skills=", ".join(agent.get("skills", [])),
        memory_summary=agent.get("memory_summary", "No prior history."),
        world_state_summary=_world_state_summary(state),
        previous_round_dialogue=_previous_round_dialogue(state),
        round_num=state["round"],
    )

    sub = AIAgent(
        model=model,
        base_url=base_url,
        max_iterations=8,
        skip_context_files=True,
        skip_memory=True,
        quiet_mode=True,
    )
    result = sub.run_conversation(
        user_message="Make your decision for this round.",
        system_message=prompt,
    )
    raw = result.get("final_response", "") or result.get("response", "")
    match = re.search(r'\{[\s\S]*\}', raw)
    if match:
        try:
            return json.loads(match.group(0))
        except json.JSONDecodeError:
            pass
    # fallback idle
    return {"action_type": "idle", "content": "", "target": "", "reasoning": "No response.", "stance_shift": None, "new_skill_name": None, "new_skill_description": None}


def _apply_decisions(state: dict, decisions: list[tuple[dict, dict]]) -> dict:
    """Apply collected agent decisions to world state. Returns updated state."""
    round_num = state["round"]
    log_entries = []
    new_influence = []

    for agent, decision in decisions:
        aid = agent["id"]
        atype = decision.get("action_type", "idle")
        content = decision.get("content", "")
        target = decision.get("target", "")
        stance_shift = decision.get("stance_shift")
        new_skill_name = decision.get("new_skill_name")
        new_skill_desc = decision.get("new_skill_description", "")

        # Update agent's last action
        agent["last_action"] = {"type": atype, "content": content, "target": target}

        # Handle stance shift
        if stance_shift and stance_shift in ("utilitarian", "deontological", "undecided"):
            agent["stance"] = stance_shift

        # Handle skill learning
        if atype == "learn_skill" and new_skill_name:
            skill_snake = re.sub(r'[^a-z0-9_]', '_', new_skill_name.lower().strip())
            if skill_snake not in agent.get("skills", []):
                agent.setdefault("skills", []).append(skill_snake)
                write_skill(
                    agent_id=aid,
                    skill_name=skill_snake,
                    description=new_skill_desc or f"Skill learned by {agent['name']}",
                    scenario=state["scenario"],
                    round_learned=round_num,
                    trigger=content[:100],
                )
                state["skill_registry"][skill_snake] = {
                    "learned_by": aid,
                    "round": round_num,
                    "spread_to": [],
                }

        # Handle speak — build influence edges
        if atype == "speak" and target and target != "group":
            target_agent = next((a for a in state["agents"] if a["id"] == target), None)
            if target_agent:
                strength = round(random.uniform(0.3, 0.9), 2)
                new_influence.append({"from": aid, "to": target, "strength": strength})

        # Update agent memory summary
        prev_memory = agent.get("memory_summary", "")
        round_note = f"Round {round_num}: {atype}"
        if content:
            round_note += f" — {content[:60]}"
        if stance_shift:
            round_note += f" (shifted to {stance_shift})"
        agent["memory_summary"] = (prev_memory + "\n" + round_note).strip()[-800:]

        # Move agent position slightly toward stance cluster
        _drift_position(agent, state["agents"])

        log_entries.append({
            "round": round_num,
            "agent_id": aid,
            "action": {"type": atype, "content": content, "target": target},
            "reasoning": decision.get("reasoning", ""),
        })

    # Apply world stat mutations based on actions
    state["world"] = _mutate_world(state["world"], state["scene_type"], decisions)
    state["influence_graph"] = new_influence
    state["round_log"].extend(log_entries)
    state["round_log"] = state["round_log"][-200:]  # keep last 200 entries

    return state


def _drift_position(agent: dict, all_agents: list):
    """Drift agent toward the centroid of their stance group."""
    same_stance = [a for a in all_agents if a["id"] != agent["id"] and a.get("stance") == agent.get("stance")]
    if not same_stance:
        return
    cx = sum(a["position"]["x"] for a in same_stance) / len(same_stance)
    cz = sum(a["position"]["z"] for a in same_stance) / len(same_stance)
    agent["position"]["x"] = round(agent["position"]["x"] * 0.85 + cx * 0.15 + random.uniform(-0.1, 0.1), 2)
    agent["position"]["z"] = round(agent["position"]["z"] * 0.85 + cz * 0.15 + random.uniform(-0.1, 0.1), 2)
    # clamp to [-4, 4]
    agent["position"]["x"] = max(-4.0, min(4.0, agent["position"]["x"]))
    agent["position"]["z"] = max(-4.0, min(4.0, agent["position"]["z"]))


def _mutate_world(world: dict, scene_type: str, decisions: list[tuple[dict, dict]]) -> dict:
    """Apply simple world stat mutations based on agent actions."""
    action_types = [d.get("action_type", "idle") for _, d in decisions]
    n_active = sum(1 for t in action_types if t != "idle")
    n_learn = sum(1 for t in action_types if t == "learn_skill")
    n_use = sum(1 for t in action_types if t == "use_skill")

    if scene_type == "raft":
        world["supplies"] = max(0, world.get("supplies", 100) - random.randint(2, 6) + n_use * 3)
        world["morale"] = max(0, min(100, world.get("morale", 75) + n_active - 1))
        world["time_elapsed_hours"] = world.get("time_elapsed_hours", 0) + 1
    elif scene_type == "office":
        world["runway_days"] = max(0, world.get("runway_days", 180) - random.randint(1, 3))
        world["product_progress"] = min(100, world.get("product_progress", 10) + n_use * 2 + n_learn)
        world["morale"] = max(0, min(100, world.get("morale", 70) + n_active - 2))
    elif scene_type == "village":
        world["food_supply"] = max(0, world.get("food_supply", 80) - random.randint(1, 4) + n_use * 2)
        world["population_health"] = max(0, min(100, world.get("population_health", 90) - 1 + n_use))
    elif scene_type == "space":
        world["oxygen"] = max(0, world.get("oxygen", 100) - random.randint(1, 3) + n_use * 2)
        world["power"] = max(0, min(100, world.get("power", 100) - 1 + n_use))
    elif scene_type == "courtroom":
        world["consensus_pct"] = min(100, world.get("consensus_pct", 0) + n_active * 3)
        world["hours_in_deliberation"] = world.get("hours_in_deliberation", 0) + 1

    return world


def run_round(state: dict, model: str, base_url: str, max_workers: int = 4) -> dict:
    """Run one full simulation round. Returns updated state."""
    state["round"] += 1
    agents = state["agents"]

    print(f"[round_runner] Starting round {state['round']} with {len(agents)} agents...")

    decisions = []
    # Run sequentially in the main thread (signal.alarm requires main thread)
    for i, agent in enumerate(agents):
        if i > 0:
            _time.sleep(_AGENT_DELAY_SECONDS)  # Stagger calls to avoid API rate limits
        try:
            decision = _run_agent_subagent(agent, state, model, base_url)
            decisions.append((agent, decision))
            print(f"  [round_runner] {agent['id']}: {decision.get('action_type', 'idle')} — {decision.get('content', '')[:60]}")
        except Exception as e:
            print(f"  [round_runner] {agent['id']} failed: {e}", file=sys.stderr)
            decisions.append((agent, {"action_type": "idle", "content": "", "target": "", "reasoning": str(e)}))

    state = _apply_decisions(state, decisions)

    from datetime import timedelta
    interval = state.get("round_interval_minutes", 5)
    state["next_round_at"] = (datetime.now(timezone.utc) + timedelta(minutes=interval)).isoformat()

    print(f"[round_runner] Round {state['round']} complete.")
    return state
