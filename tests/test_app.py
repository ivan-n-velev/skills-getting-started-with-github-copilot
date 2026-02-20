from copy import deepcopy

from fastapi.testclient import TestClient

from src.app import app, activities


client = TestClient(app)


def reset_activities_state(func):
    def wrapper(*args, **kwargs):
        original = deepcopy(activities)
        try:
            return func(*args, **kwargs)
        finally:
            activities.clear()
            activities.update(original)

    return wrapper


@reset_activities_state
def test_root_redirects_to_static_index():
    response = client.get("/", follow_redirects=False)
    assert response.status_code in (302, 307)
    assert response.headers.get("location") == "/static/index.html"


@reset_activities_state
def test_get_activities_returns_initial_data():
    response = client.get("/activities")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, dict)
    # Ensure we have at least a couple of known activities
    assert "Basketball Team" in data
    assert "Soccer Club" in data


@reset_activities_state
def test_signup_for_activity_success():
    activity_name = "Basketball Team"
    email = "new.student@mergington.edu"

    response = client.post(f"/activities/{activity_name}/signup", params={"email": email})

    assert response.status_code == 200
    body = response.json()
    assert email in activities[activity_name]["participants"]
    assert "Signed up" in body.get("message", "")


@reset_activities_state
def test_signup_for_activity_duplicate_rejected():
    activity_name = "Basketball Team"
    email = activities[activity_name]["participants"][0]

    response = client.post(f"/activities/{activity_name}/signup", params={"email": email})

    assert response.status_code == 400
    body = response.json()
    assert body.get("detail") == "Student already signed up for this activity"


@reset_activities_state
def test_signup_for_missing_activity_returns_404():
    response = client.post("/activities/Unknown Activity/signup", params={"email": "test@mergington.edu"})
    assert response.status_code == 404
    body = response.json()
    assert body.get("detail") == "Activity not found"


@reset_activities_state
def test_unregister_participant_success():
    activity_name = "Basketball Team"
    # Use an existing participant from the initial data
    email = activities[activity_name]["participants"][0]

    response = client.delete(f"/activities/{activity_name}/participants/{email}")

    assert response.status_code == 200
    body = response.json()
    assert email not in activities[activity_name]["participants"]
    assert "Removed" in body.get("message", "")


@reset_activities_state
def test_unregister_nonexistent_participant_returns_404():
    activity_name = "Basketball Team"
    email = "not.registered@mergington.edu"

    response = client.delete(f"/activities/{activity_name}/participants/{email}")

    assert response.status_code == 404
    body = response.json()
    assert body.get("detail") == "Participant not found for this activity"


@reset_activities_state
def test_unregister_from_missing_activity_returns_404():
    response = client.delete("/activities/Unknown Activity/participants/test@mergington.edu")
    assert response.status_code == 404
    body = response.json()
    assert body.get("detail") == "Activity not found"
