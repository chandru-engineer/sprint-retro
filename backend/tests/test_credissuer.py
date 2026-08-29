import datetime

from tests.helpers import auth_headers as _auth
from tests.helpers import login as _login
from tests.helpers import seed_admin_with_org


def test_credissuer_config_and_one_click_issue(client, db_session, monkeypatch):
    admin, _org = seed_admin_with_org(db_session)
    admin_token = _login(client, admin.email, monkeypatch)

    member = client.post(
        "/api/users",
        json={"name": "Casey Recipient", "email": "casey@acme-corp.com", "role": "member"},
        headers=_auth(admin_token),
    ).json()

    # Not configured yet.
    status_resp = client.get("/api/credissuer/config", headers=_auth(admin_token))
    assert status_resp.status_code == 200
    assert status_resp.json()["configured"] is False

    # Issuing before configuring is rejected.
    early_issue = client.post(
        "/api/credissuer/issue", json={"user_id": member["id"]}, headers=_auth(admin_token)
    )
    assert early_issue.status_code == 400

    # An empty API key is rejected when listing templates.
    empty_key = client.get("/api/credissuer/templates?api_key=", headers=_auth(admin_token))
    assert empty_key.status_code == 400

    templates = client.get("/api/credissuer/templates?api_key=sk_test_123", headers=_auth(admin_token)).json()
    assert len(templates) >= 1
    chosen = templates[0]

    saved = client.put(
        "/api/credissuer/config",
        json={"api_key": "sk_test_123", "template_id": chosen["id"], "template_name": chosen["name"]},
        headers=_auth(admin_token),
    )
    assert saved.status_code == 200, saved.text
    body = saved.json()
    assert body["configured"] is True
    assert body["template_name"] == chosen["name"]
    # The key is masked, never echoed back in full.
    assert "sk_test_123" not in body["api_key_masked"]

    # One-click issue now succeeds.
    issued = client.post(
        "/api/credissuer/issue", json={"user_id": member["id"]}, headers=_auth(admin_token)
    )
    assert issued.status_code == 200, issued.text
    issued_body = issued.json()
    assert issued_body["user_name"] == "Casey Recipient"
    assert issued_body["template_name"] == chosen["name"]
    assert issued_body["vc_id"].startswith("vc_mock_")
    assert issued_body["status"] == "issued"

    # Shows up in the issuance history.
    history = client.get("/api/credissuer/history", headers=_auth(admin_token)).json()
    assert len(history) == 1
    assert history[0]["vc_id"] == issued_body["vc_id"]

    # A non-admin can't configure or issue.
    member_token = _login(client, "casey@acme-corp.com", monkeypatch)
    forbidden_config = client.get("/api/credissuer/config", headers=_auth(member_token))
    assert forbidden_config.status_code == 403
    forbidden_issue = client.post(
        "/api/credissuer/issue", json={"user_id": member["id"]}, headers=_auth(member_token)
    )
    assert forbidden_issue.status_code == 403


def test_credential_issuance_scoped_to_a_retro_is_restricted_to_the_sprint_hero(client, db_session, monkeypatch):
    admin, _org = seed_admin_with_org(db_session)
    admin_token = _login(client, admin.email, monkeypatch)

    hero = client.post(
        "/api/users", json={"name": "Hero Person", "email": "hero@acme-corp.com", "role": "member"},
        headers=_auth(admin_token),
    ).json()
    runner_up = client.post(
        "/api/users", json={"name": "Runner Up", "email": "runnerup@acme-corp.com", "role": "member"},
        headers=_auth(admin_token),
    ).json()
    team = client.post(
        "/api/teams",
        json={"name": "Team", "description": "", "team_lead_id": None, "member_ids": [hero["id"], runner_up["id"]]},
        headers=_auth(admin_token),
    ).json()
    project = client.post(
        "/api/projects", json={"name": "Project", "description": "", "team_id": team["id"], "status": "active"},
        headers=_auth(admin_token),
    ).json()
    today = datetime.date.today()
    retro = client.post(
        "/api/retros",
        json={
            "project_id": project["id"], "team_id": team["id"], "name": "Retro", "sprint_name": "Sprint 1",
            "sprint_start_date": str(today), "sprint_end_date": str(today), "retro_date": str(today),
            "retro_time": "10:00:00", "participant_ids": [hero["id"], runner_up["id"]],
        },
        headers=_auth(admin_token),
    ).json()
    retro_id = retro["id"]
    client.post(f"/api/retros/{retro_id}/invite", headers=_auth(admin_token))

    hero_token = _login(client, "hero@acme-corp.com", monkeypatch)
    runner_up_token = _login(client, "runnerup@acme-corp.com", monkeypatch)

    # Both vote for "Hero Person" — they win 2-0.
    client.put(f"/api/retros/{retro_id}/hero-vote", json={"candidate_id": hero["id"]}, headers=_auth(hero_token))
    client.put(
        f"/api/retros/{retro_id}/hero-vote", json={"candidate_id": hero["id"]}, headers=_auth(runner_up_token)
    )

    client.put(
        "/api/credissuer/config",
        json={"api_key": "sk_test_hero", "template_id": "tpl_sprint_hero", "template_name": "Sprint Hero Award"},
        headers=_auth(admin_token),
    )

    # Issuing to the runner-up (not the winner) for this retro is rejected.
    rejected = client.post(
        "/api/credissuer/issue",
        json={"user_id": runner_up["id"], "retro_id": retro_id},
        headers=_auth(admin_token),
    )
    assert rejected.status_code == 400

    # Issuing to the actual Sprint Hero for this retro succeeds.
    accepted = client.post(
        "/api/credissuer/issue",
        json={"user_id": hero["id"], "retro_id": retro_id},
        headers=_auth(admin_token),
    )
    assert accepted.status_code == 200, accepted.text
    assert accepted.json()["user_name"] == "Hero Person"
