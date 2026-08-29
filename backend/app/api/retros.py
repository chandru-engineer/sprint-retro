from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import CurrentUser, get_current_user, require_admin, require_pmo
from app.database import get_db
from app.models.retro import FeedbackStatus, Retrospective, RetroStatus, RetroParticipant
from app.models.user import UserRole
from app.schemas.feedback import FeedbackOut, FeedbackSave, FeedbackWithUser, ReactRequest
from app.schemas.hero_vote import HeroCandidate, HeroVoteIn, HeroVoteOut, HeroVoteResults
from app.schemas.retro import ParticipantOut, RetroCreate, RetroDetailOut, RetroOut, RetroSummaryOut, RetroUpdate
from app.services import feedback_service, hero_vote_service, retro_service, report_service

router = APIRouter(prefix="/api/retros", tags=["retros"])


def _is_participant(db: Session, retro_id: int, user_id: int) -> bool:
    return (
        db.query(RetroParticipant)
        .filter(RetroParticipant.retro_id == retro_id, RetroParticipant.user_id == user_id)
        .first()
        is not None
    )


def _get_viewable_retro(db: Session, current_user: CurrentUser, retro_id: int) -> Retrospective:
    """Fetches the retro scoped to the caller's org (raises 404 for any other
    org's retro), then checks the caller is allowed to see it."""
    retro = retro_service.get_retro(db, current_user.org_id, retro_id)
    if current_user.role not in (UserRole.ADMIN, UserRole.PMO):
        if not _is_participant(db, retro_id, current_user.id):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not invited to this retrospective")
    return retro


def _to_detail(db: Session, retro: Retrospective) -> RetroDetailOut:
    stats = retro_service.get_participation_stats(db, retro.id)
    participants = [
        ParticipantOut(
            id=p.id,
            user_id=p.user_id,
            user_name=p.user.name,
            user_email=p.user.email,
            invitation_status=p.invitation_status,
            feedback_status=p.feedback_status,
            invited_at=p.invited_at,
            submitted_at=p.submitted_at,
        )
        for p in retro.participants
    ]
    return RetroDetailOut(
        **RetroOut.model_validate(retro).model_dump(),
        participants=participants,
        submitted_count=stats["submitted"],
        total_count=stats["total"],
        completion_percent=stats["percent"],
    )


