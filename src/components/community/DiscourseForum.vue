<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import {
  getDiscourseBaseUrl,
  useDiscourse,
} from "@/composables/useDiscourse";

const {
  isLoading,
  error,
  topics,
  activeTopic,
  activePosts,
  loadLatest,
  openTopic,
  clearTopic,
  applyApiCredentials,
  clearApiCredentials,
} = useDiscourse();

const baseUrl = computed(() => getDiscourseBaseUrl());
const hasBase = computed(() => Boolean(baseUrl.value));

const showAdvanced = ref(false);
const pastedApiKey = ref("");
const pastedApiUsername = ref("");

function formatWhen(iso: string | null) {
  if (!iso) return "—";
  try {
    const d = new Date(iso);
    if (Number.isNaN(d.getTime())) return iso;
    return d.toLocaleString(undefined, {
      dateStyle: "medium",
      timeStyle: "short",
    });
  } catch {
    return iso;
  }
}

function applyPastedCredentials() {
  applyApiCredentials(pastedApiKey.value, pastedApiUsername.value);
}

function clearPastedCredentials() {
  pastedApiKey.value = "";
  pastedApiUsername.value = "";
  clearApiCredentials();
}

onMounted(() => {
  if (hasBase.value) void loadLatest();
});
</script>

<template>
  <div class="forum">
    <div v-if="!hasBase" class="setup-card" role="status">
      <h2 class="setup-title">Discourse not configured</h2>
      <p class="setup-body">
        Set <code class="code">VITE_DISCOURSE_BASE_URL</code> (forum root, no trailing slash) in
        <code class="code">.env</code> and rebuild. Optional:
        <code class="code">VITE_DISCOURSE_API_KEY</code> and
        <code class="code">VITE_DISCOURSE_API_USERNAME</code> for API access. The Discourse site must
        allow CORS from this app’s origin (or use a same-origin proxy).
      </p>
    </div>

    <template v-else>
      <div class="toolbar">
        <h2 class="panel-title">Forum</h2>
        <div class="toolbar-actions">
          <button
            type="button"
            class="btn"
            :disabled="isLoading"
            @click="loadLatest()"
          >
            Refresh
          </button>
          <button
            type="button"
            class="btn ghost"
            @click="showAdvanced = !showAdvanced"
          >
            {{ showAdvanced ? "Hide" : "Advanced" }}
          </button>
        </div>
      </div>

      <p v-if="error" class="err" role="alert">{{ error }}</p>
      <p v-else-if="isLoading && !activeTopic && topics.length === 0" class="muted">
        Loading topics…
      </p>

      <div v-if="showAdvanced" class="advanced">
        <p class="muted small">
          Prefer defining API credentials in env at build time. You may paste a global or user API key
          and username here for this session only (stored in memory).
        </p>
        <div class="row">
          <input
            v-model="pastedApiUsername"
            class="input"
            type="text"
            autocomplete="off"
            placeholder="API username (Discourse)"
          />
          <input
            v-model="pastedApiKey"
            class="input"
            type="password"
            autocomplete="off"
            placeholder="API key"
          />
        </div>
        <div class="row">
          <button type="button" class="btn" @click="applyPastedCredentials">
            Apply credentials
          </button>
          <button type="button" class="btn ghost" @click="clearPastedCredentials">
            Clear
          </button>
        </div>
      </div>

      <div v-if="activeTopic" class="detail">
        <div class="detail-head">
          <button type="button" class="btn back" @click="clearTopic">
            ← Back to topics
          </button>
          <button
            type="button"
            class="btn ghost"
            :disabled="isLoading"
            @click="openTopic(activeTopic.id)"
          >
            Refresh thread
          </button>
        </div>
        <h3 class="thread-title">{{ activeTopic.title }}</h3>
        <ul class="posts" aria-label="Posts">
          <li v-for="p in activePosts" :key="p.id" class="post">
            <div class="post-meta">
              <span class="author">{{ p.username }}</span>
              <span class="muted">{{ formatWhen(p.created_at) }}</span>
            </div>
            <div class="cooked" v-html="p.cooked" />
          </li>
        </ul>
      </div>

      <div v-else class="list-wrap">
        <ul class="topic-list" aria-label="Latest topics">
          <li v-for="t in topics" :key="t.id">
            <button type="button" class="topic-row" @click="openTopic(t.id)">
              <span class="topic-title">{{ t.title }}</span>
              <span class="topic-meta muted">
                {{ t.replyCount }} repl{{ t.replyCount === 1 ? "y" : "ies" }} ·
                {{ formatWhen(t.lastActivity) }}
              </span>
            </button>
          </li>
        </ul>
      </div>
    </template>
  </div>
