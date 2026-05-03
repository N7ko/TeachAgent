from enum import StrEnum
from typing import Literal

from pydantic import BaseModel, Field


class SessionStatus(StrEnum):
    TEACHING = "teaching"
    WAITING_FOR_ANSWER = "waiting_for_answer"
    MASTERED = "mastered"


class QuizQuestion(BaseModel):
    prompt: str
    expected_points: list[str] = Field(default_factory=list)


class StartSessionRequest(BaseModel):
    topic: str = Field(..., min_length=1, max_length=2000)


class SubmitAnswerRequest(BaseModel):
    answer: str = Field(..., min_length=1, max_length=4000)


class Feedback(BaseModel):
    mastered: bool
    score: float = Field(..., ge=0, le=1)
    strengths: list[str] = Field(default_factory=list)
    weak_points: list[str] = Field(default_factory=list)
    guidance: str


class TeachingSession(BaseModel):
    id: str
    topic: str
    explanation: str
    question: QuizQuestion | None = None
    feedback: Feedback | None = None
    status: SessionStatus
    attempts: int = 0
    history: list[dict[str, str]] = Field(default_factory=list)


class SessionResponse(BaseModel):
    session: TeachingSession
    next_action: Literal["answer_question", "review_feedback", "complete"]

