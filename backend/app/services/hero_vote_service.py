from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.hero_vote import SprintHeroVote
from app.models.org_membership import OrgMembership
from app.models.retro import Retrospective, RetroParticipant, RetroStatus
from app.models.user import User
from app.schemas.hero_vote import HeroVoteEntry, HeroVoteIn, HeroVoteResultItem, HeroVoteResults
from app.utils.logger import get_logger

logger = get_logger(__name__)


def list_candidates(db: Session, org_id: int, exclude_user_id: int) -> list[User]:
    return (
        db.query(User)
        .join(OrgMembership, OrgMembership.user_id == User.id)
        .filter(
            OrgMembership.org_id == org_id,
            OrgMembership.is_active.is_(True),
            User.is_active.is_(True),
            User.id != exclude_user_id,
        )
        .order_by(User.name)
        .all()
    )


def _get_retro_or_404(db: Session, retro_id: int) -> Retrospective:
    retro = db.get(Retrospective, retro_id)
    if not retro:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Retrospective not found")
    return retro


def _ensure_participant(db: Session, retro_id: int, user_id: int) -> None:
    participant = (
        db.query(RetroParticipant)
        .filter(RetroParticipant.retro_id == retro_id, RetroParticipant.user_id == user_id)
        .first()
    )
    if not participant:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You are not a participant of this retro")


def get_my_vote(db: Session, retro_id: int, voter_id: int) -> SprintHeroVote | None:
    return (
        db.query(SprintHeroVote)
        .filter(SprintHeroVote.retro_id == retro_id, SprintHeroVote.voter_id == voter_id)
        .first()
    )


def cast_vote(db: Session, org_id: int, retro_id: int, voter_id: int, data: HeroVoteIn) -> SprintHeroVote:
    retro = _get_retro_or_404(db, retro_id)
    _ensure_participant(db, retro_id, voter_id)

    if retro.status == RetroStatus.COMPLETED:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Retrospective is completed; voting is closed")

    if data.candidate_id == voter_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="You cannot vote for yourself")

    candidate_membership = (
        db.query(OrgMembership)
        .filter(OrgMembership.org_id == org_id, OrgMembership.user_id == data.candidate_id, OrgMembership.is_active.is_(True))
        .first()
    )
    candidate = db.get(User, data.candidate_id) if candidate_membership else None
    if not candidate or not candidate.is_active:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Selected candidate is not a valid user")

    vote = get_my_vote(db, retro_id, voter_id)
    if not vote:
        vote = SprintHeroVote(retro_id=retro_id, voter_id=voter_id)
        db.add(vote)

    vote.candidate_id = data.candidate_id
    vote.is_anonymous = data.is_anonymous
    vote.comment = data.comment

    db.commit()
    db.refresh(vote)
    logger.info("Sprint Hero vote cast retro_id=%s voter_id=%s anonymous=%s", retro_id, voter_id, data.is_anonymous)
    return vote


def get_results(db: Session, retro_id: int) -> HeroVoteResults:
    _get_retro_or_404(db, retro_id)
    votes = db.query(SprintHeroVote).filter(SprintHeroVote.retro_id == retro_id).all()

    tally: dict[int, dict] = {}
    for v in votes:
        entry = tally.setdefault(v.candidate_id, {"user_id": v.candidate_id, "vote_count": 0, "entries": []})
        entry["vote_count"] += 1
        entry["entries"].append(
            HeroVoteEntry(voter_name=None if v.is_anonymous else v.voter.name, comment=v.comment)
        )

    results = [
        HeroVoteResultItem(
            user_id=entry["user_id"],
            user_name=db.get(User, entry["user_id"]).name,
            vote_count=entry["vote_count"],
            entries=entry["entries"],
        )
        for entry in tally.values()
    ]
    results.sort(key=lambda r: r.vote_count, reverse=True)

    return HeroVoteResults(retro_id=retro_id, total_votes=len(votes), results=results)
