import { computed, ref } from "vue";

import { createSessionStream, submitSessionAnswerStream } from "../api/sessions";

export function useTutorSession() {
  const topic = ref("");
  const answer = ref("");
  const session = ref(null);
  const loading = ref(false);
  const streaming = ref(false);
  const error = ref("");

  const progressLabel = computed(() => {
    if (!session.value) return "未开始";
    if (session.value.status === "mastered") return "已掌握";
    return `第 ${session.value.attempts + 1} 轮检测`;
  });

  const masteryPercent = computed(() => {
    if (!session.value?.feedback) return 0;
    return Math.round(session.value.feedback.score * 100);
  });

  const isMastered = computed(() => session.value?.status === "mastered");

  async function startSession() {
    if (!topic.value.trim()) {
      error.value = "请输入关键词或粘贴一段文本。";
      return;
    }

    loading.value = true;
    streaming.value = true;
    error.value = "";
    answer.value = "";
    session.value = {
      id: "streaming",
      topic: topic.value.trim(),
      explanation: "",
      question: null,
      feedback: null,
      status: "teaching",
      attempts: 0,
      history: [],
    };
    try {
      await createSessionStream(topic.value.trim(), (event) => {
        if (event.type === "session_started") {
          session.value.id = event.session_id;
        }
        if (event.type === "explanation_delta") {
          session.value.explanation += event.delta;
        }
        if (event.type === "notice") {
          error.value = event.message;
        }
        if (event.type === "complete") {
          session.value = event.session;
        }
        if (event.type === "error") {
          throw new Error(event.message);
        }
      });
    } catch (err) {
      error.value = err.message;
      session.value = null;
    } finally {
      loading.value = false;
      streaming.value = false;
    }
  }

  async function submitAnswer() {
    if (!answer.value.trim() || !session.value) {
      error.value = "请先填写你的回答。";
      return;
    }

    loading.value = true;
    streaming.value = true;
    error.value = "";
    let receivedRemediation = false;
    try {
      await submitSessionAnswerStream(session.value.id, answer.value.trim(), (event) => {
        if (event.type === "feedback") {
          session.value = {
            ...session.value,
            feedback: event.feedback,
          };
        }
        if (event.type === "explanation_delta") {
          if (!receivedRemediation) {
            session.value.explanation = "";
            receivedRemediation = true;
          }
          session.value.explanation += event.delta;
        }
        if (event.type === "notice") {
          error.value = event.message;
        }
        if (event.type === "complete") {
          session.value = event.session;
        }
        if (event.type === "error") {
          throw new Error(event.message);
        }
      });
      answer.value = "";
    } catch (err) {
      error.value = err.message;
    } finally {
      loading.value = false;
      streaming.value = false;
    }
  }

  function resetSession() {
    session.value = null;
    answer.value = "";
    error.value = "";
  }

  return {
    answer,
    error,
    isMastered,
    loading,
    masteryPercent,
    progressLabel,
    resetSession,
    session,
    startSession,
    streaming,
    submitAnswer,
    topic,
  };
}
