import datetime

from tests.helpers import auth_headers as _auth
from tests.helpers import login as _login
from tests.helpers import seed_admin_with_org


def test_react_to_submitted_response_toggle(client, db_session, monkeypatch):
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

    # Reacting to a draft is not allowed — nothing to react to yet.
    client.put(
        f"/api/retros/{retro['id']}/feedback/draft",
        json={"achievement": "wip", "went_well": "", "did_not_go_well": "", "learnings": "", "improvements": ""},
        headers=_auth(member_a_token),
    )
    still_draft = client.post(
        f"/api/retros/{retro['id']}/feedback/{member_a['id']}/react",
        json={"emoji": "👍", "question_key": "achievement"},
        headers=_auth(member_b_token),
    )
    assert still_draft.status_code == 404

    # Member A submits their response.
    client.post(
        f"/api/retros/{retro['id']}/feedback/submit",
        json={
            "achievement": "Shipped it", "went_well": "Great teamwork", "did_not_go_well": "Nothing much",
            "learnings": "Learned a lot", "improvements": "Keep it up",
        },
        headers=_auth(member_a_token),
    )

    # Unsupported emoji is rejected.
    bad_emoji = client.post(
        f"/api/retros/{retro['id']}/feedback/{member_a['id']}/react",
        json={"emoji": "🐸", "question_key": "achievement"},
        headers=_auth(member_b_token),
    )
    assert bad_emoji.status_code == 400

    # Unsupported question key is rejected.
    bad_question = client.post(
        f"/api/retros/{retro['id']}/feedback/{member_a['id']}/react",
        json={"emoji": "👍", "question_key": "not_a_question"},
        headers=_auth(member_b_token),
    )
    assert bad_question.status_code == 400

    # Member B reacts with 👍 on the "achievement" answer specifically.
    react1 = client.post(
        f"/api/retros/{retro['id']}/feedback/{member_a['id']}/react",
        json={"emoji": "👍", "question_key": "achievement"},
        headers=_auth(member_b_token),
    )
    assert react1.status_code == 200, react1.text
    reactions = react1.json()["reactions"]
    assert reactions == {"achievement": [{"emoji": "👍", "count": 1, "reacted_by_me": True}]}

    # Reacting to a *different* question on the same response doesn't merge into the first —
    # each question item tracks its own reactions independently.
    react_other_question = client.post(
        f"/api/retros/{retro['id']}/feedback/{member_a['id']}/react",
        json={"emoji": "🎉", "question_key": "went_well"},
        headers=_auth(member_b_token),
    )
    assert react_other_question.json()["reactions"] == {
        "achievement": [{"emoji": "👍", "count": 1, "reacted_by_me": True}],
        "went_well": [{"emoji": "🎉", "count": 1, "reacted_by_me": True}],
    }

    # Admin also reacts with 👍 on "achievement" — count goes up, but "reacted_by_me" is per-viewer.
    react2 = client.post(
        f"/api/retros/{retro['id']}/feedback/{member_a['id']}/react",
        json={"emoji": "👍", "question_key": "achievement"},
        headers=_auth(admin_token),
    )
    assert react2.json()["reactions"]["achievement"] == [{"emoji": "👍", "count": 2, "reacted_by_me": True}]

    # From Member B's perspective, the count is 2 but reacted_by_me still reflects their own reaction.
    listing = client.get(f"/api/retros/{retro['id']}/feedback", headers=_auth(member_b_token)).json()
    entry = next(fb for fb in listing if fb["user_id"] == member_a["id"])
    assert entry["reactions"]["achievement"] == [{"emoji": "👍", "count": 2, "reacted_by_me": True}]

    # Toggling the same emoji+question again removes Member B's reaction (count drops to 1),
    # and leaves the "went_well" reaction untouched.
    react3 = client.post(
        f"/api/retros/{retro['id']}/feedback/{member_a['id']}/react",
        json={"emoji": "👍", "question_key": "achievement"},
        headers=_auth(member_b_token),
    )
    body3 = react3.json()["reactions"]
    assert body3["achievement"] == [{"emoji": "👍", "count": 1, "reacted_by_me": False}]
    assert body3["went_well"] == [{"emoji": "🎉", "count": 1, "reacted_by_me": True}]
