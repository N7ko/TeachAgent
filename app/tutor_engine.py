import re
from collections.abc import Callable
from typing import Any, Literal, TypedDict

from app.deepseek_client import deepseek_client
from app.models import Feedback, QuizQuestion

try:
    from langgraph.graph import END, StateGraph
except Exception:  # pragma: no cover - used only when dependencies are not installed yet.
    END = "__end__"
    StateGraph = None


class TutorState(TypedDict, total=False):
    topic: str
    explanation: str
    question: QuizQuestion
    answer: str
    feedback: Feedback
    attempts: int
    history: list[dict[str, str]]


def _keywords(text: str) -> list[str]:
    words = re.findall(r"[A-Za-z][A-Za-z0-9_+\-#]*|[\u4e00-\u9fff]{2,}", text.lower())
    stop_words = {"这个", "一种", "可以", "需要", "学生", "知识", "进行", "相关", "理解"}
    result: list[str] = []
    for word in words:
        if word in stop_words or len(word) < 2:
            continue
        if word not in result:
            result.append(word)
    return result[:8]


def _topic_label(topic: str) -> str:
    compact = " ".join(topic.strip().split())
    return compact[:80]


def explain_node(state: TutorState) -> TutorState:
    if deepseek_client.enabled:
        try:
            data = deepseek_client.chat_json(
                system=(
                    "你是 TeachAgent 的专业课程助教。请用中文生成教学解释，要求准确、结构化、"
                    "面向学生理解，不要编造来源。必须只输出 JSON。"
                ),
                user=(
                    "请解释下面的关键词或文本。JSON schema: "
                    '{"explanation": "string"}。解释应包含定义、作用、关键机制、应用场景，'
                    "并控制在 500 到 900 字。\n\n"
                    f"学习内容：{state['topic']}"
                ),
                max_tokens=1800,
            )
            explanation = str(data["explanation"]).strip()
            if explanation:
                return {**state, "explanation": explanation}
        except Exception as exc:
            history = [*state.get("history", []), {"role": "system", "content": f"DeepSeek explain fallback: {exc}"}]
            state = {**state, "history": history}

    topic = _topic_label(state["topic"])
    key_terms = _keywords(topic)
    focus = "、".join(key_terms[:4]) if key_terms else topic
    explanation = (
        f"{topic} 可以先理解为一个需要拆成“定义、作用、关键机制、应用场景”四部分掌握的概念。\n\n"
        f"1. 定义：先说清它是什么，以及它和相近概念的边界。\n"
        f"2. 作用：说明它解决了什么问题，为什么有必要学习它。\n"
        f"3. 关键机制：围绕 {focus} 这些核心点解释它如何工作。\n"
        f"4. 应用：用一个真实场景说明它在专业问题中怎样被使用。\n\n"
        f"如果你能用自己的话解释上述四点，并举出一个例子，就基本掌握了这个知识点。"
    )
    return {**state, "explanation": explanation}


def quiz_node(state: TutorState) -> TutorState:
    if deepseek_client.enabled:
        try:
            weak_points = state.get("feedback").weak_points if state.get("feedback") else []
            data = deepseek_client.chat_json(
                system=(
                    "你是 TeachAgent 的测评出题节点。请基于讲解内容生成一道开放题，"
                    "用于判断学生是否真正理解概念。必须只输出 JSON。"
                ),
                user=(
                    "JSON schema: "
                    '{"prompt": "string", "expected_points": ["string"]}。'
                    "expected_points 给 4 到 6 个可评估要点。"
                    "如果存在薄弱点，请优先针对薄弱点追问。\n\n"
                    f"学习内容：{state['topic']}\n\n"
                    f"当前讲解：{state.get('explanation', '')}\n\n"
                    f"薄弱点：{weak_points}"
                ),
                max_tokens=1000,
            )
            expected_points = [str(item).strip() for item in data.get("expected_points", []) if str(item).strip()]
            question = QuizQuestion(prompt=str(data["prompt"]).strip(), expected_points=expected_points[:6])
            if question.prompt and question.expected_points:
                return {**state, "question": question}
        except Exception as exc:
            history = [*state.get("history", []), {"role": "system", "content": f"DeepSeek quiz fallback: {exc}"}]
            state = {**state, "history": history}

    topic = _topic_label(state["topic"])
    expected_points = [
        "给出清晰定义",
        "说明它解决的问题或作用",
        "描述关键机制或组成要素",
        "给出一个具体例子",
    ]
    question = QuizQuestion(
        prompt=(
            f"请不用照抄上面的说明，用自己的话解释“{topic}”。"
            "你的回答需要包含：定义、作用、关键机制，以及一个具体例子。"
        ),
        expected_points=expected_points,
    )
    return {**state, "question": question}


