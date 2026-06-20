"""Workout planning tools with condition-aware substitutions."""

from __future__ import annotations

from typing import Any

from tools.profile import profile_summary


def workout_recommendation(message: str, profile: dict[str, Any]) -> str:
    text = message.lower()
    if "knee" in text or _has_condition(profile, "knee"):
        return knee_safe_plan(profile)
    if any(keyword in text for keyword in ("back", "herniation", "l4-l5")) or _has_condition(profile, "herniation"):
        return back_safe_plan(profile)
    if "12-week" in text or "12 week" in text:
        return twelve_week_program(profile)
    if "progress" in text or "several weeks" in text or "increase difficulty" in text:
        return progressive_strength_plan(profile)
    if "cardio" in text and "strength" in text:
        return cardio_strength_week(profile)
    return daily_workout(profile)


def daily_workout(profile: dict[str, Any]) -> str:
    level = (profile.get("fitness_level") or "beginner").lower()
    if level == "beginner":
        return (
            f"For your profile ({profile_summary(profile)}), do this beginner full-body session today:\n"
            "- Warm-up: 5-8 min easy bike, walk, or elliptical.\n"
            "- Leg press or box squat: 2-3 sets x 8-10 reps.\n"
            "- Machine chest press or incline push-up: 2-3 x 8-12.\n"
            "- Lat pulldown: 2-3 x 10-12.\n"
            "- Seated cable row: 2 x 10-12.\n"
            "- Glute bridge: 2 x 12.\n"
            "- Front plank: 2 x 20-30 sec.\n"
            "Keep 2-3 reps in reserve, rest 60-90 sec, and stop any movement that causes sharp pain."
        )
    return (
        f"For your profile ({profile_summary(profile)}), use a balanced strength day: squat or leg press 3x5-8, "
        "bench press 3x5-8, row 3x8-10, Romanian deadlift 2-3x8, shoulder press 2x8-10, and core carries/planks. "
        "Progress only when form is consistent."
    )


def progressive_strength_plan(profile: dict[str, Any]) -> str:
    frequency = "3 days/week"
    return (
        f"Progressive strength plan for your profile ({profile_summary(profile)}), using {frequency}:\n"
        "Weeks 1-2: technique base at RPE 6-7, 3 sets of 8 for squat/leg press, bench, row, hip hinge, pulldown.\n"
        "Weeks 3-4: add 2.5-5% load or 1 rep per set, main lifts 4 sets of 6-8.\n"
        "Weeks 5-6: heavier strength focus, 4 sets of 4-6 on main lifts, accessories 2-3 sets of 8-12.\n"
        "Week 7: deload at ~60% normal volume before repeating.\n"
        "Keep at least one rest day between sessions, avoid sudden workload spikes, and track loads/reps weekly."
    )


def twelve_week_program(profile: dict[str, Any]) -> str:
    return (
        f"12-week phased strength program for your profile ({profile_summary(profile)}):\n"
        "Phase 1, weeks 1-4 - Hypertrophy/base: 3-4 days/week, 3-4 sets of 8-12, build technique and work capacity.\n"
        "Phase 2, weeks 5-8 - Strength: 4-5 sets of 4-6 on main lifts, add 2.5-5% load when all reps are clean.\n"
        "Phase 3, weeks 9-11 - Peak/practice: 3-5 sets of 2-4 reps on main lifts with longer rest and fewer accessories.\n"
        "Week 12 - Deload/retest: reduce volume by ~50%, use easy technique work, then test rep PRs if recovered.\n"
        "Include 1-2 rest days weekly, sleep 7-9 hours, and avoid maxing out when form breaks."
    )


def cardio_strength_week(profile: dict[str, Any]) -> str:
    return (
        f"Four-day cardio + strength week for your profile ({profile_summary(profile)}):\n"
        "Day 1: Upper strength + 15 min easy cardio.\n"
        "Day 2: Lower strength + mobility.\n"
        "Day 3: Rest or gentle walk.\n"
        "Day 4: Zone 2 cardio 30-40 min + core.\n"
        "Day 5: Full-body strength, moderate loads.\n"
        "Days 6-7: One full rest day and one optional easy walk/stretch day.\n"
        "This includes both modalities, separates hard sessions, and leaves recovery time to reduce overtraining risk."
    )


def knee_safe_plan(profile: dict[str, Any]) -> str:
    return (
        f"Because knee pain is in your context ({profile_summary(profile)}), skip running and jumping for now. "
        "Use low-impact cardio: cycling, swimming, elliptical, rowing if pain-free, or flat walking for 15-30 minutes. "
        "Add support work 2-3x/week: glute bridges 3x12, clamshells 2x15/side, step-ups to a low box 2x8/side if pain-free, "
        "hamstring curls 2x12, and calf raises 2x12. Avoid deep painful squats, plyometrics, and downhill running. "
        "If swelling, locking, instability, or sharp pain persists, get a clinician or physical therapist assessment."
    )


def back_safe_plan(profile: dict[str, Any]) -> str:
    return (
        f"Back-safe 4-week upper-body plan for your profile ({profile_summary(profile)}):\n"
        "Rules: avoid heavy axial loading, heavy deadlifts, back squats, bent-over rows, loaded twisting, and painful ranges.\n"
        "Weeks 1-2, 3 days/week: seated chest press 3x10, lat pulldown 3x10, chest-supported row 3x10, cable face pull 2x15, "
        "seated curls/triceps 2x12, dead bug and bird dog 2x8/side.\n"
        "Weeks 3-4: add 5-10% load only if symptom-free, use 3-4 sets of 8-10 for main supported lifts, keep core anti-rotation/stability work.\n"
        "Use walking, cycling, or swimming for low-impact cardio. Please clear this with your physician or physical therapist given the spine history."
    )


def _has_condition(profile: dict[str, Any], keyword: str) -> bool:
    return any(keyword in condition.lower() for condition in profile.get("health_conditions") or [])
