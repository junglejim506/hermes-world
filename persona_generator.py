"""
persona_generator.py — Generate agent personas from a scenario string using Hermes.
"""

import json
import os
import sys
import re
from pathlib import Path

# Add the Hermes agent directory to path (respects HERMES_HOME env var)
_hermes_home = Path(os.environ.get("HERMES_HOME", Path.home() / ".hermes"))
_hermes_agent = _hermes_home / "hermes-agent"
if str(_hermes_agent) not in sys.path:
    sys.path.insert(0, str(_hermes_agent))

from scene_classifier import classify_scene, get_scene_config

PERSONA_SYSTEM_PROMPT = """You are a world-builder AI. Given a scenario description, generate a set of distinct,
realistic human personas appropriate for that scenario.

Each persona must have:
- id: snake_case short identifier (e.g. "elena_c")
- name: Full name (e.g. "Elena C.")
- role: Job/role title relevant to the scenario
- background: 1-2 sentence backstory
- values: list of 2-3 core values (e.g. ["pragmatism", "duty of care"])
- stance: one of "utilitarian", "deontological", "undecided"
- skills: list of 2-3 skills from the available_skills list
- position: {"x": float, "z": float} — random position in range [-4, 4]

Return ONLY a valid JSON array of persona objects. No markdown, no explanation."""


def generate_personas(scenario: str, n_agents: int = None, model: str = None) -> list:
    """Call Hermes to generate personas for the given scenario."""
    scene_type = classify_scene(scenario)
    scene_cfg = get_scene_config(scene_type)
    available_skills = scene_cfg["available_skills"]

    if n_agents is None:
        # infer from scenario text (look for numbers)
        import re
        nums = re.findall(r'\b(\d+)\s+(?:people|person|survivor|agent|member|crew|juror|character)', scenario.lower())
        n_agents = int(nums[0]) if nums else 5
        n_agents = max(3, min(n_agents, 8))  # clamp 3-8

    prompt = f"""Scenario: {scenario}

Scene type: {scene_type}
Number of agents: {n_agents}
Available skills: {available_skills}

Generate exactly {n_agents} distinct personas appropriate for this scenario.
Vary their stances — roughly 1/3 utilitarian, 1/3 deontological, 1/3 undecided.
Spread positions across the scene (x and z in range -4 to 4).
Return only a JSON array."""

    try:
        from run_agent import AIAgent
        import yaml

        config_path = os.path.expanduser("~/.hermes/config.yaml")
        with open(config_path) as f:
            cfg = yaml.safe_load(f)

        agent = AIAgent(
            model=cfg.get("model", {}).get("default", "openrouter/hunter-alpha"),
            base_url=cfg.get("model", {}).get("base_url"),
            max_iterations=5,
            skip_context_files=True,
            skip_memory=True,
            quiet_mode=True,
        )

        result = agent.run_conversation(
            user_message=prompt,
            system_message=PERSONA_SYSTEM_PROMPT,
        )

        raw = result.get("response", "")
        # extract JSON array
        match = re.search(r'\[[\s\S]*\]', raw)
        if match:
            personas = json.loads(match.group(0))
            return personas

    except Exception as e:
        print(f"[persona_generator] LLM call failed: {e}, using fallback personas", file=sys.stderr)

    return _fallback_personas(scenario, n_agents, scene_type, available_skills)


def _fallback_personas(scenario: str, n_agents: int, scene_type: str, available_skills: list) -> list:
    """Return hardcoded fallback personas when LLM is unavailable."""
    import random, math
    stances = ["utilitarian", "deontological", "undecided"]
    names = [
        ("elena_c", "Elena C.", "Doctor"),
        ("james_t", "James T.", "Engineer"),
        ("sofia_m", "Sofia M.", "Psychologist"),
        ("david_k", "David K.", "Former Military"),
        ("amara_n", "Amara N.", "Teacher"),
        ("chen_w", "Chen W.", "Biologist"),
        ("tom_h", "Tom H.", "Fisherman"),
        ("priya_r", "Priya R.", "Lawyer"),
    ][:n_agents]

    personas = []
    for i, (pid, name, role) in enumerate(names):
        angle = (2 * math.pi * i) / n_agents
        personas.append({
            "id": pid,
            "name": name,
            "role": role,
            "background": f"Experienced {role.lower()} caught in this situation.",
            "values": ["survival", "duty"],
            "stance": stances[i % 3],
            "skills": available_skills[:2] if len(available_skills) >= 2 else available_skills,
            "position": {"x": round(3 * math.cos(angle), 2), "z": round(3 * math.sin(angle), 2)},
            "last_action": None,
            "memory_summary": "",
        })
    return personas
