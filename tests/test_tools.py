from tools.nutrition import calorie_recommendation, hydration_range, protein_range
from tools.profile import extract_profile_updates, missing_profile_fields
from tools.progress import build_progress_summary
from tools.safety import evaluate_safety
from tools.workouts import workout_recommendation
from agent.router import categorize_question


def sample_profile():
    return {
        "age": 28,
        "sex": "male",
        "height_cm": 180,
        "weight_kg": 81.6,
        "activity_level": "moderately active",
        "health_conditions": [],
        "dietary_restrictions": [],
        "fitness_goals": ["build muscle"],
        "fitness_level": "intermediate",
        "current_steps": 6000,
    }


def test_router_categories():
    assert categorize_question("Can you make me a meal plan?") == "meal"
    assert categorize_question("What workout should I do?") == "workout"
    assert categorize_question("Am I on track with progress?") == "progress"
    assert categorize_question("What stock should I buy?") == "out_of_scope"


def test_profile_extraction_and_missing_fields():
    updates = extract_profile_updates("I'm a 28-year-old male, 180 lbs, 5'11\", moderately active and allergic to shellfish.")
    assert updates["age"] == 28
    assert updates["sex"] == "male"
    assert 81 <= updates["weight_kg"] <= 82
    assert updates["height_cm"] == 180.3
    assert "shellfish allergy" in updates["dietary_restrictions"]
    assert "height_cm" in missing_profile_fields({"age": 30})


def test_nutrition_targets_are_personalized():
    profile = sample_profile()
    assert protein_range(profile, muscle_gain=True) == (131, 180)
    assert hydration_range(profile) == (98, 114)
    response = calorie_recommendation(profile)
    assert "BMR" in response
    assert "TDEE" in response
    assert "81.6 kg" in response


def test_safety_refuses_extreme_weight_loss():
    result = evaluate_safety("I want to lose 15 pounds in two weeks. Give me an extreme plan.", sample_profile())
    assert result.flagged is True
    assert "unsafe_rapid_weight_loss" in result.reasons
    assert "can't help create" in result.response


def test_workout_respects_injury_context():
    profile = sample_profile()
    profile["health_conditions"] = ["mild L4-L5 disc herniation"]
    response = workout_recommendation("Create a 4-week plan without stressing my back", profile)
    assert "avoid heavy axial loading" in response.lower()
    assert "physician or physical therapist" in response.lower()


def test_progress_summary_weight_change():
    summary = build_progress_summary(
        {
            "snapshots": [
                {"profile": {"weight_kg": 90, "activity_level": "sedentary"}},
                {"profile": {"weight_kg": 87, "activity_level": "lightly active"}},
            ],
            "events": [],
        }
    )
    assert summary["weight_change_kg"] == -3
    assert summary["activity_change"] == {"from": "sedentary", "to": "lightly active"}
