"""
scene_classifier.py — Map scenario text to scene type and world stat schema.
"""

SCENE_TYPES = {
    "raft": {
        "keywords": ["raft", "stranded", "island", "survival", "storm", "sea", "ocean", "bunker", "desert", "wilderness"],
        "world_stats": {"supplies": 100, "morale": 75, "time_elapsed_hours": 0, "weather": "calm", "events": []},
        "available_skills": ["build", "forage", "fish", "signal", "heal", "ration", "navigate"],
        "stat_labels": {"supplies": "Supplies %", "morale": "Morale %", "weather": "Weather"},
    },
    "office": {
        "keywords": ["startup", "office", "founding", "runway", "product", "team", "company", "venture", "ceo", "cto"],
        "world_stats": {"runway_days": 180, "product_progress": 10, "morale": 70, "user_count": 0, "events": []},
        "available_skills": ["code", "design", "pitch", "hire", "fundraise", "market", "pivot"],
        "stat_labels": {"runway_days": "Runway (days)", "product_progress": "Product %", "user_count": "Users"},
    },
    "village": {
        "keywords": ["village", "drought", "famine", "harvest", "crops", "community", "town", "peasant", "governor"],
        "world_stats": {"food_supply": 80, "population_health": 90, "infrastructure": 60, "relations": 70, "events": []},
        "available_skills": ["farm", "trade", "build", "heal", "negotiate", "govern", "store"],
        "stat_labels": {"food_supply": "Food Supply %", "population_health": "Health %", "infrastructure": "Infrastructure %"},
    },
    "space": {
        "keywords": ["space", "colony", "mars", "station", "asteroid", "rocket", "nasa", "oxygen", "hull", "crew"],
        "world_stats": {"oxygen": 100, "power": 100, "food": 80, "hull_integrity": 95, "earth_contact": True, "events": []},
        "available_skills": ["repair", "mine", "grow_food", "research", "communicate", "navigate"],
        "stat_labels": {"oxygen": "O₂ %", "power": "Power %", "hull_integrity": "Hull %"},
    },
    "courtroom": {
        "keywords": ["jury", "trial", "court", "verdict", "defendant", "lawyer", "judge", "evidence", "deliberate"],
        "world_stats": {"consensus_pct": 0, "evidence_weight": 50, "hours_in_deliberation": 0, "events": []},
        "available_skills": ["argue", "cross_examine", "present_evidence", "deliberate", "vote"],
        "stat_labels": {"consensus_pct": "Consensus %", "evidence_weight": "Evidence Weight"},
    },
}

DEFAULT_SCENE = "raft"


def classify_scene(scenario: str) -> str:
    """Return scene_type string for a given scenario text."""
    text = scenario.lower()
    scores = {scene: 0 for scene in SCENE_TYPES}
    for scene, cfg in SCENE_TYPES.items():
        for kw in cfg["keywords"]:
            if kw in text:
                scores[scene] += 1
    best = max(scores, key=lambda s: scores[s])
    return best if scores[best] > 0 else DEFAULT_SCENE


def get_scene_config(scene_type: str) -> dict:
    return SCENE_TYPES.get(scene_type, SCENE_TYPES[DEFAULT_SCENE])
