from uuid import uuid4

from collections.abc import Iterator

from app.deepseek_client import deepseek_client
from app.models import (
    SessionResponse,
    SessionStatus,
    StartSessionRequest,
    SubmitAnswerRequest,
    TeachingSession,
)
from app.tutor_engine import TutorState, answer_graph, evaluate_node, explain_node, quiz_node, remediate_node, start_graph


def _fallback_chunks(text: str, size: int = 18) -> Iterator[str]:
    for index in range(0, len(text), size):
        yield text[index : index + size]


class SessionService:
    def __init__(self) -> None:
        self._sessions: dict[str, TeachingSession] = {}

    def start(self, payload: StartSessionRequest) -> SessionResponse:
        state: TutorState = start_graph.invoke({"topic": payload.topic, "attempts": 0, "history": []})
        session = TeachingSession(
            id=str(uuid4()),
            topic=payload.topic,
            explanation=state["explanation"],
            question=state["question"],
            status=SessionStatus.WAITING_FOR_ANSWER,
            attempts=0,
            history=state.get("history", []),
        )
        self._sessions[session.id] = session
        return SessionResponse(session=session, next_action="answer_question")

    def start_stream(self, payload: StartSessionRequest) -> Iterator[dict]:
        session_id = str(uuid4())
        state: TutorState = {"topic": payload.topic, "attempts": 0, "history": []}
        yield {"type": "session_started", "session_id": session_id, "topic": payload.topic}

        explanation = ""
        try:
            if deepseek_client.enabled:
                chunks = deepseek_client.chat_text_stream(
                    system=(
                        "你是 TeachAgent 的专业课程助教。请用中文生成教学解释，要求准确、结构化、"
                        "面向学生理解，不要编造来源。直接输出讲解正文，不要输出 JSON，"
                        "不要使用 Markdown 标题、加粗符号或代码围栏。"
                    ),
                    user=(
                        "请解释下面的关键词或文本。解释应包含定义、作用、关键机制、应用场景，"
                        "并控制在 500 到 900 字。\n\n"
                        f"学习内容：{payload.topic}"
                    ),
                    max_tokens=1800,
                )
            else:
                fallback_state = explain_node(state)
                chunks = _fallback_chunks(fallback_state["explanation"])

            for chunk in chunks:
                explanation += chunk
                yield {"type": "explanation_delta", "delta": chunk}
        except Exception as exc:
            fallback_state = explain_node(state)
            explanation = fallback_state["explanation"]
            yield {"type": "notice", "message": f"流式模型调用失败，已切换本地讲解：{exc}"}
            for chunk in _fallback_chunks(explanation):
                yield {"type": "explanation_delta", "delta": chunk}

        state = quiz_node({**state, "explanation": explanation})
        session = TeachingSession(
            id=session_id,
            topic=payload.topic,
            explanation=explanation,
            question=state["question"],
            status=SessionStatus.WAITING_FOR_ANSWER,
            attempts=0,
            history=state.get("history", []),
        )
        self._sessions[session.id] = session
        yield {
            "type": "complete",
            "session": session.model_dump(mode="json"),
            "next_action": "answer_question",
        }

    def get(self, session_id: str) -> TeachingSession | None:
        return self._sessions.get(session_id)

    def answer(self, session_id: str, payload: SubmitAnswerRequest) -> SessionResponse:
        session = self._sessions.get(session_id)
        if session is None:
            raise KeyError(session_id)
        if session.status == SessionStatus.MASTERED:
            return SessionResponse(session=session, next_action="complete")
        if session.question is None:
            raise ValueError("Session has no active question")

        state: TutorState = answer_graph.invoke(
            {
                "topic": session.topic,
                "explanation": session.explanation,
                "question": session.question,
                "answer": payload.answer,
                "attempts": session.attempts + 1,
                "history": session.history,
            }
        )
        feedback = state["feedback"]
        if not feedback.mastered and feedback.score >= 0.6 and feedback.strengths:
            feedback = feedback.model_copy(
                update={
                    "mastered": True,
                    "guidance": "已经达到本轮学习目标。仍可根据薄弱点继续补充细节，但不需要重复作答。",
                }
            )
        mastered = feedback.mastered
        updated = session.model_copy(
            update={
                "explanation": state.get("explanation", session.explanation),
                "question": None if mastered else state.get("question", session.question),
                "feedback": feedback,
                "status": SessionStatus.MASTERED if mastered else SessionStatus.WAITING_FOR_ANSWER,
                "attempts": session.attempts + 1,
                "history": state.get("history", session.history),
            }
        )
        self._sessions[session_id] = updated
        return SessionResponse(
            session=updated,
            next_action="complete" if mastered else "review_feedback",
        )

    def answer_stream(self, session_id: str, payload: SubmitAnswerRequest) -> Iterator[dict]:
        session = self._sessions.get(session_id)
        if session is None:
            raise KeyError(session_id)
        if session.status == SessionStatus.MASTERED:
            yield {
                "type": "complete",
                "session": session.model_dump(mode="json"),
                "next_action": "complete",
            }
            return
        if session.question is None:
            raise ValueError("Session has no active question")

        state: TutorState = evaluate_node(
            {
                "topic": session.topic,
                "explanation": session.explanation,
                "question": session.question,
                "answer": payload.answer,
                "attempts": session.attempts + 1,
                "history": session.history,
            }
        )
        feedback = state["feedback"]
        if not feedback.mastered and feedback.score >= 0.6 and feedback.strengths:
            feedback = feedback.model_copy(
                update={
                    "mastered": True,
                    "guidance": "已经达到本轮学习目标。仍可根据薄弱点继续补充细节，但不需要重复作答。",
                }
            )
        yield {"type": "feedback", "feedback": feedback.model_dump(mode="json")}

        if feedback.mastered:
            updated = session.model_copy(
                update={
                    "feedback": feedback,
                    "question": None,
                    "status": SessionStatus.MASTERED,
                    "attempts": session.attempts + 1,
                    "history": state.get("history", session.history),
                }
            )
            self._sessions[session_id] = updated
            yield {
                "type": "complete",
                "session": updated.model_dump(mode="json"),
                "next_action": "complete",
            }
            return

        explanation = ""
        try:
            if deepseek_client.enabled:
                chunks = deepseek_client.chat_text_stream(
                    system=(
                        "你是 TeachAgent 的补救教学节点。请针对学生薄弱点给出引导式讲解，"
                        "帮助学生修正理解，不要直接替学生写最终答案。直接输出讲解正文，不要输出 JSON，"
                        "不要使用 Markdown 标题、加粗符号或代码围栏。"
                    ),
                    user=(
                        "补救讲解应包含：薄弱点定位、容易混淆处、一个更具体的例子、下一轮回答建议。\n\n"
                        f"学习内容：{session.topic}\n\n"
                        f"薄弱点：{state['feedback'].weak_points}\n\n"
                        f"学生上一轮回答：{payload.answer}"
                    ),
                    max_tokens=1600,
                )
            else:
                fallback_state = remediate_node(state)
                chunks = _fallback_chunks(fallback_state["explanation"])

            for chunk in chunks:
                explanation += chunk
                yield {"type": "explanation_delta", "delta": chunk}
        except Exception as exc:
            fallback_state = remediate_node(state)
            explanation = fallback_state["explanation"]
            yield {"type": "notice", "message": f"流式补救调用失败，已切换本地讲解：{exc}"}
            for chunk in _fallback_chunks(explanation):
                yield {"type": "explanation_delta", "delta": chunk}

        history = [*state.get("history", []), {"role": "tutor", "content": explanation}]
        next_state = quiz_node({**state, "explanation": explanation, "history": history})
        updated = session.model_copy(
            update={
                "explanation": explanation,
                "question": next_state["question"],
                "feedback": state["feedback"],
                "status": SessionStatus.WAITING_FOR_ANSWER,
                "attempts": session.attempts + 1,
                "history": next_state.get("history", history),
            }
        )
        self._sessions[session_id] = updated
        yield {
            "type": "complete",
            "session": updated.model_dump(mode="json"),
            "next_action": "review_feedback",
        }
