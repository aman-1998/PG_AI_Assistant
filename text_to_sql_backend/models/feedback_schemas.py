"""Pydantic schemas for the "Contact & Feedback" page."""
from __future__ import annotations

import datetime

from pydantic import BaseModel, Field

FEEDBACK_RATING_MIN = 1
FEEDBACK_RATING_MAX = 5
FEEDBACK_MESSAGE_MAX_LENGTH = 4000


class FeedbackCreateRequest(BaseModel):
    message: str = Field(min_length=1, max_length=FEEDBACK_MESSAGE_MAX_LENGTH)
    # Optional star rating (1-5) - a user may leave a comment without rating the product.
    rating: int | None = Field(default=None, ge=FEEDBACK_RATING_MIN, le=FEEDBACK_RATING_MAX)


class FeedbackResponse(BaseModel):
    id: int
    message: str
    rating: int | None = None
    created_at: datetime.datetime

    model_config = {"from_attributes": True}