@router.get("", response_model=list[RetroOut])
def list_retros(
    project_id: int | None = None,
    team_id: int | None = None,
    status_filter: RetroStatus | None = None,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    retros = retro_service.list_retros(db, current_user.org_id, project_id, team_id, status_filter)
    if current_user.role == UserRole.MEMBER:
        retros = [r for r in retros if _is_participant(db, r.id, current_user.id)]
    return retros


@router.get("/dashboard", response_model=list[RetroSummaryOut])
def get_retro_dashboard(
    project_id: int | None = None,
    team_id: int | None = None,
    status_filter: RetroStatus | None = None,
    q: str | None = None,
    user_id: int | None = None,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(require_pmo),
):
    return retro_service.list_retro_summaries(db, current_user.org_id, project_id, team_id, status_filter, q, user_id)


@router.post("", response_model=RetroOut, status_code=201)
def create_retro(
    payload: RetroCreate, db: Session = Depends(get_db), current_user: CurrentUser = Depends(require_pmo)
):
    return retro_service.create_retro(db, current_user.org_id, payload, created_by=current_user.id)


@router.get("/{retro_id}", response_model=RetroDetailOut)
def get_retro(
    retro_id: int, db: Session = Depends(get_db), current_user: CurrentUser = Depends(get_current_user)
):
    retro = _get_viewable_retro(db, current_user, retro_id)
    return _to_detail(db, retro)


@router.put("/{retro_id}", response_model=RetroOut)
def update_retro(
    retro_id: int,
    payload: RetroUpdate,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(require_pmo),
):
    return retro_service.update_retro(db, current_user.org_id, retro_id, payload)


@router.post("/{retro_id}/invite", response_model=RetroDetailOut)
def send_invitations(
    retro_id: int, db: Session = Depends(get_db), current_user: CurrentUser = Depends(require_pmo)
):
    retro = retro_service.send_invitations(db, current_user.org_id, retro_id)
    return _to_detail(db, retro)


@router.post("/{retro_id}/close", response_model=RetroOut)
def close_retro(retro_id: int, db: Session = Depends(get_db), current_user: CurrentUser = Depends(require_pmo)):
    return retro_service.close_retro(db, current_user.org_id, retro_id)


@router.get("/{retro_id}/participants", response_model=list[ParticipantOut])
def get_participants(
    retro_id: int, db: Session = Depends(get_db), current_user: CurrentUser = Depends(require_pmo)
):
    retro = retro_service.get_retro(db, current_user.org_id, retro_id)
    return _to_detail(db, retro).participants


# --- Feedback (team member's own response) ---


@router.get("/{retro_id}/feedback/me", response_model=FeedbackOut | None)
def get_my_feedback(
    retro_id: int, db: Session = Depends(get_db), current_user: CurrentUser = Depends(get_current_user)
):
    _get_viewable_retro(db, current_user, retro_id)
    return feedback_service.get_my_feedback(db, retro_id, current_user.id)


@router.put("/{retro_id}/feedback/draft", response_model=FeedbackOut)
def save_draft(
    retro_id: int,
    payload: FeedbackSave,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    _get_viewable_retro(db, current_user, retro_id)
    return feedback_service.save_draft(db, retro_id, current_user.id, payload)


@router.post("/{retro_id}/feedback/submit", response_model=FeedbackOut)
def submit_feedback(
    retro_id: int,
    payload: FeedbackSave,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    _get_viewable_retro(db, current_user, retro_id)
    return feedback_service.submit_feedback(db, retro_id, current_user.id, payload)


# --- Feedback review ---
# Everyone on the retro can browse each other's *submitted* responses — this
# is the point of a retro. Drafts stay private to their author. PMO/Admin
# additionally see drafts-in-progress, for tracking completion.


def _to_feedback_with_user(db: Session, fb, current_user_id: int) -> FeedbackWithUser:
    reactions = feedback_service.get_reactions(db, fb.id, current_user_id)
    return FeedbackWithUser(
        **FeedbackOut.model_validate(fb).model_dump(), user_name=fb.user.name, reactions=reactions
    )


@router.get("/{retro_id}/feedback", response_model=list[FeedbackWithUser])
def list_all_feedback(
    retro_id: int, db: Session = Depends(get_db), current_user: CurrentUser = Depends(get_current_user)
):
    _get_viewable_retro(db, current_user, retro_id)
    is_host = current_user.role in (UserRole.ADMIN, UserRole.PMO)
    feedbacks = feedback_service.list_feedback_for_retro(db, retro_id, submitted_only=not is_host)
    return [_to_feedback_with_user(db, fb, current_user.id) for fb in feedbacks]


@router.get("/{retro_id}/feedback/{user_id}", response_model=FeedbackWithUser)
def get_user_feedback(
    retro_id: int, user_id: int, db: Session = Depends(get_db), current_user: CurrentUser = Depends(get_current_user)
):
    _get_viewable_retro(db, current_user, retro_id)
    fb = feedback_service.get_my_feedback(db, retro_id, user_id)
    is_host = current_user.role in (UserRole.ADMIN, UserRole.PMO)
    if not fb or (not is_host and fb.status != FeedbackStatus.SUBMITTED):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No feedback found for this user")
    return _to_feedback_with_user(db, fb, current_user.id)


@router.post("/{retro_id}/feedback/{user_id}/react", response_model=FeedbackWithUser)
def react_to_feedback(
    retro_id: int,
    user_id: int,
    payload: ReactRequest,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    _get_viewable_retro(db, current_user, retro_id)
    fb = feedback_service.get_my_feedback(db, retro_id, user_id)
    is_host = current_user.role in (UserRole.ADMIN, UserRole.PMO)
    if not fb or (not is_host and fb.status != FeedbackStatus.SUBMITTED):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No submitted response to react to")
    feedback_service.toggle_reaction(db, fb.id, current_user.id, payload.emoji, payload.question_key)
    db.refresh(fb)
    return _to_feedback_with_user(db, fb, current_user.id)


# --- Report ---


@router.get("/{retro_id}/report")
def get_report(retro_id: int, db: Session = Depends(get_db), current_user: CurrentUser = Depends(require_pmo)):
    retro = retro_service.get_retro(db, current_user.org_id, retro_id)
    return report_service.build_report(db, retro)


# --- Sprint Hero voting ---
# Any participant of a retro can vote for anyone in their organization (except
# themselves). Votes are anonymous unless the voter opts to reveal their name.
# Only Admins can view the aggregated results.


@router.get("/{retro_id}/hero-vote/candidates", response_model=list[HeroCandidate])
def get_hero_vote_candidates(
    retro_id: int, db: Session = Depends(get_db), current_user: CurrentUser = Depends(get_current_user)
):
    _get_viewable_retro(db, current_user, retro_id)
    return hero_vote_service.list_candidates(db, current_user.org_id, exclude_user_id=current_user.id)


@router.get("/{retro_id}/hero-vote/me", response_model=HeroVoteOut | None)
def get_my_hero_vote(
    retro_id: int, db: Session = Depends(get_db), current_user: CurrentUser = Depends(get_current_user)
):
    _get_viewable_retro(db, current_user, retro_id)
    vote = hero_vote_service.get_my_vote(db, retro_id, current_user.id)
    if not vote:
        return None
    return HeroVoteOut(
        candidate_id=vote.candidate_id,
        candidate_name=vote.candidate.name,
        is_anonymous=vote.is_anonymous,
        comment=vote.comment,
        updated_at=vote.updated_at,
    )


@router.put("/{retro_id}/hero-vote", response_model=HeroVoteOut)
def cast_hero_vote(
    retro_id: int,
    payload: HeroVoteIn,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    _get_viewable_retro(db, current_user, retro_id)
    vote = hero_vote_service.cast_vote(db, current_user.org_id, retro_id, current_user.id, payload)
    return HeroVoteOut(
        candidate_id=vote.candidate_id,
        candidate_name=vote.candidate.name,
        is_anonymous=vote.is_anonymous,
        comment=vote.comment,
        updated_at=vote.updated_at,
    )


@router.get("/{retro_id}/hero-vote/results", response_model=HeroVoteResults, dependencies=[Depends(require_admin)])
def get_hero_vote_results(
    retro_id: int, db: Session = Depends(get_db), current_user: CurrentUser = Depends(require_admin)
):
    retro_service.get_retro(db, current_user.org_id, retro_id)
    return hero_vote_service.get_results(db, retro_id)
