"""End-to-end smoke test against RUNNING servers, going through the Next.js proxy like a browser.

Prereqs: API (with DEV_LOGIN_ENABLED=true, ENVIRONMENT=local) and web app are running.
Usage:   uv run --project apps/api python scripts/smoke_test.py [WEB_URL]
Default WEB_URL is http://localhost:3000. Uses fake @iiitr.ac.in addresses; run only locally.
"""

from __future__ import annotations

import sys
import uuid

import httpx

WEB = (sys.argv[1] if len(sys.argv) > 1 else "http://localhost:3000").rstrip("/")
ORIGIN = WEB
EMAIL = f"smoke-{uuid.uuid4().hex[:8]}@iiitr.ac.in"
failures: list[str] = []


def check(label: str, condition: bool, detail: str = "") -> None:
    print(f"  [{'PASS' if condition else 'FAIL'}] {label}" + (f"  ({detail})" if detail and not condition else ""))
    if not condition:
        failures.append(label)


def browser() -> httpx.Client:
    return httpx.Client(base_url=WEB, follow_redirects=False, headers={"Origin": ORIGIN}, timeout=30)


print(f"Smoke test against {WEB} as {EMAIL}\n")
c = browser()

print("1. Public pages and the /api proxy")
r = c.get("/")
check("landing page renders", r.status_code == 200 and "Find the people to build it with" in r.text, str(r.status_code))
check("security headers present", r.headers.get("x-content-type-options") == "nosniff" and r.headers.get("x-frame-options") == "DENY")
r = c.get("/api/v1/health/ready")
check("API reachable through the proxy (db ok)", r.status_code == 200 and r.json().get("database") == "ok", r.text[:80])
r = c.get("/login?error=domain_not_allowed")
check("login page shows a specific error", r.status_code == 200 and "pilot list" in r.text)
r = c.get("/login?error=<script>alert(1)</script>")
check("login page never reflects the error param", "<script>alert(1)</script>" not in r.text)

print("2. Not signed in")
check("GET /api/v1/auth/me -> 401", c.get("/api/v1/auth/me").status_code == 401)
for path in ("/me", "/me/edit", "/onboarding"):
    r = c.get(path)
    check(f"{path} redirects to /login", r.status_code in (307, 308) and r.headers["location"].endswith("/login"), f"{r.status_code} {r.headers.get('location')}")

print("3. Google OAuth redirect (through the proxy)")
r = c.get("/api/v1/auth/google/login")
loc = r.headers.get("location", "")
if r.status_code == 303 and loc == f"{WEB}/login?error=not_configured":
    # Fresh clone with no GOOGLE_CLIENT_ID/SECRET: the correct behaviour is to fail safe.
    print("  [NOTE] Google OAuth is not configured on this server; checking fail-safe behaviour only")
    check("unconfigured Google sign-in fails safe with a clear error", True)
    r = c.get("/login?error=not_configured")
    check("login page explains sign-in isn't set up", r.status_code == 200 and "isn&#x27;t set up" in r.text, r.text[:80])
else:
    check("redirects to Google", r.status_code == 302 and loc.startswith("https://accounts.google.com/"), f"{r.status_code} {loc[:60]}")
    check("uses PKCE + state + nonce", all(k in loc for k in ("code_challenge_method=S256", "state=", "nonce=")))
    expected = f"redirect_uri={WEB.replace(':', '%3A').replace('/', '%2F')}%2Fapi%2Fv1%2Fauth%2Fgoogle%2Fcallback"
    check("redirect_uri points at the web origin", expected in loc, loc)
    check("OAuth handshake cookie is set", "bh_oauth" in r.headers.get("set-cookie", ""))
    r = c.get("/api/v1/auth/google/callback?error=access_denied")
    check("cancelled callback redirects back to /login?error=cancelled", r.status_code == 303 and r.headers["location"] == f"{WEB}/login?error=cancelled", r.headers.get("location", ""))

print("4. Allowlist")
r = c.post("/api/v1/auth/dev-login", json={"email": "outsider@gmail.com"})
check("non-allowed domain refused (403)", r.status_code == 403 and r.json() == {"error": "domain_not_allowed"}, r.text)
check("no session cookie issued to outsider", "bh_session" not in c.cookies)

print("5. Sign in -> onboarding -> profile saved")
r = c.post("/api/v1/auth/dev-login", json={"email": EMAIL, "name": "Smoke Tester"})
check("allowed domain signs in", r.status_code == 200 and r.json()["redirect"] == "/onboarding", r.text)
sc = r.headers.get("set-cookie", "").lower()
check("session cookie is HttpOnly + SameSite=Lax", "bh_session=" in sc and "httponly" in sc and "samesite=lax" in sc, sc)
session_cookie = c.cookies.get("bh_session")
r = c.get("/me")
check("/me redirects to /onboarding before onboarding", r.status_code in (307, 308) and r.headers["location"].endswith("/onboarding"), f"{r.status_code} {r.headers.get('location')}")
r = c.get("/onboarding")
check("onboarding page renders for signed-in user", r.status_code == 200 and "Set up your profile" in r.text and "Smoke Tester" in r.text)
r = c.patch("/api/v1/profiles/me", json={"name": "Smoke Tester", "branch": "Mathematics and Computing", "year": 3, "bio": "Testing <b>escaping</b>"})
check("profile PATCH through proxy succeeds (Origin survives proxy)", r.status_code == 200 and r.json()["onboarding_completed"] is True, r.text[:120])
r = c.get("/me")
check("/me renders saved profile", r.status_code == 200 and "Mathematics and Computing" in r.text and "3rd year" in r.text)
check("bio HTML is escaped, not injected", "Testing <b>escaping</b>" not in r.text and "&lt;b&gt;escaping&lt;/b&gt;" in r.text)
check("/onboarding now redirects to /me", c.get("/onboarding").headers.get("location", "").endswith("/me"))
r = c.get("/me/edit")
check("edit page prefilled", r.status_code == 200 and "Edit profile" in r.text)

print("6. Persistence across sessions (\"see it saved after refresh\")")
c2 = browser()
r = c2.post("/api/v1/auth/dev-login", json={"email": EMAIL})
check("second login goes straight to /me", r.json().get("redirect") == "/me", r.text)
r = c2.get("/me")
check("profile still there in a fresh session", r.status_code == 200 and "Mathematics and Computing" in r.text)

print("7. CSRF")
r = c.patch("/api/v1/profiles/me", json={"bio": "hacked"}, headers={"Origin": "https://evil.example"})
check("foreign Origin blocked (403)", r.status_code == 403, str(r.status_code))
check("profile unchanged", "hacked" not in c.get("/me").text)

print("8. Logout revokes server-side")
r = c.post("/api/v1/auth/logout")
check("logout -> 204", r.status_code == 204, str(r.status_code))
c.cookies.clear()
check("/me redirects to /login after logout", c.get("/me").headers.get("location", "").endswith("/login"))
replay = browser()
replay.cookies.set("bh_session", session_cookie)
check("OLD cookie value no longer works (revoked in DB)", replay.get("/api/v1/auth/me").status_code == 401)
check("other device's session unaffected", c2.get("/api/v1/auth/me").status_code == 200)

print()
if failures:
    print(f"FAILED {len(failures)} check(s): {failures}")
    sys.exit(1)
print("ALL SMOKE CHECKS PASSED")
