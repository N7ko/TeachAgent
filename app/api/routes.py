import json
from collections.abc import Iterator

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

from app.core.config import settings
from app.deepseek_client import deepseek_client
from app.models import SessionResponse, StartSessionRequest, SubmitAnswerRequest, TeachingSession
from app.services.session_service import SessionService

router = APIRouter()
session_service = SessionService()


def _sse(events: Iterator[dict]) -> Iterator[str]:
    for event in events:
        yield f"data: {json.dumps(event, ensure_ascii=False)}\n\n"


@router.get("/")
async def root() -> dict[str, str]:
    return {
        "message": "TeachAgent API is running",
        "environment": settings.environment,
        "llm": "deepseek" if deepseek_client.enabled else "local-fallback",
        "model": deepseek_client.model if deepseek_client.enabled else "rules",
    }


@router.post("/api/sessions", response_model=SessionResponse)
async def start_session(payload: StartSessionRequest) -> SessionResponse:
    return session_service.start(payload)


@router.post("/api/sessions/stream")
async def start_session_stream(payload: StartSessionRequest) -> StreamingResponse:
    def event_stream() -> Iterator[str]:
        try:
            yield from _sse(session_service.start_stream(payload))
        except Exception as exc:
            yield from _sse(iter([{"type": "error", "message": str(exc)}]))

    return StreamingResponse(event_stream(), media_type="text/event-stream")


@router.get("/api/sessions/{session_id}", response_model=TeachingSession)
async def get_session(session_id: str) -> TeachingSession:
    session = session_service.get(session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found")
    return session


@router.post("/api/sessions/{session_id}/answer", response_model=SessionResponse)
async def submit_answer(session_id: str, payload: SubmitAnswerRequest) -> SessionResponse:
    try:
        return session_service.answer(session_id, payload)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Session not found") from exc
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@router.post("/api/sessions/{session_id}/answer/stream")
async def submit_answer_stream(session_id: str, payload: SubmitAnswerRequest) -> StreamingResponse:
    def event_stream() -> Iterator[str]:
        try:
            yield from _sse(session_service.answer_stream(session_id, payload))
        except KeyError:
            yield from _sse(iter([{"type": "error", "message": "Session not found"}]))
        except ValueError as exc:
            yield from _sse(iter([{"type": "error", "message": str(exc)}]))
        except Exception as exc:
            yield from _sse(iter([{"type": "error", "message": str(exc)}]))

    return StreamingResponse(event_stream(), media_type="text/event-stream")
