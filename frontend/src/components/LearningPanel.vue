<script setup>
import { CheckCircle2, FileQuestion, Send, ShieldCheck } from "lucide-vue-next";

defineProps({
  answer: {
    type: String,
    required: true,
  },
  isMastered: {
    type: Boolean,
    default: false,
  },
  loading: {
    type: Boolean,
    default: false,
  },
  session: {
    type: Object,
    required: true,
  },
  streaming: {
    type: Boolean,
    default: false,
  },
});

defineEmits(["submit", "update:answer"]);
</script>

<template>
  <section class="learning-panel">
    <article class="content-card explanation-card">
      <div class="card-header">
        <div>
          <span class="section-index">02</span>
          <h2>模型讲解</h2>
        </div>
        <span class="topic-pill">{{ streaming ? "流式生成中" : session.topic }}</span>
      </div>
      <p class="rich-text stream-text" :class="{ streaming }">
        {{ session.explanation || "正在连接教学模型..." }}
      </p>
    </article>

    <article class="content-card assessment-card">
      <div class="card-header">
        <div>
          <span class="section-index">03</span>
          <h2>掌握检测</h2>
        </div>
        <FileQuestion :size="20" />
      </div>

      <template v-if="!isMastered">
        <div v-if="session.question?.prompt" class="question-card">
          <div class="question-card__main">
            <span class="question-label">检测任务</span>
            <p>{{ session.question.prompt }}</p>
          </div>
          <div class="question-points">
            <span>回答时可覆盖</span>
            <ul>
              <li v-for="point in session.question.expected_points" :key="point">{{ point }}</li>
            </ul>
          </div>
        </div>
        <p v-else class="question-copy muted">讲解生成完成后，系统会继续生成掌握检测题。</p>
        <textarea
          :value="answer"
          class="answer-box"
          rows="8"
          placeholder="用自己的话作答，覆盖定义、作用、机制和例子。"
          :disabled="streaming || !session.question"
          @input="$emit('update:answer', $event.target.value)"
        />
        <button
          class="primary-action"
          type="button"
          :disabled="loading || streaming || !session.question"
          @click="$emit('submit')"
        >
          <Send :size="16" />
          {{ streaming ? "生成中" : "提交检测" }}
        </button>
      </template>

      <div v-else class="mastery-card">
        <CheckCircle2 :size="28" />
        <div>
          <strong>掌握检测通过</strong>
          <p>学生答案已经覆盖关键要点，可以结束本轮学习。</p>
        </div>
        <ShieldCheck :size="22" />
      </div>
    </article>
  </section>
</template>
