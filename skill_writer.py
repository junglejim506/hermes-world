"""
skill_writer.py — Write Hermes-compatible SKILL.md files for agent-learned skills.

At runtime, skills are written to skills/agents/{agent_id}/{skill_name}/SKILL.md
inside the project directory. install.sh symlinks this folder into ~/.hermes/skills/
so Hermes picks them up automatically.
"""
from __future__ import annotations

import os
from pathlib import Path

# Project-local skills dir — install.sh symlinks this into ~/.hermes/skills/hermes-world/
PROJECT_ROOT = Path(__file__).parent
SKILLS_BASE = PROJECT_ROOT / "skills" / "agents"

SKILL_TEMPLATE = """\
---
name: {skill_name}
description: {description}
version: 1.0.0
author: {agent_name} (Hermes World)
license: MIT
dependencies: []
metadata:
  hermes:
    tags: [{tags}]
    related_skills: []
---

# {skill_name_title}

{description}

## Context

This skill was autonomously learned by agent **{agent_name}** during simulation round {round_learned}.

Scenario: {scenario}

## Usage

When this skill is invoked, the agent applies domain knowledge to:
{usage_steps}

## Notes

- Learned in response to: {trigger}
- Can be spread to other agents who observe its effectiveness.
"""


def write_skill(
    agent_id: str,
    skill_name: str,
    description: str,
    scenario: str,
    round_learned: int,
    trigger: str = "simulation need",
    tags: list = None,
    usage_steps: str = None,
) -> Path:
    """Write a SKILL.md for an agent-learned skill. Returns path to skill dir."""
    skill_dir = SKILLS_BASE / agent_id / skill_name
    skill_dir.mkdir(parents=True, exist_ok=True)

    skill_md = SKILL_TEMPLATE.format(
        skill_name=skill_name,
        skill_name_title=skill_name.replace("_", " ").title(),
        description=description,
        agent_name=agent_id,
        round_learned=round_learned,
        scenario=scenario,
        trigger=trigger,
        tags=", ".join(tags or [skill_name]),
        usage_steps=usage_steps or (
            f"- Applies {skill_name.replace('_', ' ')} expertise to the current situation\n"
            "- Reports outcome to the group"
        ),
    )

    skill_path = skill_dir / "SKILL.md"
    skill_path.write_text(skill_md)
    print(f"[skill_writer] Written skill '{skill_name}' for agent '{agent_id}' at {skill_path}")
    return skill_dir


def skill_exists(agent_id: str, skill_name: str) -> bool:
    return (SKILLS_BASE / agent_id / skill_name / "SKILL.md").exists()


def list_agent_skills(agent_id: str) -> list:
    agent_dir = SKILLS_BASE / agent_id
    if not agent_dir.exists():
        return []
    return [d.name for d in agent_dir.iterdir() if d.is_dir() and (d / "SKILL.md").exists()]
