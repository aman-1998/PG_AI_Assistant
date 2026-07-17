"""Service layer for user-submitted product feedback."""
from __future__ import annotations

from sqlalchemy.orm import Session

from db.models import Feedback
from models.feedback_schemas import FeedbackCreateRequest


def create_feedback(db: Session, user_id: int, payload: FeedbackCreateRequest) -> Feedback:
    feedback = Feedback(user_id=user_id, message=payload.message, rating=payload.rating)
    db.add(feedback)
    db.commit()
    db.refresh(feedback)
    return feedback
