"""
telegram_reporter.py — Send round summaries via Hermes's built-in Telegram gateway.

No bot token setup needed — uses the gateway already configured in ~/.hermes/.
The Hermes gateway must be running: `hermes gateway start`
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

_hermes_home = Path(os.environ.get("HERMES_HOME", Path.home() / ".hermes"))
_hermes_agent = _hermes_home / "hermes-agent"
if str(_hermes_agent) not in sys.path:
    sys.path.insert(0, str(_hermes_agent))


def _send(message: str, target: str = None) -> dict:
    """Send a message via Hermes gateway send_message_tool."""
    if target is None:
        # Use configured home channel from env, or let Hermes use its default
        channel = os.environ.get("TELEGRAM_HOME_CHANNEL")
        if channel:
            target = f"telegram:{channel}" if not channel.startswith("telegram") else channel
        else:
            target = "telegram"  # Falls back to Hermes gateway default
    try:
        from tools.send_message_tool import send_message_tool
        result = send_message_tool({"action": "send", "target": target, "message": message})
        return json.loads(result) if isinstance(result, str) else result
    except Exception as e:
        return {"error": str(e)}


def format_round_summary(state: dict) -> str:
    """Format a round summary as a Telegram message."""
    scenario = state.get("scenario", "Unknown scenario")
    scene_type = state.get("scene_type", "?")
    round_num = state.get("round", 0)
    world = state.get("world", {})
    agents = state.get("agents", [])
    log = state.get("round_log", [])
    skill_registry = state.get("skill_registry", {})
    influence_graph = state.get("influence_graph", [])

    lines = [
        f"🌍 *Hermes World — Round {round_num}*",
        f"_{scene_type.upper()} · {scenario[:80]}{'…' if len(scenario) > 80 else ''}_",
        "",
    ]

    # World stats
    stat_lines = []
    for k, v in world.items():
        if k == "events":
            continue
        if isinstance(v, (int, float)):
            stat_lines.append(f"  {k.replace('_', ' ').title()}: {v}")
        elif isinstance(v, bool):
            stat_lines.append(f"  {k.replace('_', ' ').title()}: {'✓' if v else '✗'}")
        else:
            stat_lines.append(f"  {k.replace('_', ' ').title()}: {v}")
    if stat_lines:
        lines.append("📊 *World State*")
        lines.extend(stat_lines)
        lines.append("")

    # Agent actions this round — from round_log
    current_round_actions = [
        e for e in log if isinstance(e, dict) and e.get("round") == round_num
    ]
    if current_round_actions:
        lines.append("🗣 *Agent Actions*")
        for entry in current_round_actions[:8]:  # cap at 8 for readability
            agent_id = entry.get("agent_id", "?")
            action = entry.get("action", {})
            atype = action.get("type", "idle")
            content = action.get("content", "")
            target = action.get("target", "")
            emoji = {"speak": "💬", "use_skill": "⚙️", "learn_skill": "📚", "idle": "💤"}.get(atype, "•")
            if atype == "speak":
                lines.append(f"  {emoji} *{agent_id}*: \"{content[:80]}\"")
            elif atype == "learn_skill":
                lines.append(f"  {emoji} *{agent_id}* learned `{action.get('new_skill_name', '?')}`")
            elif atype == "use_skill":
                lines.append(f"  {emoji} *{agent_id}* used `{content}` on {target}")
            else:
                lines.append(f"  {emoji} *{agent_id}* is idle")
        lines.append("")

    # New skills learned this round
    new_skills = [
        (name, info) for name, info in skill_registry.items()
        if info.get("round") == round_num
    ]
    if new_skills:
        lines.append("📚 *New Skills Learned*")
        for name, info in new_skills:
            lines.append(f"  • `{name}` by {info.get('learned_by', '?')}")
        lines.append("")

    # Influence summary
    strong = [e for e in influence_graph if e.get("strength", 0) >= 0.7]
    if strong:
        lines.append("🔗 *Strong Influences*")
        for edge in strong[:4]:
            lines.append(f"  {edge['from']} → {edge['to']} ({edge['strength']:.0%})")
        lines.append("")

    # Stance distribution
    stances = {}
    for a in agents:
        s = a.get("stance", "undecided")
        stances[s] = stances.get(s, 0) + 1
    if stances:
        lines.append("⚖️ *Stance Split*")
        for s, count in sorted(stances.items()):
            bar = "█" * count + "░" * (len(agents) - count)
            lines.append(f"  {s.title()}: {bar} {count}/{len(agents)}")
        lines.append("")

    # Recent events
    events = world.get("events", [])
    if events:
        lines.append("📋 *Events*")
        for ev in events[-3:]:
            lines.append(f"  • {ev}")
        lines.append("")

    lines.append("💬 _Reply to intervene: add agents, change conditions, inject events._")
    return "\n".join(lines)


def send_round_summary(state: dict) -> bool:
    """Format and send the round summary. Returns True on success."""
    message = format_round_summary(state)
    result = _send(message)
    if result.get("error"):
        print(f"[telegram_reporter] Failed to send: {result['error']}", file=sys.stderr)
        return False
    print(f"[telegram_reporter] Round {state.get('round')} summary sent via Hermes gateway.")
    return True


def send_message(text: str) -> bool:
    """Send an arbitrary message via Telegram."""
    result = _send(text)
    if result.get("error"):
        print(f"[telegram_reporter] Failed to send: {result['error']}", file=sys.stderr)
        return False
    return True