def evaluate_node(state: TutorState) -> TutorState:
    if deepseek_client.enabled:
        try:
            data = deepseek_client.chat_json(
                system=(
                    "你是 TeachAgent 的学习评估节点。请以教学促进为目标判断学生是否基本掌握，"
                    "不要用考试满分标准要求学生。若学生能说清核心定义、主要作用和关键机制，"
                    "即使例子不够完美也可以判定掌握。必须只输出 JSON。"
                ),
                user=(
                    "JSON schema: "
                    '{"mastered": true, "score": 0.0, "strengths": ["string"], '
                    '"weak_points": ["string"], "guidance": "string"}。'
                    "score 取 0 到 1；mastered 在 score >= 0.6 且核心概念没有明显错误时可为 true。"
                    "如果只是细节不完整，不要要求学生反复重答；guidance 可以给补充建议。\n\n"
                    f"学习内容：{state['topic']}\n\n"
                    f"讲解：{state.get('explanation', '')}\n\n"
                    f"题目：{state['question'].prompt}\n"
                    f"期望要点：{state['question'].expected_points}\n\n"
                    f"学生回答：{state.get('answer', '')}"
                ),
                max_tokens=1400,
            )
            score = max(0.0, min(1.0, float(data.get("score", 0))))
            feedback = Feedback(
                mastered=bool(data.get("mastered")) and score >= 0.6,
                score=score,
                strengths=[str(item).strip() for item in data.get("strengths", []) if str(item).strip()],
                weak_points=[str(item).strip() for item in data.get("weak_points", []) if str(item).strip()],
                guidance=str(data.get("guidance", "")).strip() or "请补充关键定义、机制和例子。",
            )
            history = [*state.get("history", []), {"role": "student", "content": state.get("answer", "").strip()}]
            return {**state, "feedback": feedback, "history": history}
        except Exception as exc:
            history = [*state.get("history", []), {"role": "system", "content": f"DeepSeek evaluate fallback: {exc}"}]
            state = {**state, "history": history}

    answer = state.get("answer", "").strip()
    lower_answer = answer.lower()
    expected_points = state["question"].expected_points
    checks = {
        "给出清晰定义": any(token in lower_answer for token in ["是", "指", "定义", "means", "refers"]),
        "说明它解决的问题或作用": any(token in lower_answer for token in ["作用", "解决", "用于", "帮助", "why", "purpose"]),
        "描述关键机制或组成要素": any(token in lower_answer for token in ["机制", "过程", "步骤", "组成", "原理", "how"]),
        "给出一个具体例子": any(token in lower_answer for token in ["例如", "比如", "场景", "例子", "for example"]),
    }
    strengths = [point for point in expected_points if checks.get(point)]
    weak_points = [point for point in expected_points if not checks.get(point)]
    score = len(strengths) / len(expected_points)
    mastered = score >= 0.5 and len(answer) >= 24
    guidance = (
        "回答已经覆盖核心结构，可以进入下一个知识点。"
        if mastered
        else "还没有完全掌握。请补充缺失部分，尤其要把概念边界、工作机制和例子说具体。"
    )
    feedback = Feedback(
        mastered=mastered,
        score=score,
        strengths=strengths,
        weak_points=weak_points,
        guidance=guidance,
    )
    history = [*state.get("history", []), {"role": "student", "content": answer}]
    return {**state, "feedback": feedback, "history": history}


