from tests.helpers import auth_headers as _auth
from tests.helpers import login as _login
from tests.helpers import seed_admin_with_org


def test_new_account_invite_email_has_no_password(client, db_session, monkeypatch):
    admin, org = seed_admin_with_org(db_session)
    admin_token = _login(client, admin.email, monkeypatch)

    captured = {}

    def fake_send(to_email, user_name, org_name):
        captured.update(to_email=to_email, user_name=user_name, org_name=org_name)
        return True

    monkeypatch.setattr("app.services.user_service.send_new_account_invite_email", fake_send)

    resp = client.post(
        "/api/users",
        json={"name": "New Member", "email": "newmember@acme-corp.com", "role": "member"},
        headers=_auth(admin_token),
    )
    assert resp.status_code == 201, resp.text

    assert captured["to_email"] == "newmember@acme-corp.com"
    assert captured["user_name"] == "New Member"
    assert captured["org_name"] == org.name
    assert "password" not in captured  # there are no passwords anywhere in this app


def test_existing_account_org_invite_email(client, db_session, monkeypatch):
    admin, org = seed_admin_with_org(db_session)
    admin_token = _login(client, admin.email, monkeypatch)

    # First, create the user directly (their "existing account" elsewhere).
    client.post(
        "/api/users",
        json={"name": "Existing Person", "email": "existing@acme-corp.com", "role": "member"},
        headers=_auth(admin_token),
    )

    # A second organization now attaches that same email.
    admin2, org2 = seed_admin_with_org(db_session, org_name="Second Org", email="admin2@second-org.example")
    admin2_token = _login(client, admin2.email, monkeypatch)

    captured = {}

    def fake_send(to_email, user_name, org_name):
        captured.update(to_email=to_email, user_name=user_name, org_name=org_name)
        return True

    monkeypatch.setattr("app.services.user_service.send_existing_account_org_invite_email", fake_send)

    resp = client.post(
        "/api/users",
        json={"name": "Existing Person", "email": "existing@acme-corp.com", "role": "member"},
        headers=_auth(admin2_token),
    )
    assert resp.status_code == 201, resp.text

    assert captured["to_email"] == "existing@acme-corp.com"
    assert captured["org_name"] == org2.name
