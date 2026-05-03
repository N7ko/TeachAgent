<script setup>
import {
  Activity,
  BookOpenCheck,
  Brain,
  ClipboardCheck,
  FileText,
  RotateCcw,
  Send,
  Sparkles,
} from "lucide-vue-next";

import FeedbackPanel from "../components/FeedbackPanel.vue";
import LearningPanel from "../components/LearningPanel.vue";
import SessionComposer from "../components/SessionComposer.vue";
import StatusRail from "../components/StatusRail.vue";
import { sampleTopics } from "../constants/sampleTopics";
import { useTutorSession } from "../composables/useTutorSession";
import { statusText } from "../utils/format";

const tutor = useTutorSession();

function useSampleTopic(value) {
  tutor.topic.value = value;
}
</script>

<template>
  <main class="app-shell">
    <StatusRail
      :attempts="tutor.session.value?.attempts ?? 0"
      :model-label="'DeepSeek V4'"
      :progress-label="tutor.progressLabel.value"
      :status-label="statusText(tutor.session.value?.status)"
    />

    <section class="workbench">
      <header class="command-header">
        <div class="title-block">
          <p class="kicker"><Sparkles :size="15" /> TeachAgent Enterprise</p>
          <h1>知识掌握闭环工作台</h1>
        </div>
        <div class="header-metrics">
          <div class="metric">
            <Activity :size="17" />
            <span>{{ tutor.progressLabel.value }}</span>
          </div>
          <div class="metric strong">
            <Brain :size="17" />
            <span>{{ tutor.masteryPercent.value }}%</span>
          </div>
        </div>
      </header>

      <section class="control-strip">
        <SessionComposer
          v-model="tutor.topic.value"
          :disabled="tutor.loading.value"
          :has-session="Boolean(tutor.session.value)"
          @reset="tutor.resetSession"
          @submit="tutor.startSession"
        />

        <aside class="sample-bank" aria-label="示例主题">
          <div class="sample-bank__head">
            <FileText :size="17" />
            <span>快速载入</span>
          </div>
          <button
            v-for="item in sampleTopics"
            :key="item"
            type="button"
            class="sample-chip"
            @click="useSampleTopic(item)"
          >
            {{ item }}
          </button>
        </aside>
      </section>

      <p v-if="tutor.error.value" class="error-banner">{{ tutor.error.value }}</p>

      <section class="learning-layout" :class="{ empty: !tutor.session.value }">
        <template v-if="tutor.session.value">
          <LearningPanel
            :answer="tutor.answer.value"
            :is-mastered="tutor.isMastered.value"
            :loading="tutor.loading.value"
            :session="tutor.session.value"
            :streaming="tutor.streaming.value"
            @submit="tutor.submitAnswer"
            @update:answer="tutor.answer.value = $event"
          />

          <FeedbackPanel
            :feedback="tutor.session.value.feedback"
            :mastery-percent="tutor.masteryPercent.value"
          />
        </template>

        <article v-else class="empty-state">
          <div class="empty-state__mark">
            <BookOpenCheck :size="44" />
          </div>
          <div>
            <p class="eyebrow-line">Ready</p>
            <h2>输入一个专业概念，系统会生成讲解、检测题和补救路径。</h2>
            <p>
              工作台会保留每轮判断结果，直到学生答案覆盖关键要点并通过掌握检测。
            </p>
          </div>
        </article>
      </section>

      <footer class="workspace-footer">
        <span><ClipboardCheck :size="15" /> Explain -> Test -> Diagnose -> Remediate</span>
        <button type="button" class="ghost-action" @click="tutor.resetSession">
          <RotateCcw :size="15" />
          重置工作台
        </button>
      </footer>
    </section>
  </main>
</template>
