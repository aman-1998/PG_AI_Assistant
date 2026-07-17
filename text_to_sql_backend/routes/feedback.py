"""Endpoint for submitting product feedback from the "Contact & Feedback" page."""
from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from db.models import User
from db.postgres import get_db
from models.feedback_schemas import FeedbackCreateRequest, FeedbackResponse
from services import feedback_service
from services.auth_service import get_current_user

router = APIRouter(prefix="/feedback", tags=["feedback"])


@router.post("", response_model=FeedbackResponse, status_code=201)
def submit_feedback(
    payload: FeedbackCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> FeedbackResponse:
    feedback = feedback_service.create_feedback(db, current_user.id, payload)
    return FeedbackResponse.model_validate(feedback)
