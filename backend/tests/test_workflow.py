import datetime

from tests.helpers import auth_headers as _auth
from tests.helpers import login as _login
from tests.helpers import seed_admin_with_org


def test_login_unknown_email_is_rejected(client, db_session):
    seed_admin_with_org(db_session)
    resp = client.post("/api/auth/login", json={"email": "nobody@acme-corp.com"})
    assert resp.status_code == 404


def test_full_retro_workflow(client, db_session, monkeypatch):
    seed_admin_with_org(db_session)
    admin_token = _login(client, "admin@acme-corp.com", monkeypatch)

    # Admin creates users
    pmo_resp = client.post(
        "/api/users",
        json={"name": "PMO Lead", "email": "pmo@acme-corp.com", "role": "pmo"},
        headers=_auth(admin_token),
    )
    assert pmo_resp.status_code == 201, pmo_resp.text
    pmo_id = pmo_resp.json()["id"]

    member_resp = client.post(
        "/api/users",
        json={"name": "Member One", "email": "member1@acme-corp.com", "role": "member"},
        headers=_auth(admin_token),
    )
    assert member_resp.status_code == 201
    member_id = member_resp.json()["id"]

    # Admin creates team with member
    team_resp = client.post(
        "/api/teams",
        json={"name": "Backend Team", "description": "", "team_lead_id": pmo_id, "member_ids": [pmo_id, member_id]},
        headers=_auth(admin_token),
    )
    assert team_resp.status_code == 201, team_resp.text
    team_id = team_resp.json()["id"]
    assert len(team_resp.json()["members"]) == 2

    # Admin creates project
    project_resp = client.post(
        "/api/projects",
        json={"name": "Payment Platform", "description": "", "team_id": team_id, "status": "active"},
        headers=_auth(admin_token),
    )
    assert project_resp.status_code == 201
    project_id = project_resp.json()["id"]

    # Non-admin cannot create users (authorization check)
    member_login = _login(client, "member1@acme-corp.com", monkeypatch)
    forbidden_resp = client.post(
        "/api/users",
        json={"name": "X", "email": "x@acme-corp.com", "role": "member"},
        headers=_auth(member_login),
    )
    assert forbidden_resp.status_code == 403

    # PMO creates retro and invites member
    pmo_token = _login(client, "pmo@acme-corp.com", monkeypatch)
    today = datetime.date.today()
    retro_resp = client.post(
        "/api/retros",
        json={
            "project_id": project_id,
            "team_id": team_id,
            "name": "Sprint 25 Retro",
            "sprint_name": "Sprint 25",
            "sprint_start_date": str(today - datetime.timedelta(days=14)),
            "sprint_end_date": str(today - datetime.timedelta(days=1)),
            "retro_date": str(today + datetime.timedelta(days=1)),
            "retro_time": "10:00:00",
            "participant_ids": [member_id],
        },
        headers=_auth(pmo_token),
    )
    assert retro_resp.status_code == 201, retro_resp.text
    retro_id = retro_resp.json()["id"]
    assert retro_resp.json()["status"] == "draft"

    # Send invitations -> retro moves to open
    invite_resp = client.post(f"/api/retros/{retro_id}/invite", headers=_auth(pmo_token))
    assert invite_resp.status_code == 200, invite_resp.text
    assert invite_resp.json()["status"] == "open"
    assert invite_resp.json()["total_count"] == 1

    # Member saves a draft
    draft_payload = {
        "achievement": "Completed API integration",
        "went_well": "Good collaboration",
        "did_not_go_well": "",
        "learnings": "",
        "improvements": "",
    }
    draft_resp = client.put(
        f"/api/retros/{retro_id}/feedback/draft", json=draft_payload, headers=_auth(member_login)
    )
    assert draft_resp.status_code == 200, draft_resp.text
    assert draft_resp.json()["status"] == "draft"

    # Submitting with missing required fields fails validation
    incomplete_submit = client.post(
        f"/api/retros/{retro_id}/feedback/submit", json=draft_payload, headers=_auth(member_login)
    )
    assert incomplete_submit.status_code == 400

    # Member completes and submits response
    full_payload = {
        "achievement": "Completed API integration",
        "went_well": "Good collaboration",
        "did_not_go_well": "CI flakiness",
        "learnings": "Learned about deployment pipelines",
        "improvements": "Improve CI reliability",
    }
    submit_resp = client.post(
        f"/api/retros/{retro_id}/feedback/submit", json=full_payload, headers=_auth(member_login)
    )
    assert submit_resp.status_code == 200, submit_resp.text
    assert submit_resp.json()["status"] == "submitted"
    assert submit_resp.json()["submitted_at"] is not None

    # Editing after submission is blocked
    reedit_resp = client.put(
        f"/api/retros/{retro_id}/feedback/draft", json=full_payload, headers=_auth(member_login)
    )
    assert reedit_resp.status_code == 400

    # PMO sees participation stats and reviews responses
    detail_resp = client.get(f"/api/retros/{retro_id}", headers=_auth(pmo_token))
    assert detail_resp.status_code == 200
    assert detail_resp.json()["submitted_count"] == 1
    assert detail_resp.json()["total_count"] == 1
    assert detail_resp.json()["completion_percent"] == 100.0

    all_feedback_resp = client.get(f"/api/retros/{retro_id}/feedback", headers=_auth(pmo_token))
    assert all_feedback_resp.status_code == 200
    assert len(all_feedback_resp.json()) == 1
    assert all_feedback_resp.json()[0]["user_name"] == "Member One"

    # Members can see teammates' submitted responses too (not just PMO/Admin) —
    # everyone sees each other's retro answers; only Sprint Hero voting stays private.
    member_review = client.get(f"/api/retros/{retro_id}/feedback", headers=_auth(member_login))
    assert member_review.status_code == 200
    assert len(member_review.json()) == 1

    # PMO generates the consolidated report
    report_resp = client.get(f"/api/retros/{retro_id}/report", headers=_auth(pmo_token))
    assert report_resp.status_code == 200
    report = report_resp.json()
    assert report["responses"] == 1
    assert "Completed API integration" in report["achievements"]

    # PMO closes the retro
    close_resp = client.post(f"/api/retros/{retro_id}/close", headers=_auth(pmo_token))
    assert close_resp.status_code == 200
    assert close_resp.json()["status"] == "completed"

    # Retro remains visible in history for the member
    history_resp = client.get("/api/retros", headers=_auth(member_login))
    assert history_resp.status_code == 200
    assert any(r["id"] == retro_id for r in history_resp.json())


