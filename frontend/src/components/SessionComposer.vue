<script setup>
import { Play, RotateCcw } from "lucide-vue-next";

defineProps({
  disabled: {
    type: Boolean,
    default: false,
  },
  hasSession: {
    type: Boolean,
    default: false,
  },
  modelValue: {
    type: String,
    required: true,
  },
});

defineEmits(["reset", "submit", "update:modelValue"]);
</script>

<template>
  <form class="composer" @submit.prevent="$emit('submit')">
    <div class="composer__head">
      <div>
        <span class="section-index">01</span>
        <h2>学习输入</h2>
      </div>
      <p>支持关键词、专业术语或课堂文本片段。</p>
    </div>

    <textarea
      :value="modelValue"
      class="composer__textarea"
      rows="7"
      placeholder="例如：Transformer 的自注意力机制"
      @input="$emit('update:modelValue', $event.target.value)"
    />

    <div class="composer__actions">
      <button class="primary-action" type="submit" :disabled="disabled">
        <Play :size="16" />
        {{ hasSession ? "重新生成" : "开始教学" }}
      </button>
      <button v-if="hasSession" class="secondary-action" type="button" @click="$emit('reset')">
        <RotateCcw :size="16" />
        清空
      </button>
    </div>
  </form>
</template>

