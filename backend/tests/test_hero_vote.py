import datetime

from tests.helpers import auth_headers as _auth
from tests.helpers import login as _login
from tests.helpers import seed_admin_with_org as _seed_admin


def _setup_retro_with_participants(client, admin_token, monkeypatch):
    # Two teams so we can prove voting is organization-wide, not team-scoped.
    pmo_resp = client.post(
        "/api/users",
        json={"name": "PMO Lead", "email": "pmo@acme-corp.com", "role": "pmo"},
        headers=_auth(admin_token),
    )
    pmo_id = pmo_resp.json()["id"]

    member_a = client.post(
        "/api/users",
        json={"name": "Member A", "email": "membera@acme-corp.com", "role": "member"},
        headers=_auth(admin_token),
    ).json()
    member_b = client.post(
        "/api/users",
        json={"name": "Member B", "email": "memberb@acme-corp.com", "role": "member"},
        headers=_auth(admin_token),
    ).json()
    # Outsider: not invited to the retro, not on the team, but still a valid
    # org-wide vote candidate.
    outsider = client.post(
        "/api/users",
        json={"name": "Outsider", "email": "outsider@acme-corp.com", "role": "member"},
        headers=_auth(admin_token),
    ).json()

    team = client.post(
        "/api/teams",
        json={
            "name": "Backend Team",
            "description": "",
            "team_lead_id": pmo_id,
            "member_ids": [pmo_id, member_a["id"], member_b["id"]],
        },
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
            "participant_ids": [member_a["id"], member_b["id"]],
        },
        headers=_auth(pmo_token),
    ).json()
    client.post(f"/api/retros/{retro['id']}/invite", headers=_auth(pmo_token))

    return {
        "retro_id": retro["id"],
        "pmo_token": pmo_token,
        "member_a": member_a,
        "member_a_token": _login(client, "membera@acme-corp.com", monkeypatch),
        "member_b": member_b,
        "member_b_token": _login(client, "memberb@acme-corp.com", monkeypatch),
        "outsider": outsider,
    }


def test_org_wide_vote_anonymous_by_default_and_admin_only_results(client, db_session, monkeypatch):
    _seed_admin(db_session)
    admin_token = _login(client, "admin@acme-corp.com", monkeypatch)
    ctx = _setup_retro_with_participants(client, admin_token, monkeypatch)
    retro_id = ctx["retro_id"]

    # Candidate list is org-wide: includes the outsider who isn't on the team
    # or invited to this retro, and excludes the voter themselves.
    candidates_resp = client.get(f"/api/retros/{retro_id}/hero-vote/candidates", headers=_auth(ctx["member_a_token"]))
    assert candidates_resp.status_code == 200
    candidate_ids = {c["id"] for c in candidates_resp.json()}
    assert ctx["outsider"]["id"] in candidate_ids
    assert ctx["member_a"]["id"] not in candidate_ids  # can't vote for self

    # Member A votes for the outsider, anonymously (default), with an optional comment.
    vote_resp = client.put(
        f"/api/retros/{retro_id}/hero-vote",
        json={"candidate_id": ctx["outsider"]["id"], "comment": "Unblocked the deploy pipeline for everyone."},
        headers=_auth(ctx["member_a_token"]),
    )
    assert vote_resp.status_code == 200, vote_resp.text
    assert vote_resp.json()["is_anonymous"] is True
    assert vote_resp.json()["comment"] == "Unblocked the deploy pipeline for everyone."

    # Cannot vote for yourself.
    self_vote = client.put(
        f"/api/retros/{retro_id}/hero-vote",
        json={"candidate_id": ctx["member_b"]["id"], "is_anonymous": False},
        headers=_auth(ctx["member_b_token"]),
    )
    forbidden_self_vote = client.put(
        f"/api/retros/{retro_id}/hero-vote",
        json={"candidate_id": ctx["member_b"]["id"]},
        headers=_auth(ctx["member_b_token"]),
    )
    assert forbidden_self_vote.status_code == 400

    # Member B votes for the outsider too, this time revealing their name, no comment.
    vote_resp_b = client.put(
        f"/api/retros/{retro_id}/hero-vote",
        json={"candidate_id": ctx["outsider"]["id"], "is_anonymous": False},
        headers=_auth(ctx["member_b_token"]),
    )
    assert vote_resp_b.status_code == 200
    assert vote_resp_b.json()["is_anonymous"] is False
    assert vote_resp_b.json()["comment"] is None

    # A user can always see their own vote regardless of anonymity.
    my_vote = client.get(f"/api/retros/{retro_id}/hero-vote/me", headers=_auth(ctx["member_a_token"]))
    assert my_vote.status_code == 200
    assert my_vote.json()["candidate_id"] == ctx["outsider"]["id"]

    # PMO cannot see results — admin only.
    pmo_results = client.get(f"/api/retros/{retro_id}/hero-vote/results", headers=_auth(ctx["pmo_token"]))
    assert pmo_results.status_code == 403

    # A regular member cannot see results either.
    member_results = client.get(f"/api/retros/{retro_id}/hero-vote/results", headers=_auth(ctx["member_a_token"]))
    assert member_results.status_code == 403

    # Admin sees the tally, plus per-vote entries: the anonymous voter's name is
    # hidden but their comment still shows; the revealed voter's name shows.
    admin_results = client.get(f"/api/retros/{retro_id}/hero-vote/results", headers=_auth(admin_token))
    assert admin_results.status_code == 200
    data = admin_results.json()
    assert data["total_votes"] == 2
    top = data["results"][0]
    assert top["user_id"] == ctx["outsider"]["id"]
    assert top["vote_count"] == 2

    entries = sorted(top["entries"], key=lambda e: e["voter_name"] or "")
    anon_entry, named_entry = entries[0], entries[1]
    assert anon_entry["voter_name"] is None
    assert anon_entry["comment"] == "Unblocked the deploy pipeline for everyone."
    assert named_entry["voter_name"] == "Member B"
    assert named_entry["comment"] is None


def test_vote_upsert_and_closed_retro_blocks_voting(client, db_session, monkeypatch):
    _seed_admin(db_session)
    admin_token = _login(client, "admin@acme-corp.com", monkeypatch)
    ctx = _setup_retro_with_participants(client, admin_token, monkeypatch)
    retro_id = ctx["retro_id"]

    client.put(
        f"/api/retros/{retro_id}/hero-vote",
        json={"candidate_id": ctx["outsider"]["id"]},
        headers=_auth(ctx["member_a_token"]),
    )
    # Changing your mind updates the same vote rather than creating a second one.
    updated = client.put(
        f"/api/retros/{retro_id}/hero-vote",
        json={"candidate_id": ctx["member_b"]["id"], "is_anonymous": True},
        headers=_auth(ctx["member_a_token"]),
    )
    assert updated.status_code == 200
    assert updated.json()["candidate_id"] == ctx["member_b"]["id"]

    admin_results = client.get(f"/api/retros/{retro_id}/hero-vote/results", headers=_auth(admin_token)).json()
    assert admin_results["total_votes"] == 1

    client.post(f"/api/retros/{retro_id}/close", headers=_auth(ctx["pmo_token"]))

    blocked = client.put(
        f"/api/retros/{retro_id}/hero-vote",
        json={"candidate_id": ctx["outsider"]["id"]},
        headers=_auth(ctx["member_b_token"]),
    )
    assert blocked.status_code == 400