def test_member_cannot_see_a_teammates_draft(client, db_session, monkeypatch):
    admin, _org = seed_admin_with_org(db_session)
    admin_token = _login(client, admin.email, monkeypatch)

    member_a = client.post(
        "/api/users", json={"name": "Member A", "email": "membera@acme-corp.com", "role": "member"},
        headers=_auth(admin_token),
    ).json()
    member_b = client.post(
        "/api/users", json={"name": "Member B", "email": "memberb@acme-corp.com", "role": "member"},
        headers=_auth(admin_token),
    ).json()
    team = client.post(
        "/api/teams",
        json={"name": "Team", "description": "", "team_lead_id": None, "member_ids": [member_a["id"], member_b["id"]]},
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
            "retro_time": "10:00:00", "participant_ids": [member_a["id"], member_b["id"]],
        },
        headers=_auth(admin_token),
    ).json()
    client.post(f"/api/retros/{retro['id']}/invite", headers=_auth(admin_token))

    member_a_token = _login(client, "membera@acme-corp.com", monkeypatch)
    member_b_token = _login(client, "memberb@acme-corp.com", monkeypatch)

    # Member A only saves a draft — never submits.
    client.put(
        f"/api/retros/{retro['id']}/feedback/draft",
        json={"achievement": "wip", "went_well": "", "did_not_go_well": "", "learnings": "", "improvements": ""},
        headers=_auth(member_a_token),
    )

    # Member B submits a real response.
    client.post(
        f"/api/retros/{retro['id']}/feedback/submit",
        json={
            "achievement": "Shipped the feature", "went_well": "Good pairing", "did_not_go_well": "Slow CI",
            "learnings": "New testing approach", "improvements": "Faster CI",
        },
        headers=_auth(member_b_token),
    )

    # Member B reviewing the retro sees only submitted responses — Member A's
    # draft never appears, even though Member B is a participant too.
    review = client.get(f"/api/retros/{retro['id']}/feedback", headers=_auth(member_b_token))
    assert review.status_code == 200
    names = {fb["user_name"] for fb in review.json()}
    assert names == {"Member B"}

    # Fetching Member A's response directly also 404s for a peer (it's a draft).
    direct = client.get(f"/api/retros/{retro['id']}/feedback/{member_a['id']}", headers=_auth(member_b_token))
    assert direct.status_code == 404

    # But the host (Admin) can still see the in-progress draft for tracking.
    admin_review = client.get(f"/api/retros/{retro['id']}/feedback", headers=_auth(admin_token))
    admin_names = {fb["user_name"] for fb in admin_review.json()}
    assert admin_names == {"Member A", "Member B"}
