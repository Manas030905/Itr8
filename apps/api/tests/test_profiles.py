"""Profile update: validation, onboarding completion, and authorization."""

import pytest

from tests.conftest import claims


def _patch(c, **body):
    return c.patch("/api/v1/profiles/me", json=body)


def test_partial_update_does_not_complete_onboarding(signed_in):
    r = _patch(signed_in, branch="CSE")
    assert r.status_code == 200
    assert r.json()["profile"]["branch"] == "CSE"
    assert r.json()["onboarding_completed"] is False


def test_completing_name_branch_year_completes_onboarding_and_persists(
    signed_in, make_client, google_sign_in
):
    r = _patch(signed_in, name="Asha R", branch="AI & Data Science", year=3, bio="I build things.")
    assert r.status_code == 200
    body = r.json()
    assert body["onboarding_completed"] is True
    assert body["profile"]["onboarding_completed_at"] is not None
    assert body["name"] == "Asha R"

    # "Saved": visible from a brand-new session (fresh cookie jar, new login).
    fresh = make_client()
    google_sign_in(fresh, claims())
    again = fresh.get("/api/v1/profiles/me").json()
    assert again["name"] == "Asha R"
    assert again["profile"]["year"] == 3 and again["profile"]["bio"] == "I build things."
    assert again["onboarding_completed"] is True


def test_completion_timestamp_is_not_rewritten_on_later_edits(signed_in):
    first = _patch(signed_in, branch="CSE", year=2).json()["profile"]["onboarding_completed_at"]
    second = _patch(signed_in, bio="updated").json()["profile"]["onboarding_completed_at"]
    assert first == second


@pytest.mark.parametrize(
    "body",
    [
        {"year": 0},
        {"year": 7},
        {"year": "second"},
        {"bio": "x" * 501},
        {"name": ""},
        {"name": "   "},
        {"name": None},
        {"branch": None},
        {"year": None},
        {"name": "n" * 101},
        {"branch": "b" * 81},
    ],
)
def test_invalid_updates_are_rejected(signed_in, body):
    assert _patch(signed_in, **body).status_code == 422


@pytest.mark.parametrize(
    "field",
    [
        "role",
        "email",
        "id",
        "college_id",
        "onboarding_completed_at",
        "onboarding_completed",
        "user_id",
    ],
)
def test_clients_cannot_set_server_controlled_fields(signed_in, field):
    """Mass-assignment guard: unknown fields are rejected, not silently applied."""
    assert _patch(signed_in, **{field: "admin"}).status_code == 422
    me = signed_in.get("/api/v1/auth/me").json()
    assert me["role"] == "student" and me["onboarding_completed"] is False


def test_text_is_cleaned(signed_in):
    r = _patch(
        signed_in, name="  Asha \n\t Rao\x00 ", branch="CSE\x07", bio="  line1\r\nline2\x00  "
    ).json()
    assert r["name"] == "Asha Rao"
    assert r["profile"]["branch"] == "CSE"
    assert r["profile"]["bio"] == "line1\nline2"


def test_bio_can_be_cleared(signed_in):
    _patch(signed_in, bio="hello")
    assert _patch(signed_in, bio=None).json()["profile"]["bio"] is None
    _patch(signed_in, bio="again")
    assert _patch(signed_in, bio="   ").json()["profile"]["bio"] is None


def test_html_is_stored_verbatim_and_escaped_by_the_ui(signed_in):
    """The API stores text as-is; React escapes on render. Just make sure nothing breaks."""
    bio = "<script>alert(1)</script>"
    assert _patch(signed_in, bio=bio).json()["profile"]["bio"] == bio


def test_users_can_only_modify_their_own_profile(signed_in, make_client, google_sign_in):
    other = make_client()
    google_sign_in(other, claims(email="bala@iiitr.ac.in", sub="google-sub-2"))
    _patch(signed_in, name="Asha", branch="CSE", year=1)

    r = _patch(other, name="Bala", branch="MnC", year=4)
    assert r.status_code == 200

    a = signed_in.get("/api/v1/profiles/me").json()
    b = other.get("/api/v1/profiles/me").json()
    assert (a["email"], a["name"], a["profile"]["branch"], a["profile"]["year"]) == (
        "asha@iiitr.ac.in",
        "Asha",
        "CSE",
        1,
    )
    assert (b["email"], b["name"], b["profile"]["branch"], b["profile"]["year"]) == (
        "bala@iiitr.ac.in",
        "Bala",
        "MnC",
        4,
    )
    # There is no endpoint that takes another user's id at all.
    assert signed_in.patch(f"/api/v1/profiles/{b['id']}", json={"name": "hacked"}).status_code in (
        404,
        405,
    )
