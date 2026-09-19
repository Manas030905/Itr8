import pytest

from app.core.security import generate_token, hash_token, safe_next_path


def test_liveness(client):
    r = client.get("/api/v1/health")
    assert r.status_code == 200 and r.json() == {"status": "ok"}


def test_readiness_checks_database(client):
    r = client.get("/api/v1/health/ready")
    assert r.status_code == 200 and r.json()["database"] == "ok"


def test_token_is_random_and_hash_is_sha256_hex():
    a, b = generate_token(), generate_token()
    assert a != b and len(a) >= 43
    assert len(hash_token(a)) == 64 and hash_token(a) != a and hash_token(a) == hash_token(a)


@pytest.mark.parametrize("value", ["/me", "/me/edit", "/onboarding?x=1", "/"])
def test_safe_next_path_allows_relative_paths(value):
    assert safe_next_path(value) == value


@pytest.mark.parametrize(
    "value",
    [
        None,
        "",
        "me",
        "https://evil.com",
        "//evil.com",
        "///evil.com",
        "/\\evil.com",
        "\\\\evil.com",
        "javascript:alert(1)",
        "/ok\r\nSet-Cookie: x=1",
        "/" + "a" * 300,
        "http://localhost:3000/me",
    ],
)
def test_safe_next_path_rejects_open_redirects(value):
    assert safe_next_path(value, default="/fallback") == "/fallback"
