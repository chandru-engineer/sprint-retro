from tests.helpers import auth_headers as _auth
from tests.helpers import login as _login
from tests.helpers import request_and_capture_otp


def _signup_and_capture_otp(client, monkeypatch, *, org_name, name, email):
    captured = {}

    def fake_send_otp_email(to_email, user_name, code):
        captured["code"] = code
        return True

    monkeypatch.setattr("app.services.auth_service.send_otp_email", fake_send_otp_email)

    resp = client.post("/api/auth/signup", json={"org_name": org_name, "name": name, "email": email})
    assert resp.status_code == 201, resp.text
    assert resp.json()["email"] == email
    assert "code" in captured, "signup did not attempt to send an OTP"
    return captured["code"]


def test_signup_otp_verify_and_login(client, monkeypatch):
    code = _signup_and_capture_otp(
        client, monkeypatch, org_name="Initech", name="Peter Gibbons", email="peter@initech.example"
    )

    # Cannot log in before signup exists at all... but after signup, requesting
    # a login code always works (there's no separate "verified" gate anymore —
    # the OTP itself *is* the verification, every time).
    unknown = client.post("/api/auth/login", json={"email": "nobody@initech.example"})
    assert unknown.status_code == 404

    # Wrong code is rejected without consuming the real one.
    wrong = client.post("/api/auth/verify-otp", json={"email": "peter@initech.example", "code": "000000"})
    assert wrong.status_code == 400

    # Correct code verifies and logs in as the new org's Admin.
    verify_resp = client.post("/api/auth/verify-otp", json={"email": "peter@initech.example", "code": code})
    assert verify_resp.status_code == 200, verify_resp.text
    body = verify_resp.json()
    assert body["requires_org_selection"] is False
    assert body["user"]["role"] == "admin"
    assert body["access_token"]

    # That code is now consumed — reusing it fails.
    replay = client.post("/api/auth/verify-otp", json={"email": "peter@initech.example", "code": code})
    assert replay.status_code == 400

    # A brand new login (new code, new verify) works the same way every time.
    token = _login(client, "peter@initech.example", monkeypatch)
    me = client.get("/api/auth/me", headers=_auth(token))
    assert me.status_code == 200
    assert me.json()["email"] == "peter@initech.example"


def test_signup_rejects_duplicate_email(client, monkeypatch):
    _signup_and_capture_otp(client, monkeypatch, org_name="Initech", name="Peter", email="dup@initech.example")
    dup = client.post(
        "/api/auth/signup",
        json={"org_name": "Another Co", "name": "Someone Else", "email": "dup@initech.example"},
    )
    assert dup.status_code == 400


def test_user_already_in_one_org_can_be_added_to_another_and_login_picks_org(client, monkeypatch):
    # Org 1: signup + verify Peter as Admin of Initech.
    code1 = _signup_and_capture_otp(
        client, monkeypatch, org_name="Initech", name="Peter Gibbons", email="peter@multiorg.example"
    )
    client.post("/api/auth/verify-otp", json={"email": "peter@multiorg.example", "code": code1})

    # Org 2: a totally separate organization, separate admin.
    code2 = _signup_and_capture_otp(
        client, monkeypatch, org_name="Globex", name="Hank Scorpio", email="hank@multiorg.example"
    )
    globex_verify = client.post("/api/auth/verify-otp", json={"email": "hank@multiorg.example", "code": code2})
    globex_admin_token = globex_verify.json()["access_token"]

    # Globex's admin adds Peter (already a member/admin elsewhere) to Globex as a Member.
    # Peter already has a global account — this is the "already part of
    # another org" attach path, no new account created.
    attach_resp = client.post(
        "/api/users",
        json={"name": "Peter Gibbons", "email": "peter@multiorg.example", "role": "member"},
        headers=_auth(globex_admin_token),
    )
    assert attach_resp.status_code == 201, attach_resp.text

    # Peter now belongs to two orgs — logging in (after OTP) returns an org
    # choice, not a token straight away. This is the switch-organization flow.
    peter_code = request_and_capture_otp(client, monkeypatch, "peter@multiorg.example")
    login_resp = client.post("/api/auth/verify-otp", json={"email": "peter@multiorg.example", "code": peter_code})
    assert login_resp.status_code == 200
    login_body = login_resp.json()
    assert login_body["requires_org_selection"] is True
    assert login_body["access_token"] is None
    org_names = {o["name"] for o in login_body["orgs"]}
    assert org_names == {"Initech", "Globex"}
    pending_token = login_body["pending_token"]

    globex_org_id = next(o["id"] for o in login_body["orgs"] if o["name"] == "Globex")

    # A pending token cannot be used as a normal auth token.
    blocked = client.get("/api/auth/me", headers=_auth(pending_token))
    assert blocked.status_code == 401

    # Selecting Globex issues a real token scoped to that org, with the role
    # granted there (member), independent of his Admin role at Initech.
    select_resp = client.post(
        "/api/auth/select-org", json={"org_id": globex_org_id}, headers=_auth(pending_token)
    )
    assert select_resp.status_code == 200, select_resp.text
    select_body = select_resp.json()
    assert select_body["user"]["role"] == "member"

    globex_scoped_token = select_body["access_token"]

    # Confirm data isolation: Peter as a Globex member cannot see Initech's users.
    users_resp = client.get("/api/users", headers=_auth(globex_scoped_token))
    assert users_resp.status_code == 403  # member, not admin, at Globex

    # And switching orgs in-app (no re-login) lands him back at Initech as Admin.
    my_orgs = client.get("/api/auth/my-orgs", headers=_auth(globex_scoped_token))
    assert my_orgs.status_code == 200
    initech_org_id = next(o["id"] for o in my_orgs.json() if o["name"] == "Initech")

    switch_resp = client.post(
        "/api/auth/switch-org", json={"org_id": initech_org_id}, headers=_auth(globex_scoped_token)
    )
    assert switch_resp.status_code == 200
    assert switch_resp.json()["user"]["role"] == "admin"
