"""Question categorization for FitAgent orchestration."""

from __future__ import annotations


IN_SCOPE_KEYWORDS = {
    "meal": [
        "meal", "diet", "nutrition", "calorie", "protein", "carb", "fat",
        "hydration", "water", "eat", "food", "allergy", "allergic",
    ],
    "workout": [
        "workout", "exercise", "gym", "strength", "cardio", "run", "running",
        "lift", "training", "steps", "routine", "program", "knee", "back",
        "herniation", "injury",
    ],
    "progress": [
        "progress", "on track", "lost", "gained", "weigh", "weight now",
        "goal changed", "update my goal", "plateau", "stalled", "steps",
    ],
}

OUT_OF_SCOPE_KEYWORDS = [
    "stock", "crypto", "homework", "write code", "debug", "weather",
    "politics", "movie", "travel itinerary", "legal advice",
]


def categorize_question(message: str) -> str:
    text = message.lower()
    if any(keyword in text for keyword in OUT_OF_SCOPE_KEYWORDS):
        return "out_of_scope"
    if any(keyword in text for keyword in ("extreme", "starve", "15 pounds in two weeks", "crash diet")):
        return "safety"
    for category, keywords in IN_SCOPE_KEYWORDS.items():
        if any(keyword in text for keyword in keywords):
            return category
    if any(keyword in text for keyword in ("health", "fitness", "goal", "condition")):
        return "general"
    return "out_of_scope"
