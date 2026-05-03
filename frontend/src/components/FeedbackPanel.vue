<script setup>
import { AlertTriangle, Check, LineChart, Target } from "lucide-vue-next";

defineProps({
  feedback: {
    type: Object,
    default: null,
  },
  masteryPercent: {
    type: Number,
    default: 0,
  },
});
</script>

<template>
  <aside class="feedback-panel">
    <div class="feedback-score">
      <LineChart :size="20" />
      <span>掌握度</span>
      <strong>{{ masteryPercent }}%</strong>
    </div>

    <template v-if="feedback">
      <section class="diagnosis-block">
        <div class="diagnosis-head">
          <Target :size="18" />
          <h2>诊断建议</h2>
        </div>
        <p>{{ feedback.guidance }}</p>
      </section>

      <section class="list-block covered">
        <h3><Check :size="16" /> 已覆盖</h3>
        <ul>
          <li v-for="item in feedback.strengths" :key="item">{{ item }}</li>
          <li v-if="feedback.strengths.length === 0">暂无明确覆盖点</li>
        </ul>
      </section>

      <section class="list-block weak">
        <h3><AlertTriangle :size="16" /> 薄弱点</h3>
        <ul>
          <li v-for="item in feedback.weak_points" :key="item">{{ item }}</li>
          <li v-if="feedback.weak_points.length === 0">暂无薄弱点</li>
        </ul>
      </section>
    </template>

    <section v-else class="diagnosis-block muted">
      <div class="diagnosis-head">
        <Target :size="18" />
        <h2>等待评估</h2>
      </div>
      <p>提交学生回答后，这里会展示掌握度、已覆盖点和下一轮补救方向。</p>
    </section>
  </aside>
</template>

