from pathlib import Path

from fastapi.testclient import TestClient

from agent.service import FitAgentService
from api.app import create_app
from memory.sqlite_store import SQLiteStore


def client(tmp_path: Path) -> TestClient:
    store = SQLiteStore(f"sqlite:///{tmp_path / 'test.sqlite3'}")
    return TestClient(create_app(FitAgentService(store)))


def profile_payload():
    return {
        "age": 34,
        "sex": "female",
        "height_cm": 165,
        "weight_kg": 79.4,
        "activity_level": "lightly active",
        "health_conditions": [],
        "dietary_restrictions": [],
        "fitness_goals": ["weight loss"],
        "fitness_level": "beginner",
        "current_steps": 4000,
    }


def create_profile(api: TestClient) -> str:
    response = api.post("/api/profiles", json=profile_payload())
    assert response.status_code == 200
    return response.json()["session_id"]


def test_meal_recommendation_flow(tmp_path):
    api = client(tmp_path)
    session_id = create_profile(api)
    response = api.post("/api/chat", json={"session_id": session_id, "message": "Can you create a one-day meal plan?"})
    body = response.json()
    assert response.status_code == 200
    assert body["category"] == "meal"
    assert "79.4 kg" in body["response"]
    assert "Breakfast" in body["response"]


def test_workout_plan_flow(tmp_path):
    api = client(tmp_path)
    session_id = create_profile(api)
    response = api.post("/api/chat", json={"session_id": session_id, "message": "What workout should I do today as a beginner?"})
    body = response.json()
    assert response.status_code == 200
    assert body["category"] == "workout"
    assert "beginner full-body" in body["response"].lower()


def test_safety_flagged_flow(tmp_path):
    api = client(tmp_path)
    session_id = create_profile(api)
    response = api.post(
        "/api/chat",
        json={"session_id": session_id, "message": "I want to lose 15 pounds in two weeks. What extreme plan can I follow?"},
    )
    body = response.json()
    assert response.status_code == 200
    assert body["category"] == "safety"
    assert "unsafe_rapid_weight_loss" in body["safety_flags"]
    assert "can't help" in body["response"]


def test_out_of_scope_flow(tmp_path):
    api = client(tmp_path)
    session_id = create_profile(api)
    response = api.post("/api/chat", json={"session_id": session_id, "message": "What stock should I buy?"})
    body = response.json()
    assert response.status_code == 200
    assert body["category"] == "out_of_scope"
    assert "out-of-scope" in body["response"]


def test_history_and_progress_flow(tmp_path):
    api = client(tmp_path)
    session_id = create_profile(api)
    api.post("/api/profiles", json={**profile_payload(), "session_id": session_id, "weight_kg": 77.9})
    api.post("/api/chat", json={"session_id": session_id, "message": "Am I on track with my progress?"})

    history = api.get(f"/api/conversations/{session_id}").json()
    progress = api.get(f"/api/progress/{session_id}").json()

    assert len(history["messages"]) == 2
    assert progress["summary"]["weight_change_kg"] == -1.5
