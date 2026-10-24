from app.core.security import create_access_token


def test_register_login_me_logout(make_client):
    c = make_client()
    r = c.post("/api/v1/auth/register", json={"email": "A@Example.com", "password": "longenough1", "display_name": "A"})
    assert r.status_code == 201 and r.json()["email"] == "a@example.com"
    assert "password" not in r.text
    assert c.get("/api/v1/auth/me").json()["display_name"] == "A"
    assert c.post("/api/v1/auth/logout").status_code == 204
    c.cookies.clear()
    assert c.get("/api/v1/auth/me").status_code == 401
    r = c.post("/api/v1/auth/login", json={"email": "a@example.com", "password": "longenough1"})
    assert r.status_code == 200
    assert c.get("/api/v1/auth/me").status_code == 200


def test_duplicate_email_and_weak_password(client, make_client):
    c = make_client()
    assert c.post("/api/v1/auth/register", json={"email": "owner@example.com", "password": "longenough1"}).status_code == 409
    r = c.post("/api/v1/auth/register", json={"email": "x@example.com", "password": "short"})
    assert r.status_code == 422 and r.json()["error"]["code"] == "validation_error"


def test_login_failures_are_generic(client, make_client):
    c = make_client()
    wrong = c.post("/api/v1/auth/login", json={"email": "owner@example.com", "password": "nope-nope-nope"})
    ghost = c.post("/api/v1/auth/login", json={"email": "ghost@example.com", "password": "nope-nope-nope"})
    assert wrong.status_code == ghost.status_code == 401
    assert wrong.json()["error"]["message"] == ghost.json()["error"]["message"]


def test_protected_routes_require_auth_and_reject_bad_tokens(make_client):
    c = make_client()
    for path in ("/auth/me", "/brands", "/products", "/campaigns", "/analytics/overview", "/meta"):
        assert c.get(f"/api/v1{path}").status_code == 401, path
    c.cookies.set("adcraft_token", "garbage")
    assert c.get("/api/v1/auth/me").status_code == 401
    c.cookies.set("adcraft_token", create_access_token("not-a-uuid"))
    assert c.get("/api/v1/auth/me").status_code == 401


def test_password_is_hashed_not_stored(client, db):
    from app.models import User
    u = db.query(User).one()
    assert u.password_hash.startswith("$argon2") and "correct-horse-1" not in u.password_hash


def test_foreign_origin_blocked_on_unsafe_methods(client):
    r = client.post("/api/v1/brands", json={"name": "X"}, headers={"Origin": "https://evil.example"})
    assert r.status_code == 403 and r.json()["error"]["code"] == "bad_origin"
    ok = client.post("/api/v1/brands", json={"name": "X"}, headers={"Origin": "http://localhost:5173"})
    assert ok.status_code == 201


def test_change_password(client):
    assert client.post("/api/v1/auth/change-password",
                       json={"current_password": "wrong-wrong", "new_password": "brand-new-pass"}).status_code == 400
    assert client.post("/api/v1/auth/change-password",
                       json={"current_password": "correct-horse-1", "new_password": "brand-new-pass"}).status_code == 204
    client.cookies.clear()
    assert client.post("/api/v1/auth/login", json={"email": "owner@example.com", "password": "brand-new-pass"}).status_code == 200
