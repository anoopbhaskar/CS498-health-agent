"""Progress tracking summaries from stored profile snapshots."""

from __future__ import annotations

from typing import Any


def build_progress_summary(progress: dict[str, list[dict[str, Any]]]) -> dict[str, Any]:
    snapshots = progress.get("snapshots", [])
    if not snapshots:
        return {
            "snapshot_count": 0,
            "weight_change_kg": None,
            "activity_change": None,
            "goal_changes": [],
        }
    first = snapshots[0]["profile"]
    latest = snapshots[-1]["profile"]
    weight_change = None
    if first.get("weight_kg") and latest.get("weight_kg"):
        weight_change = round(float(latest["weight_kg"]) - float(first["weight_kg"]), 1)
    activity_change = None
    if first.get("activity_level") != latest.get("activity_level"):
        activity_change = {
            "from": first.get("activity_level"),
            "to": latest.get("activity_level"),
        }
    goals = []
    for event in progress.get("events", []):
        if event["event_type"] == "fitness_goals":
            goals.append({"created_at": event["created_at"], "value": event["value"]})
    return {
        "snapshot_count": len(snapshots),
        "weight_change_kg": weight_change,
        "activity_change": activity_change,
        "goal_changes": goals,
    }


def progress_answer(progress: dict[str, list[dict[str, Any]]]) -> str:
    summary = build_progress_summary(progress)
    if summary["snapshot_count"] == 0:
        return "I do not have progress snapshots for this session yet. Submit your profile once, then update weight, activity level, steps, or goals over time."

    parts = [f"I have {summary['snapshot_count']} profile snapshot(s) for this session."]
    if summary["weight_change_kg"] is not None:
        change = summary["weight_change_kg"]
        if change < 0:
            parts.append(f"Your recorded weight is down {abs(change):.1f} kg since the first snapshot.")
        elif change > 0:
            parts.append(f"Your recorded weight is up {change:.1f} kg since the first snapshot.")
        else:
            parts.append("Your recorded weight is unchanged since the first snapshot.")
    if summary["activity_change"]:
        parts.append(
            f"Your activity level changed from {summary['activity_change']['from']} to {summary['activity_change']['to']}."
        )
    if summary["goal_changes"]:
        latest_goal = summary["goal_changes"][-1]["value"]
        parts.append(f"Your latest recorded goal set is: {', '.join(latest_goal) if latest_goal else 'none recorded'}.")
    parts.append("Use this as trend context, not a medical assessment; daily fluctuations are normal.")
    return " ".join(parts)
