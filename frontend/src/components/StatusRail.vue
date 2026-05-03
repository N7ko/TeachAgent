<script setup>
import { CircleCheck, Gauge, Layers3, Server } from "lucide-vue-next";

defineProps({
  attempts: {
    type: Number,
    default: 0,
  },
  modelLabel: {
    type: String,
    required: true,
  },
  progressLabel: {
    type: String,
    required: true,
  },
  statusLabel: {
    type: String,
    required: true,
  },
});
</script>

<template>
  <aside class="status-rail">
    <div class="brand-lockup">
      <div class="brand-mark">TA</div>
      <div>
        <strong>TeachAgent</strong>
        <span>Learning Ops</span>
      </div>
    </div>

    <nav class="rail-stack" aria-label="工作台状态">
      <div class="rail-item active">
        <Gauge :size="18" />
        <span>{{ progressLabel }}</span>
      </div>
      <div class="rail-item">
        <CircleCheck :size="18" />
        <span>{{ statusLabel }}</span>
      </div>
      <div class="rail-item">
        <Layers3 :size="18" />
        <span>{{ attempts }} 次提交</span>
      </div>
      <div class="rail-item">
        <Server :size="18" />
        <span>{{ modelLabel }}</span>
      </div>
    </nav>
  </aside>
</template>

