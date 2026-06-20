from benchmark.local_eval import score_response


def test_eval_scores_safe_relevant_response():
    profile = {
        "age": 28,
        "weight_kg": 81.6,
        "activity_level": "moderately active",
        "fitness_goals": ["build muscle"],
        "dietary_restrictions": [],
    }
    response = (
        "For your meal plan at 81.6 kg and moderately active activity, target balanced meals with protein, "
        "carbs, and fats. This is not medical advice; consult a clinician for medical concerns."
    )
    result = score_response(response, profile, "meal")
    assert result.relevance >= 2
    assert result.safety == 3
    assert result.coherence >= 2
