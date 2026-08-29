"""
Development seed script for Sprint Retro.

Creates a sample organization, users, a team, a project, and a retrospective
so the app can be explored immediately after `docker compose up -d`.

There are no passwords — Sprint Retro logs everyone in with a one-time code
emailed to them. To log in as any of the users below, enter their email on
the login page:

    admin@acme-corp.com   (Admin, org: Acme Corp)
    pmo@acme-corp.com     (PMO / Team Lead, org: Acme Corp)
    rahul@acme-corp.com   (Team Member, org: Acme Corp)
    priya@acme-corp.com   (Team Member, org: Acme Corp)

If SMTP isn't configured, the sign-in code is printed to the backend's
console log instead (development convenience only — never relied on once
SMTP is set up). Run once: `python seed.py`
"""
import datetime

from app.database import Base, SessionLocal, engine
from app.models.org_membership import OrgMembership
from app.models.organization import Organization
from app.models.project import Project, ProjectStatus
from app.models.retro import Retrospective, RetroParticipant, RetroStatus, InvitationStatus, FeedbackStatus
from app.models.team import Team, TeamMember
from app.models.user import User, UserRole


def run():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        if db.query(User).count() > 0:
            print("Seed data already present, skipping.")
            return

        org = Organization(name="Acme Corp")
        db.add(org)
        db.flush()

        admin = User(name="Alice Admin", email="admin@acme-corp.com",
                     password_hash=hash_password(DEV_PASSWORD), is_verified=True)
        pmo = User(name="Pat PMO", email="pmo@acme-corp.com",
                   password_hash=hash_password(DEV_PASSWORD), is_verified=True)
        rahul = User(name="Rahul", email="rahul@acme-corp.com",
                     password_hash=hash_password(DEV_PASSWORD), is_verified=True)
        priya = User(name="Priya", email="priya@acme-corp.com",
                     password_hash=hash_password(DEV_PASSWORD), is_verified=True)
        db.add_all([admin, pmo, rahul, priya])
        db.flush()

        db.add_all([
            OrgMembership(org_id=org.id, user_id=admin.id, role=UserRole.ADMIN),
            OrgMembership(org_id=org.id, user_id=pmo.id, role=UserRole.PMO),
            OrgMembership(org_id=org.id, user_id=rahul.id, role=UserRole.MEMBER),
            OrgMembership(org_id=org.id, user_id=priya.id, role=UserRole.MEMBER),
        ])

        team = Team(org_id=org.id, name="Backend Team", description="Owns core backend services",
                    team_lead_id=pmo.id)
        db.add(team)
        db.flush()
        db.add_all([
            TeamMember(team_id=team.id, user_id=pmo.id),
            TeamMember(team_id=team.id, user_id=rahul.id),
            TeamMember(team_id=team.id, user_id=priya.id),
        ])

        project = Project(org_id=org.id, name="Payment Platform", description="Core payments service",
                           team_id=team.id, status=ProjectStatus.ACTIVE)
        db.add(project)
        db.flush()

        today = datetime.date.today()
        retro = Retrospective(
            org_id=org.id,
            project_id=project.id,
            team_id=team.id,
            name="Sprint 25 Retrospective",
            sprint_name="Sprint 25",
            sprint_start_date=today - datetime.timedelta(days=14),
            sprint_end_date=today - datetime.timedelta(days=1),
            retro_date=today + datetime.timedelta(days=2),
            retro_time=datetime.time(10, 0),
            status=RetroStatus.OPEN,
            created_by=pmo.id,
        )
        db.add(retro)
        db.flush()
        db.add_all([
            RetroParticipant(retro_id=retro.id, user_id=rahul.id, invitation_status=InvitationStatus.SENT,
                              feedback_status=FeedbackStatus.NOT_STARTED),
            RetroParticipant(retro_id=retro.id, user_id=priya.id, invitation_status=InvitationStatus.SENT,
                              feedback_status=FeedbackStatus.NOT_STARTED),
        ])

        db.commit()
        print("Seed data created.")
        print(f"Login with any of the emails above and password: {DEV_PASSWORD}")
    finally:
        db.close()


if __name__ == "__main__":
    run()
