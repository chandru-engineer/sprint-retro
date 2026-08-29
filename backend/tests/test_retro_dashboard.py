import datetime

from tests.helpers import auth_headers as _auth
from tests.helpers import login as _login
from tests.helpers import seed_admin_with_org as _seed_admin


def test_retro_dashboard_search_and_authorization(client, db_session, monkeypatch):
    _seed_admin(db_session)
    admin_token = _login(client, "admin@acme-corp.com", monkeypatch)

    pmo_id = client.post(
        "/api/users",
        json={"name": "PMO Lead", "email": "pmo@acme-corp.com", "role": "pmo"},
        headers=_auth(admin_token),
    ).json()["id"]
    member_id = client.post(
        "/api/users",
        json={"name": "Member One", "email": "member1@acme-corp.com", "role": "member"},
        headers=_auth(admin_token),
    ).json()["id"]

    team = client.post(
        "/api/teams",
        json={"name": "Backend Team", "description": "", "team_lead_id": pmo_id, "member_ids": [pmo_id, member_id]},
        headers=_auth(admin_token),
    ).json()

    project = client.post(
        "/api/projects",
        json={"name": "Payment Platform", "description": "", "team_id": team["id"], "status": "active"},
        headers=_auth(admin_token),
    ).json()

    pmo_token = _login(client, "pmo@acme-corp.com", monkeypatch)
    today = datetime.date.today()
    retro = client.post(
        "/api/retros",
        json={
            "project_id": project["id"],
            "team_id": team["id"],
            "name": "Sprint 25 Retro",
            "sprint_name": "Sprint 25",
            "sprint_start_date": str(today - datetime.timedelta(days=14)),
            "sprint_end_date": str(today - datetime.timedelta(days=1)),
            "retro_date": str(today + datetime.timedelta(days=1)),
            "retro_time": "10:00:00",
            "participant_ids": [member_id],
        },
        headers=_auth(pmo_token),
    ).json()
    client.post(f"/api/retros/{retro['id']}/invite", headers=_auth(pmo_token))

    # Member cannot access the host dashboard.
    member_token = _login(client, "member1@acme-corp.com", monkeypatch)
    forbidden = client.get("/api/retros/dashboard", headers=_auth(member_token))
    assert forbidden.status_code == 403

    # PMO (a retro host) sees it, with denormalized names and participation stats.
    dash_resp = client.get("/api/retros/dashboard", headers=_auth(pmo_token))
    assert dash_resp.status_code == 200
    items = dash_resp.json()
    assert len(items) == 1
    item = items[0]
    assert item["project_name"] == "Payment Platform"
    assert item["team_name"] == "Backend Team"
    assert item["total_count"] == 1
    assert item["submitted_count"] == 0

    # Admin also sees it, and search matches by sprint name.
    search_hit = client.get("/api/retros/dashboard?q=Sprint 25", headers=_auth(admin_token))
    assert search_hit.status_code == 200
    assert len(search_hit.json()) == 1

    # Search matches by project name too.
    search_project = client.get("/api/retros/dashboard?q=Payment", headers=_auth(admin_token))
    assert len(search_project.json()) == 1

    # No match for an unrelated query.
    search_miss = client.get("/api/retros/dashboard?q=nonexistent-xyz", headers=_auth(admin_token))
    assert search_miss.json() == []
