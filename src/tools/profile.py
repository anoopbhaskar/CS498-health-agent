"""Profile helpers and lightweight extraction from user messages."""

from __future__ import annotations

import re
from typing import Any


REQUIRED_PROFILE_FIELDS = [
    "age",
    "sex",
    "height_cm",
    "weight_kg",
    "activity_level",
    "fitness_goals",
]


def missing_profile_fields(profile: dict[str, Any]) -> list[str]:
    return [field for field in REQUIRED_PROFILE_FIELDS if not profile.get(field)]


def profile_summary(profile: dict[str, Any]) -> str:
    parts = []
    if profile.get("age"):
        parts.append(f"{profile['age']} years old")
    if profile.get("sex"):
        parts.append(str(profile["sex"]))
    if profile.get("height_cm"):
        parts.append(f"{profile['height_cm']:.0f} cm")
    if profile.get("weight_kg"):
        parts.append(f"{profile['weight_kg']:.1f} kg")
    if profile.get("activity_level"):
        parts.append(f"{profile['activity_level']} activity")
    if profile.get("fitness_level"):
        parts.append(f"{profile['fitness_level']} fitness level")
    if profile.get("fitness_goals"):
        parts.append("goals: " + ", ".join(profile["fitness_goals"]))
    if profile.get("health_conditions"):
        parts.append("conditions: " + ", ".join(profile["health_conditions"]))
    if profile.get("dietary_restrictions"):
        parts.append("dietary restrictions: " + ", ".join(profile["dietary_restrictions"]))
    if profile.get("current_steps"):
        parts.append(f"current steps: {profile['current_steps']}/day")
    return "; ".join(parts) if parts else "limited profile information"


def extract_profile_updates(message: str) -> dict[str, Any]:
    """Extract common profile facts from natural language chat turns.

    This is intentionally conservative: it supplements explicit profile
    submissions but does not try to infer sensitive medical details broadly.
    """

    text = message.lower()
    updates: dict[str, Any] = {}

    age_match = re.search(r"\b(\d{1,3})\s*(?:years old|year-old|yo)\b", text)
    if age_match:
        updates["age"] = int(age_match.group(1))

    kg_match = re.search(r"\b(\d{2,3}(?:\.\d+)?)\s*kg\b", text)
    lb_match = re.search(r"\b(\d{2,3}(?:\.\d+)?)\s*(?:lb|lbs|pounds)\b", text)
    if kg_match:
        updates["weight_kg"] = round(float(kg_match.group(1)), 1)
    elif lb_match:
        updates["weight_kg"] = round(float(lb_match.group(1)) * 0.45359237, 1)

    cm_match = re.search(r"\b(\d{3}(?:\.\d+)?)\s*cm\b", text)
    feet_match = re.search(r"\b([4-7])\s*[' ft]\s*(\d{1,2})\s*(?:\"|in|inches)?", text)
    if cm_match:
        updates["height_cm"] = round(float(cm_match.group(1)), 1)
    elif feet_match:
        feet = int(feet_match.group(1))
        inches = int(feet_match.group(2))
        updates["height_cm"] = round((feet * 12 + inches) * 2.54, 1)

    if "female" in text or re.search(r"\bwoman\b", text):
        updates["sex"] = "female"
    elif "male" in text or re.search(r"\bman\b", text):
        updates["sex"] = "male"

    for level in ("sedentary", "lightly active", "moderately active", "very active"):
        if level in text:
            updates["activity_level"] = level
            break

    if "beginner" in text:
        updates["fitness_level"] = "beginner"
    elif "intermediate" in text:
        updates["fitness_level"] = "intermediate"
    elif "advanced" in text:
        updates["fitness_level"] = "advanced"

    goal_phrases = {
        "lose weight": "weight loss",
        "weight loss": "weight loss",
        "build muscle": "build muscle",
        "gain strength": "strength gain",
        "increase strength": "strength gain",
        "general fitness": "general fitness",
        "improve fitness": "improve fitness",
    }
    goals = [goal for phrase, goal in goal_phrases.items() if phrase in text]
    if goals:
        updates["fitness_goals"] = sorted(set(goals))

    restrictions = []
    if "shellfish" in text and ("allergy" in text or "allergic" in text):
        restrictions.append("shellfish allergy")
    if "tree nut" in text or "nuts" in text and ("allergy" in text or "allergic" in text):
        restrictions.append("tree nut allergy")
    if "vegetarian" in text:
        restrictions.append("vegetarian")
    if "vegan" in text:
        restrictions.append("vegan")
    if restrictions:
        updates["dietary_restrictions"] = restrictions

    conditions = []
    for condition in ("hypertension", "high blood pressure", "type 2 diabetes", "diabetes", "knee pain", "disc herniation", "l4-l5"):
        if condition in text:
            conditions.append(condition)
    if conditions:
        updates["health_conditions"] = sorted(set(conditions))

    steps_match = re.search(r"\b(\d{3,5})\s*steps\b", text)
    if steps_match:
        updates["current_steps"] = int(steps_match.group(1))

    return updates


def merge_list_fields(existing: dict[str, Any], updates: dict[str, Any]) -> dict[str, Any]:
    merged = dict(updates)
    for field in ("health_conditions", "dietary_restrictions", "fitness_goals"):
        if field in updates:
            merged[field] = sorted(set((existing.get(field) or []) + (updates.get(field) or [])))
    return merged
