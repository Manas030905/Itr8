"""Skills catalogue and per-user skill management."""

from tests.conftest import claims


def test_skill_catalogue_is_seeded(client):
    response = client.get("/api/v1/skills")
    assert response.status_code == 200
    skills = response.json()
    assert len(skills) >= 20
    assert {s["slug"] for s in skills} >= {"python", "react", "machine-learning"}


def test_user_can_replace_their_skills(signed_in):
    catalogue = signed_in.get("/api/v1/skills").json()
    python = next(s for s in catalogue if s["slug"] == "python")
    react = next(s for s in catalogue if s["slug"] == "react")

    response = signed_in.put(
        "/api/v1/skills/me",
        json={
            "skills": [
                {"skill_id": python["id"], "level": "advanced"},
                {"skill_id": react["id"], "level": "intermediate"},
            ]
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert {(x["skill"]["slug"], x["level"]) for x in body} == {
        ("python", "advanced"),
        ("react", "intermediate"),
    }

    again = signed_in.get("/api/v1/skills/me")
    assert again.status_code == 200
    assert {(x["skill"]["slug"], x["level"]) for x in again.json()} == {
        ("python", "advanced"),
        ("react", "intermediate"),
    }


def test_user_can_clear_their_skills(signed_in):
    catalogue = signed_in.get("/api/v1/skills").json()
    python = next(s for s in catalogue if s["slug"] == "python")
    signed_in.put(
        "/api/v1/skills/me",
        json={"skills": [{"skill_id": python["id"], "level": "beginner"}]},
    )
    response = signed_in.put("/api/v1/skills/me", json={"skills": []})
    assert response.status_code == 200
    assert response.json() == []


def test_invalid_skill_id_is_rejected(signed_in):
    response = signed_in.put(
        "/api/v1/skills/me",
        json={"skills": [{"skill_id": "00000000-0000-0000-0000-000000000000", "level": "beginner"}]},
    )
    assert response.status_code == 422


def test_duplicate_skill_is_rejected(signed_in):
    catalogue = signed_in.get("/api/v1/skills").json()
    python = next(s for s in catalogue if s["slug"] == "python")
    response = signed_in.put(
        "/api/v1/skills/me",
        json={
            "skills": [
                {"skill_id": python["id"], "level": "beginner"},
                {"skill_id": python["id"], "level": "advanced"},
            ]
        },
    )
    assert response.status_code == 422


def test_skills_are_private_to_the_authenticated_user(make_client, google_sign_in):
    first = make_client()
    second = make_client()
    google_sign_in(first, claims())
    google_sign_in(second, claims(email="bala@iiitr.ac.in", sub="google-sub-2"))

    catalogue = first.get("/api/v1/skills").json()
    python = next(s for s in catalogue if s["slug"] == "python")
    first.put(
        "/api/v1/skills/me",
        json={"skills": [{"skill_id": python["id"], "level": "advanced"}]},
    )

    assert first.get("/api/v1/skills/me").json()[0]["level"] == "advanced"
    assert second.get("/api/v1/skills/me").json() == []