</template>

<style scoped>
.forum {
  display: flex;
  flex-direction: column;
  gap: 14px;
  color: var(--txt);
  min-height: 0;
}

.setup-card {
  border: 1px dashed var(--b2);
  border-radius: 10px;
  padding: 18px;
  background: rgba(0, 0, 0, 0.03);
}

.setup-title {
  margin: 0 0 8px;
  font-size: 18px;
  font-weight: 700;
  color: var(--txt);
}

.setup-body {
  margin: 0;
  font-size: 14px;
  line-height: 1.5;
  color: var(--muted);
}

.code {
  font-size: 0.9em;
  padding: 1px 6px;
  border-radius: 4px;
  border: 1px solid var(--b2);
  background: var(--bg);
  color: var(--txt);
}

.toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  flex-wrap: wrap;
}

.panel-title {
  margin: 0;
  font-size: 18px;
  font-weight: 700;
  color: var(--txt);
}

.toolbar-actions {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.btn {
  padding: 8px 14px;
  border-radius: 8px;
  border: 1px solid var(--b);
  background: var(--bg);
  color: var(--txt);
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  font-family: inherit;
  transition: border-color 0.2s ease, background 0.2s ease;
}

.btn:hover:not(:disabled) {
  border-color: var(--b2);
  background: rgba(255, 255, 255, 0.06);
}

.btn:disabled {
  opacity: 0.55;
  cursor: not-allowed;
}

.btn.ghost {
  border-color: var(--b2);
  color: var(--muted);
}

.btn.back {
  align-self: flex-start;
}

.err {
  margin: 0;
  color: #c45c5c;
  font-size: 14px;
}

.muted {
  color: var(--muted);
}

.small {
  font-size: 13px;
  margin: 0 0 8px;
}

.advanced {
  border: 1px solid var(--b2);
  border-radius: 10px;
  padding: 12px;
  background: rgba(0, 0, 0, 0.02);
}

.row {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-top: 8px;
}

.input {
  flex: 1;
  min-width: 160px;
  padding: 8px 10px;
  border-radius: 8px;
  border: 1px solid var(--b2);
  background: var(--bg);
  color: var(--txt);
  font-size: 14px;
  font-family: inherit;
}

.detail-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  flex-wrap: wrap;
}

.thread-title {
  margin: 10px 0 14px;
  font-size: 20px;
  font-weight: 800;
  line-height: 1.25;
  color: var(--txt);
}

.posts {
  list-style: none;
  margin: 0;
  padding: 0;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.post {
  border: 1px solid var(--b);
  border-radius: 10px;
  padding: 12px 14px;
  background: rgba(0, 0, 0, 0.02);
}

.post-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  align-items: baseline;
  margin-bottom: 8px;
  font-size: 13px;
}

.author {
  font-weight: 700;
  color: var(--txt);
}

/* Cooked HTML from Discourse */
.cooked :deep(p) {
  margin: 0 0 0.65em;
  line-height: 1.5;
  color: var(--txt);
}

.cooked :deep(a) {
  color: var(--txt);
  text-decoration: underline;
  text-underline-offset: 2px;
}

.cooked :deep(img) {
  max-width: 100%;
  height: auto;
  border-radius: 6px;
}

.cooked :deep(blockquote) {
  margin: 0.5em 0;
  padding-left: 12px;
  border-left: 3px solid var(--b2);
  color: var(--muted);
}

.topic-list {
  list-style: none;
  margin: 0;
  padding: 0;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.topic-row {
  width: 100%;
  text-align: left;
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: 4px;
  padding: 12px 14px;
  border-radius: 10px;
  border: 1px solid var(--b);
  background: var(--bg);
  color: var(--txt);
  cursor: pointer;
  font-family: inherit;
  transition: border-color 0.2s ease, background 0.2s ease;
}

.topic-row:hover {
  border-color: var(--b2);
  background: rgba(255, 255, 255, 0.04);
}

.topic-title {
  font-size: 15px;
  font-weight: 650;
  line-height: 1.35;
}

.topic-meta {
  font-size: 13px;
}
</style>
