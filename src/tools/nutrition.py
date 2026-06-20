"""Nutrition and meal-planning tools grounded in user biometrics."""

from __future__ import annotations

from typing import Any

from tools.profile import profile_summary


ACTIVITY_MULTIPLIERS = {
    "sedentary": 1.2,
    "lightly active": 1.375,
    "moderately active": 1.55,
    "very active": 1.725,
}


def estimate_energy(profile: dict[str, Any]) -> dict[str, float] | None:
    age = profile.get("age")
    sex = (profile.get("sex") or "").lower()
    height = profile.get("height_cm")
    weight = profile.get("weight_kg")
    if not all([age, sex, height, weight]):
        return None
    sex_adjustment = 5 if sex.startswith("m") else -161
    bmr = 10 * float(weight) + 6.25 * float(height) - 5 * int(age) + sex_adjustment
    activity = (profile.get("activity_level") or "sedentary").lower()
    multiplier = ACTIVITY_MULTIPLIERS.get(activity, 1.375)
    tdee = bmr * multiplier
    return {
        "bmr": round(bmr),
        "tdee": round(tdee),
        "weight_loss_target": round(max(1200 if sex.startswith("f") else 1500, tdee - 500)),
        "safe_deficit_low": round(tdee - 300),
        "safe_deficit_high": round(max(1200 if sex.startswith("f") else 1500, tdee - 750)),
    }


def protein_range(profile: dict[str, Any], muscle_gain: bool = False) -> tuple[int, int] | None:
    weight = profile.get("weight_kg")
    if not weight:
        return None
    low, high = (1.6, 2.2) if muscle_gain else (1.2, 1.6)
    return round(float(weight) * low), round(float(weight) * high)


def hydration_range(profile: dict[str, Any]) -> tuple[int, int] | None:
    weight = profile.get("weight_kg")
    if not weight:
        return None
    base_oz = float(weight) * 2.20462 * 0.5
    activity = (profile.get("activity_level") or "").lower()
    add = 16 if "moderate" in activity or "very" in activity else 8
    return round(base_oz + add - 8), round(base_oz + add + 8)


def meal_recommendation(message: str, profile: dict[str, Any]) -> str:
    text = message.lower()
    if "protein" in text:
        return protein_recommendation(profile)
    if "water" in text or "hydration" in text:
        return hydration_recommendation(profile)
    if "7-day" in text or "weekly" in text or "week" in text:
        return seven_day_plan(profile)
    if "calorie" in text or "calories" in text:
        return calorie_recommendation(profile)
    return one_day_meal_plan(profile)


def calorie_recommendation(profile: dict[str, Any]) -> str:
    energy = estimate_energy(profile)
    if not energy:
        return (
            f"Using your current profile ({profile_summary(profile)}), I still need age, sex, height, weight, "
            "and activity level to calculate a precise TDEE. A safe starting point for weight loss is usually a "
            "300-750 calorie/day deficit, without dropping below medically safe minimums unless supervised."
        )
    protein = protein_range(profile)
    protein_text = f" Aim for about {protein[0]}-{protein[1]} g protein/day to preserve lean mass." if protein else ""
    return (
        f"Based on your profile ({profile_summary(profile)}), your estimated BMR is about {energy['bmr']} kcal/day "
        f"and your TDEE is about {energy['tdee']} kcal/day. For safe weight loss, use a 300-750 kcal deficit: "
        f"roughly {energy['safe_deficit_high']}-{energy['safe_deficit_low']} kcal/day, with a practical starting "
        f"target near {energy['weight_loss_target']} kcal/day. This supports gradual fat loss while avoiding crash "
        f"dieting.{protein_text}"
    )


def protein_recommendation(profile: dict[str, Any]) -> str:
    muscle_goal = any("muscle" in goal.lower() or "strength" in goal.lower() for goal in profile.get("fitness_goals") or [])
    protein = protein_range(profile, muscle_gain=muscle_goal)
    if not protein:
        return "I need your body weight to calculate a personalized protein target. For muscle gain, ACSM guidance commonly uses 1.6-2.2 g/kg/day."
    per_kg = "1.6-2.2 g/kg/day" if muscle_goal else "1.2-1.6 g/kg/day"
    return (
        f"Using your weight of {profile['weight_kg']:.1f} kg and your goals ({', '.join(profile.get('fitness_goals') or ['general fitness'])}), "
        f"a grounded protein target is {protein[0]}-{protein[1]} g/day ({per_kg}). Split that across 3-5 meals, "
        "for example 25-40 g per meal from Greek yogurt, eggs, tofu, poultry, fish, beans, or lean meat."
    )


