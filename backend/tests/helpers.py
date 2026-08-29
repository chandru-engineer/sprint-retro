from app.models.email_otp import EmailOtp
from app.models.org_membership import OrgMembership
from app.models.organization import Organization
from app.models.user import User, UserRole


def seed_admin_with_org(db_session, org_name="Acme Corp", email="admin@acme-corp.com", name="Admin"):
    """Seeds a fresh org with an Admin — the entry point every test workflow
    starts from, mirroring what `/api/auth/signup` + OTP verify would have
    produced. There's no password; tests log in via `login()` below."""
    org = Organization(name=org_name)
    db_session.add(org)
    db_session.flush()

    admin = User(name=name, email=email, is_active=True)
    db_session.add(admin)
    db_session.flush()

    db_session.add(OrgMembership(org_id=org.id, user_id=admin.id, role=UserRole.ADMIN, is_active=True))
    db_session.commit()
    db_session.refresh(admin)
    db_session.refresh(org)
    return admin, org


def login(client, email, monkeypatch):
    """Logs in via the OTP flow: request a code, capture it (by reading the
    stored hash's plaintext isn't possible, so we intercept the send call),
    then verify. Requires a `monkeypatch` fixture. Returns the access token —
    asserts the account belongs to exactly one active org, matching most
    test setups; for multi-org tests, use `request_and_capture_otp` +
    `/api/auth/verify-otp` + `/api/auth/select-org` directly instead."""
    code = request_and_capture_otp(client, monkeypatch, email)
    resp = client.post("/api/auth/verify-otp", json={"email": email, "code": code})
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert not body["requires_org_selection"], "login() helper expects a single-org login; use verify-otp directly for multi-org cases"
    return body["access_token"]


def request_and_capture_otp(client, monkeypatch, email):
    """Triggers a login-code send (via /api/auth/login) and returns the
    plaintext code, captured by monkeypatching the outbound email call."""
    captured = {}

    def fake_send_otp_email(to_email, user_name, code):
        captured["code"] = code
        return True

    monkeypatch.setattr("app.services.auth_service.send_otp_email", fake_send_otp_email)

    resp = client.post("/api/auth/login", json={"email": email})
    assert resp.status_code == 200, resp.text
    assert "code" in captured, "login did not attempt to send an OTP"
    return captured["code"]


def auth_headers(token):
    return {"Authorization": f"Bearer {token}"}
