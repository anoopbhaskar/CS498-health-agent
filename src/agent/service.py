"""Production FitAgent orchestration service."""

from __future__ import annotations

import logging
from typing import Any

from agent.router import categorize_question
from config import settings
from memory.sqlite_store import SQLiteStore
from tools.nutrition import meal_recommendation
from tools.profile import extract_profile_updates, merge_list_fields, missing_profile_fields, profile_summary
from tools.progress import build_progress_summary, progress_answer
from tools.safety import evaluate_safety, professional_disclaimer
from tools.workouts import workout_recommendation

logger = logging.getLogger(__name__)


class FitAgentService:
    """Coordinates memory, routing, safety, and recommendation tools."""

    def __init__(self, store: SQLiteStore):
        self.store = store

    def submit_profile(self, payload: dict[str, Any]) -> dict[str, Any]:
        session_id = self.store.ensure_session(payload.get("session_id"))
        profile = self.store.upsert_profile(session_id, payload)
        logger.info(
            "profile_submitted",
            extra={"session_id": session_id, "category": "profile"},
        )
        return {
            "session_id": session_id,
            "profile": profile,
            "missing_fields": missing_profile_fields(profile),
        }

    def answer_question(self, message: str, session_id: str | None = None) -> dict[str, Any]:
        sid = self.store.ensure_session(session_id)
        profile = self.store.get_profile(sid)
        updates = extract_profile_updates(message)
        if updates:
            updates = merge_list_fields(profile, updates)
            profile = self.store.upsert_profile(sid, updates)

        category = categorize_question(message)
        self.store.add_message(sid, "user", message, category)
        logger.info(
            "chat_received",
            extra={"session_id": sid, "category": category},
        )

        used_tools: list[str] = []
        safety = evaluate_safety(message, profile)
        if safety.flagged:
            used_tools.append("safety_guardrails")
            response = safety.response or "I cannot safely help with that request."
            safety_flags = safety.reasons
        elif category == "meal":
            used_tools.extend(["profile_memory", "nutrition_planner"])
            response = meal_recommendation(message, profile) + professional_disclaimer(profile, message)
            safety_flags = []
        elif category == "workout":
            used_tools.extend(["profile_memory", "workout_planner"])
            response = workout_recommendation(message, profile) + professional_disclaimer(profile, message)
            safety_flags = []
        elif category == "progress":
            used_tools.extend(["profile_memory", "progress_tracker"])
            progress = self.store.list_progress(sid)
            response = progress_answer(progress)
            safety_flags = []
        elif category == "general":
            used_tools.append("profile_memory")
            response = (
                f"I can help with meal planning, workouts, safety-aware substitutions, and progress tracking. "
                f"Your current profile context is: {profile_summary(profile)}. Ask me for a meal plan, workout plan, "
                "or progress check and I will tailor it to that context."
            )
            safety_flags = []
        else:
            used_tools.append("scope_guardrail")
            response = (
                "I can only help with general health, fitness, nutrition, safety-aware exercise substitutions, "
                "and progress tracking. I cannot help with that out-of-scope request, but I can build a meal plan, "
                "workout routine, or progress check from your profile."
            )
            safety_flags = ["out_of_scope"]

        self.store.add_message(sid, "assistant", response, category)
        logger.info(
            "chat_answered",
            extra={
                "session_id": sid,
                "category": category,
                "tool": ",".join(used_tools),
            },
        )
        return {
            "session_id": sid,
            "response": response,
            "category": category,
            "safety_flags": safety_flags,
            "used_tools": used_tools,
        }

    def conversation_history(self, session_id: str) -> dict[str, Any]:
        return {"session_id": session_id, "messages": self.store.list_messages(session_id)}

    def progress(self, session_id: str) -> dict[str, Any]:
        progress = self.store.list_progress(session_id)
        return {
            "session_id": session_id,
            "snapshots": progress["snapshots"],
            "events": progress["events"],
            "summary": build_progress_summary(progress),
        }


def build_service() -> FitAgentService:
    return FitAgentService(SQLiteStore(settings.database_url))