def hydration_recommendation(profile: dict[str, Any]) -> str:
    water = hydration_range(profile)
    if not water:
        return "I need your body weight to personalize hydration. A common starting point is about half your body weight in ounces, adjusted for sweat, climate, and activity."
    return (
        f"Based on your {profile['weight_kg']:.1f} kg body weight and {profile.get('activity_level') or 'current'} activity level, "
        f"aim for about {water[0]}-{water[1]} oz water/day ({water[0] * 0.0296:.1f}-{water[1] * 0.0296:.1f} L). "
        "Spread it through the day and use urine color, sweat rate, heat, and workout duration to adjust. Avoid forcing excessive water intake."
    )


def one_day_meal_plan(profile: dict[str, Any]) -> str:
    energy = estimate_energy(profile)
    target = energy["weight_loss_target"] if energy and _has_goal(profile, "loss") else energy["tdee"] if energy else 2200
    restrictions = _restriction_text(profile)
    protein = protein_range(profile, muscle_gain=_has_goal(profile, "muscle") or _has_goal(profile, "strength"))
    protein_text = f" and {protein[0]}-{protein[1]} g protein" if protein else ""
    return (
        f"Here is a one-day plan tailored to your profile ({profile_summary(profile)}). Target about {target} kcal{protein_text}. {restrictions}\n\n"
        "Breakfast: Greek yogurt or tofu yogurt bowl with oats, berries, and chia seeds.\n"
        "Lunch: Grilled chicken, tofu, or beans over quinoa/brown rice with spinach, peppers, olive oil, and lemon.\n"
        "Snack: Cottage cheese or hummus with fruit/vegetables and whole-grain crackers.\n"
        "Dinner: Salmon, lentils, or tempeh with sweet potato, broccoli, and a side salad.\n\n"
        "This balances protein, high-fiber carbohydrates, healthy fats, and vegetables without extreme restriction."
    )


def seven_day_plan(profile: dict[str, Any]) -> str:
    energy = estimate_energy(profile)
    target = energy["weight_loss_target"] if energy else 1700
    restrictions = _restriction_text(profile)
    days = [
        ("Greek yogurt oats; chicken quinoa salad; apple with seed butter; salmon, rice, broccoli"),
        ("Egg or tofu scramble; turkey or hummus wrap; cottage cheese; bean chili with salad"),
        ("Protein smoothie; tuna/tofu bowl; carrots with hummus; chicken or tempeh stir-fry"),
        ("Overnight oats; lentil soup; fruit and yogurt; cod/tofu, potatoes, asparagus"),
        ("Avocado toast with eggs/beans; chicken salad; roasted chickpeas; turkey/tofu tacos"),
        ("Cottage cheese bowl; quinoa veggie bowl; smoothie; salmon/lentils with vegetables"),
        ("Oatmeal with berries; burrito bowl; fruit; sheet-pan chicken/tofu with sweet potato"),
    ]
    lines = [f"Day {i + 1}: {meal}" for i, meal in enumerate(days)]
    return (
        f"Here is a 7-day plan around ~{target} kcal/day for your profile ({profile_summary(profile)}). {restrictions} "
        "Adjust portions up or down based on hunger, training, and weekly progress.\n\n"
        + "\n".join(lines)
        + "\n\nEach day includes protein, fiber-rich carbs, vegetables, and healthy fats. Avoid skipping meals or using starvation-level calories."
    )


def _restriction_text(profile: dict[str, Any]) -> str:
    restrictions = [r.lower() for r in profile.get("dietary_restrictions") or []]
    if not restrictions:
        return "No dietary restrictions are currently recorded."
    avoid = ", ".join(restrictions)
    shellfish_note = " Use fish like salmon/cod only if tolerated; avoid shrimp, crab, lobster, and cross-contact." if "shellfish allergy" in restrictions else ""
    nut_note = " Avoid tree nuts and check labels for hidden nuts or cross-contact." if any("nut" in r for r in restrictions) else ""
    return f"Dietary restrictions recorded: {avoid}.{shellfish_note}{nut_note}"


def _has_goal(profile: dict[str, Any], keyword: str) -> bool:
    return any(keyword in goal.lower() for goal in profile.get("fitness_goals") or [])