def remediate_node(state: TutorState) -> TutorState:
    if deepseek_client.enabled:
        try:
            data = deepseek_client.chat_json(
                system=(
                    "你是 TeachAgent 的补救教学节点。请针对学生薄弱点给出引导式讲解，"
                    "帮助学生修正理解，不要直接替学生写最终答案。必须只输出 JSON。"
                ),
                user=(
                    'JSON schema: {"explanation": "string"}。'
                    "补救讲解应包含：薄弱点定位、容易混淆处、一个更具体的例子、下一轮回答建议。\n\n"
                    f"学习内容：{state['topic']}\n\n"
                    f"薄弱点：{state['feedback'].weak_points}\n\n"
                    f"学生上一轮回答：{state.get('answer', '')}"
                ),
                max_tokens=1600,
            )
            explanation = str(data["explanation"]).strip()
            if explanation:
                history = [*state.get("history", []), {"role": "tutor", "content": explanation}]
                return {**state, "explanation": explanation, "history": history}
        except Exception as exc:
            history = [*state.get("history", []), {"role": "system", "content": f"DeepSeek remediate fallback: {exc}"}]
            state = {**state, "history": history}

    weak_points = state["feedback"].weak_points
    topic = _topic_label(state["topic"])
    missing = "、".join(weak_points) if weak_points else "表达的完整性"
    explanation = (
        f"针对“{topic}”，你现在主要薄弱在：{missing}。\n\n"
        "可以按这个模板重新组织答案：\n"
        f"- 它是什么：用一句话给出“{topic}”的定义。\n"
        "- 为什么重要：说明它解决的问题。\n"
        "- 它怎么工作：按 2 到 3 个步骤讲清机制。\n"
        "- 怎么使用：放到一个具体场景中举例。\n\n"
        "下一次回答时，不需要更长，但要让每一句都对应一个明确要点。"
    )
    history = [*state.get("history", []), {"role": "tutor", "content": explanation}]
    return {**state, "explanation": explanation, "history": history}


def finish_node(state: TutorState) -> TutorState:
    return state


def route_after_evaluation(state: TutorState) -> Literal["finish", "remediate"]:
    return "finish" if state["feedback"].mastered else "remediate"


class _FallbackGraph:
    def __init__(self, nodes: list[Callable[[TutorState], TutorState]]) -> None:
        self.nodes = nodes

    def invoke(self, state: TutorState) -> TutorState:
        next_state = state
        for node in self.nodes:
            next_state = node(next_state)
        return next_state


def build_start_graph() -> Any:
    if StateGraph is None:
        return _FallbackGraph([explain_node, quiz_node])
    graph = StateGraph(TutorState)
    graph.add_node("explain", explain_node)
    graph.add_node("quiz", quiz_node)
    graph.set_entry_point("explain")
    graph.add_edge("explain", "quiz")
    graph.add_edge("quiz", END)
    return graph.compile()


def build_answer_graph() -> Any:
    if StateGraph is None:
        return _FallbackGraph([evaluate_node])
    graph = StateGraph(TutorState)
    graph.add_node("evaluate", evaluate_node)
    graph.add_node("remediate", remediate_node)
    graph.add_node("quiz", quiz_node)
    graph.add_node("finish", finish_node)
    graph.set_entry_point("evaluate")
    graph.add_conditional_edges("evaluate", route_after_evaluation)
    graph.add_edge("remediate", "quiz")
    graph.add_edge("quiz", END)
    graph.add_edge("finish", END)
    return graph.compile()


start_graph = build_start_graph()
answer_graph = build_answer_graph()
