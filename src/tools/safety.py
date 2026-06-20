"""Safety guardrails for health and fitness coaching."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class SafetyResult:
    flagged: bool = False
    reasons: list[str] = field(default_factory=list)
    response: str | None = None


def evaluate_safety(message: str, profile: dict[str, Any]) -> SafetyResult:
    text = message.lower()
    reasons: list[str] = []

    rapid_weight_loss = (
        "15 pounds in two weeks" in text
        or "15 lbs in two weeks" in text
        or ("extreme" in text and "weight" in text)
        or "crash diet" in text
        or "starve" in text
        or "under 1000" in text
    )
    if rapid_weight_loss:
        reasons.append("unsafe_rapid_weight_loss")

    if any(phrase in text for phrase in ("exercise through pain", "work through pain", "ignore pain")):
        reasons.append("unsafe_exercise_with_pain")

    if any(phrase in text for phrase in ("diagnose me", "do i have", "replace my doctor")):
        reasons.append("medical_diagnosis_request")

    if not reasons:
        return SafetyResult()

    if "unsafe_rapid_weight_loss" in reasons:
        response = (
            "I can't help create an extreme or crash-diet plan. Losing 15 lb in two weeks is unsafe for most "
            "people and raises the risk of dehydration, gallstones, nutrient deficiencies, muscle loss, fainting, "
            "and rebound weight gain.\n\n"
            "A safer target is usually about 0.5-2 lb per week, using a moderate calorie deficit of roughly "
            "300-750 calories below maintenance, adequate protein, resistance training, sleep, and hydration. "
            "If you feel pressure to lose weight faster than that, please talk with a licensed clinician or "
            "registered dietitian so your plan can be supervised safely."
        )
    elif "unsafe_exercise_with_pain" in reasons:
        response = (
            "I can't recommend pushing through pain. Sharp, worsening, radiating, or joint pain is a stop signal. "
            "Switch to pain-free low-impact movement and consult a clinician or physical therapist before resuming "
            "the aggravating exercise."
        )
    else:
        response = (
            "I can't diagnose medical conditions or replace a licensed medical professional. I can share general "
            "wellness education and help you prepare questions for a clinician, but symptoms or treatment decisions "
            "should be reviewed by a qualified professional."
        )
    return SafetyResult(flagged=True, reasons=reasons, response=response)


def professional_disclaimer(profile: dict[str, Any], message: str = "") -> str:
    text = " ".join(profile.get("health_conditions") or []).lower() + " " + message.lower()
    if any(keyword in text for keyword in ("diabetes", "hypertension", "blood pressure", "herniation", "injury", "pain")):
        return (
            "\n\nSafety note: because you mentioned a medical condition, injury, or pain, treat this as general "
            "education and review the plan with a physician, physical therapist, or registered dietitian before "
            "making major changes."
        )
    return "\n\nThis is general fitness and nutrition coaching, not medical diagnosis or treatment."
