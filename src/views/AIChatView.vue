<script setup lang="ts">
import type { UIMessage } from "ai";
import { computed, ref } from "vue";
import { useChat } from "@/composables/useChat";

const { messages, status, error, sendMessage, stop } = useChat();
const input = ref("");

const isReady = computed(() => status.value === "ready");
const isStreaming = computed(
  () => status.value === "submitted" || status.value === "streaming"
);
const hasError = computed(() => !!error.value);

function handleSubmit(e?: Event) {
  e?.preventDefault();
  const text = input.value.trim();
  if (!text || !isReady.value) return;
  input.value = "";
  sendMessage({ text });
}

function getMessageText(msg: UIMessage) {
  return msg.parts
    .filter((p): p is { type: "text"; text: string } => p.type === "text")
    .map((p) => p.text)
    .join("");
}
</script>

<template>
  <div class="ai-chat-view">
    <!-- Scrollable message area -->
    <div class="chat-messages">
      <div
        v-for="msg in messages"
        :key="msg.id"
        :class="['chat-bubble', msg.role === 'user' ? 'chat-bubble-user' : 'chat-bubble-assistant']"
      >
        <span class="chat-bubble-label">{{ msg.role === "user" ? "You" : "Current" }}</span>
        <div class="chat-bubble-content">
          {{ getMessageText(msg) }}
        </div>
      </div>
      <div v-if="messages.length === 0" class="chat-empty">
        <p class="chat-empty-text">Ask the Current anything about Daoist astrology or herbal alchemy.</p>
      </div>
    </div>

    <!-- Error state -->
    <div v-if="hasError" class="chat-error">
      <p>Something went wrong. Please try again.</p>
    </div>

    <!-- Sticky input area -->
    <div class="chat-input-area">
      <form class="chat-input-form" @submit="handleSubmit">
        <input
          v-model="input"
          type="text"
          class="chat-input"
          placeholder="Ask about your chart, formulas..."
          :disabled="!isReady"
          autocomplete="off"
        />
        <div class="chat-actions">
          <button
            v-if="isStreaming"
            type="button"
            class="chat-btn chat-btn-stop"
            @click="stop"
          >
            Stop
          </button>
          <button
            type="submit"
            class="chat-btn chat-btn-send"
            :disabled="!input.trim() || !isReady"
          >
            Send
          </button>
        </div>
      </form>
    </div>
  </div>
</template>

<style scoped>
.ai-chat-view {
  display: flex;
  flex-direction: column;
  min-height: calc(100vh - 120px);
  min-height: calc(100dvh - 120px);
  padding-bottom: env(safe-area-inset-bottom, 0);
}

.chat-messages {
  flex: 1;
  overflow-y: auto;
  padding: 16px;
  padding-bottom: 8px;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.chat-empty {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 24px;
}

.chat-empty-text {
  color: var(--color-daoist-muted);
  font-size: 15px;
  text-align: center;
  max-width: 280px;
}

.chat-bubble {
  max-width: 88%;
  align-self: flex-start;
  padding: 12px 16px;
  border-radius: 12px;
  word-wrap: break-word;
}

.chat-bubble-user {
  align-self: flex-end;
  background: rgba(26, 36, 53, 0.9);
  border: 1px solid rgba(255, 255, 255, 0.06);
  color: var(--color-daoist-text);
}

.chat-bubble-assistant {
  background: var(--color-daoist-surface);
  border-left: 4px solid var(--color-daoist-jade);
  color: var(--color-daoist-text);
}

.chat-bubble-label {
  display: block;
  font-size: 11px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: var(--color-daoist-muted);
  margin-bottom: 6px;
}

.chat-bubble-assistant .chat-bubble-label {
  color: var(--color-daoist-jade-muted);
}

.chat-bubble-content {
  font-size: 15px;
  line-height: 1.5;
  white-space: pre-wrap;
}

.chat-error {
  padding: 12px 16px;
  margin: 0 16px;
  background: rgba(180, 60, 60, 0.15);
  border: 1px solid rgba(180, 60, 60, 0.3);
  border-radius: 8px;
  color: #e88;
  font-size: 14px;
}

.chat-input-area {
  position: sticky;
  bottom: 0;
  padding: 12px 16px;
  padding-bottom: calc(12px + env(safe-area-inset-bottom, 0px));
  background: var(--color-daoist-bg);
  border-top: 1px solid rgba(255, 255, 255, 0.08);
}

.chat-input-form {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.chat-input {
  width: 100%;
  padding: 12px 16px;
  font-size: 16px;
  color: var(--color-daoist-text);
  background: var(--color-daoist-surface);
  border: 1px solid rgba(255, 255, 255, 0.12);
  border-radius: 10px;
  outline: none;
  transition: border-color 0.2s;
}

.chat-input::placeholder {
  color: var(--color-daoist-muted);
}

.chat-input:focus {
  border-color: var(--color-daoist-jade-muted);
}

.chat-input:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.chat-actions {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
}

.chat-btn {
  padding: 10px 20px;
  font-size: 14px;
  font-weight: 500;
  border-radius: 8px;
  cursor: pointer;
  transition: background-color 0.2s, border-color 0.2s;
}

.chat-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.chat-btn-send {
  background: var(--color-daoist-jade);
  color: #0d1520;
  border: none;
}

.chat-btn-send:hover:not(:disabled) {
  background: var(--color-daoist-jade-muted);
}

.chat-btn-stop {
  background: transparent;
  color: var(--color-daoist-gold);
  border: 1px solid var(--color-daoist-gold-muted);
}

.chat-btn-stop:hover {
  background: rgba(201, 162, 39, 0.15);
}
</style>
