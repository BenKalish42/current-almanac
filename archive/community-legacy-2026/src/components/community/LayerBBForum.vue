<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import { useLayerBB } from "@/composables/useLayerBB";

const {
  apiBase,
  isAuthenticated,
  isLoading,
  error,
  categories,
  threads,
  activeThread,
  login,
  logout,
  fetchCategories,
  fetchRecentThreads,
  fetchThreadDetail,
  clearActiveThread,
  loadArchivesHome,
} = useLayerBB();

const tokenInput = ref("");

const hasConfig = computed(() => !!apiBase.value.replace(/\/$/, ""));

onMounted(() => {
  if (hasConfig.value) void loadArchivesHome();
});

function applyToken() {
  const t = tokenInput.value.trim();
  if (!t) return;
  login(t);
  tokenInput.value = "";
  void loadArchivesHome();
}

function disconnect() {
  logout();
  void loadArchivesHome();
}

async function openThread(id: string) {
  await fetchThreadDetail(id);
}

function backToList() {
  clearActiveThread();
}

const filteredThreads = computed(() => {
  const cat = selectedCategoryId.value;
  if (!cat) return threads.value;
  return threads.value.filter((t) => t.categoryId === cat || !t.categoryId);
});

const selectedCategoryId = ref<string | null>(null);

function selectCategory(id: string | null) {
  selectedCategoryId.value = id;
}
</script>

<template>
  <div class="layerbb-forum">
    <div v-if="!hasConfig" class="setup-card">
      <h2 class="section-title">The Archives (LayerBB)</h2>
      <p class="muted">
        Set <code class="code">VITE_LAYERBB_API_URL</code> in <code class="code">.env</code> to your LayerBB API root (no trailing slash), e.g.
        <code class="code">https://forum.example.com/api/v1</code>. Restart the dev server, then return here.
      </p>
      <p class="muted small">
        Expected JSON routes (adjust your reverse proxy or LayerBB routes to match):
        <code class="code">GET /categories</code>,
        <code class="code">GET /threads?limit=30</code>,
        <code class="code">GET /threads/:id</code>
      </p>
    </div>

    <template v-else>
      <div class="feed-header">
        <h2 class="title">The Archives (LayerBB)</h2>
        <p class="tagline">Structured forum — categories, threads, and replies</p>
        <div class="auth-section">
          <span class="base-pill" :title="apiBase">{{ apiBase }}</span>
          <input
            v-if="!isAuthenticated"
            v-model="tokenInput"
            class="input token-input"
            type="password"
            autocomplete="off"
            placeholder="Bearer token (optional; or use VITE_LAYERBB_BEARER_TOKEN)"
            @keyup.enter="applyToken"
          />
          <button v-if="!isAuthenticated" type="button" class="btn primary" @click="applyToken">
            Save token
          </button>
          <template v-else>
            <span class="auth-status">Token active</span>
            <button type="button" class="btn" @click="disconnect">Reset token to .env</button>
          </template>
          <button type="button" class="btn" :disabled="isLoading" @click="() => void loadArchivesHome()">
            Refresh all
          </button>
          <button type="button" class="btn" :disabled="isLoading" @click="() => void fetchCategories()">
            Categories
          </button>
          <button type="button" class="btn" :disabled="isLoading" @click="() => void fetchRecentThreads()">
            Threads
          </button>
        </div>
      </div>

      <div v-if="error" class="error-msg">{{ error }}</div>

      <div v-if="activeThread" class="thread-detail">
        <button type="button" class="btn back-btn" @click="backToList">← Back to list</button>
        <h3 class="thread-title">{{ activeThread.title }}</h3>
        <div v-if="isLoading" class="muted">Loading…</div>
        <ul v-else class="post-list">
          <li v-for="p in activeThread.posts" :key="p.id" class="post-card">
            <div class="post-meta">
              <span class="post-author">{{ p.author }}</span>
              <span v-if="p.createdAt" class="post-date">{{ p.createdAt }}</span>
            </div>
            <div class="post-body" v-html="p.body"></div>
          </li>
        </ul>
        <p v-if="!isLoading && activeThread.posts.length === 0" class="muted">No posts returned for this thread.</p>
      </div>

      <div v-else class="archives-grid">
        <aside v-if="categories.length" class="categories-panel">
          <div class="panel-head">Categories</div>
          <button
            type="button"
            class="cat-chip"
            :class="{ active: selectedCategoryId === null }"
            @click="selectCategory(null)"
          >
            All
          </button>
          <button
            v-for="c in categories"
            :key="c.id"
            type="button"
            class="cat-chip"
            :class="{ active: selectedCategoryId === c.id }"
            @click="selectCategory(c.id)"
          >
            {{ c.name }}
          </button>
        </aside>

        <div class="threads-panel">
          <div class="panel-head">Recent threads</div>
          <div v-if="isLoading && !threads.length" class="muted padded">Loading…</div>
          <ul v-else class="thread-list">
            <li
              v-for="t in filteredThreads"
              :key="t.id"
              class="thread-row"
              role="button"
              tabindex="0"
              @click="openThread(t.id)"
              @keydown.enter.prevent="openThread(t.id)"
            >
              <div class="thread-row-title">{{ t.title }}</div>
              <div v-if="t.excerpt" class="thread-row-excerpt">{{ t.excerpt }}</div>
              <div class="thread-row-meta">
                <span>{{ t.author }}</span>
                <span v-if="t.replyCount"> · {{ t.replyCount }} replies</span>
                <span v-if="t.createdAt"> · {{ t.createdAt }}</span>
              </div>
            </li>
          </ul>
          <p v-if="!isLoading && !filteredThreads.length" class="muted padded">No threads to show.</p>
        </div>
      </div>
    </template>
  </div>
</template>

<style scoped>
.layerbb-forum {
  display: flex;
  flex-direction: column;
  gap: 16px;
  width: 100%;
  max-width: 960px;
  margin: 0 auto;
}

.setup-card {
  padding: 20px;
  background: rgba(0, 0, 0, 0.15);
  border: 1px solid var(--b2);
  border-radius: 12px;
  text-align: left;
}

.section-title {
  margin: 0 0 12px;
  font-size: 18px;
  font-weight: 700;
  color: var(--txt);
}

.muted {
  font-size: 14px;
  color: var(--muted);
  line-height: 1.5;
  margin: 0 0 10px;
}

.muted.small {
  font-size: 12px;
}

.code {
  font-size: 12px;
  background: rgba(0, 0, 0, 0.35);
  padding: 2px 6px;
  border-radius: 6px;
  color: var(--txt);
}

.feed-header {
  display: flex;
  flex-direction: column;
  gap: 10px;
  padding: 16px;
  background: rgba(0, 0, 0, 0.15);
  border: 1px solid var(--b2);
  border-radius: 12px;
}

.title {
  font-size: 18px;
  font-weight: 700;
  color: var(--txt);
  margin: 0;
}

.tagline {
  margin: 0;
  font-size: 13px;
  color: var(--muted);
}

.auth-section {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  align-items: center;
}

.base-pill {
  font-size: 11px;
  max-width: 100%;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  padding: 6px 10px;
  border-radius: 8px;
  background: var(--bg);
  border: 1px solid var(--b2);
  color: var(--muted);
}

.token-input {
  flex: 1;
  min-width: 200px;
}

.auth-status {
  font-size: 13px;
  color: #4ade80;
  font-weight: 600;
}

.error-msg {
  padding: 12px;
  background: rgba(239, 68, 68, 0.1);
  border: 1px solid rgba(239, 68, 68, 0.3);
  border-radius: 8px;
  color: rgb(248, 113, 113);
  font-size: 14px;
}

.input {
  width: 100%;
  padding: 10px;
  border: 1px solid var(--b2);
  border-radius: 10px;
  outline: none;
  background: rgba(0, 0, 0, 0.2);
  color: var(--txt);
  font-family: inherit;
}
.input:focus {
  border-color: rgba(255, 255, 255, 0.3);
}

.btn {
  padding: 10px 12px;
  border-radius: 10px;
  border: 1px solid var(--b2);
  background: transparent;
  cursor: pointer;
  color: var(--txt);
  transition: background 0.2s ease;
  font-family: inherit;
  font-size: 13px;
}
.btn:hover:not(:disabled) {
  background: rgba(255, 255, 255, 0.05);
}
.btn.primary {
  background: var(--bg);
  font-weight: 700;
  border-color: rgba(255, 255, 255, 0.1);
}
.btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.archives-grid {
  display: grid;
  grid-template-columns: minmax(160px, 220px) 1fr;
  gap: 16px;
  align-items: start;
}

@media (max-width: 720px) {
  .archives-grid {
    grid-template-columns: 1fr;
  }
}

.categories-panel,
.threads-panel {
  border: 1px solid var(--b);
  border-radius: 12px;
  background: rgba(0, 0, 0, 0.12);
  overflow: hidden;
}

.panel-head {
  padding: 12px 14px;
  font-weight: 700;
  font-size: 13px;
  color: var(--txt);
  border-bottom: 1px solid var(--b2);
  background: rgba(0, 0, 0, 0.2);
}

.categories-panel {
  display: flex;
  flex-direction: column;
  gap: 6px;
  padding: 10px;
}

.cat-chip {
  text-align: left;
  padding: 8px 10px;
  border-radius: 8px;
  border: 1px solid var(--b2);
  background: transparent;
  color: var(--muted);
  cursor: pointer;
  font-size: 13px;
  font-family: inherit;
}
.cat-chip:hover {
  background: rgba(255, 255, 255, 0.04);
  color: var(--txt);
}
.cat-chip.active {
  background: rgba(255, 255, 255, 0.08);
  color: var(--txt);
  border-color: rgba(255, 255, 255, 0.2);
}

.thread-list {
  list-style: none;
  margin: 0;
  padding: 0;
}

.thread-row {
  padding: 14px 16px;
  border-bottom: 1px solid var(--b);
  cursor: pointer;
  transition: background 0.15s ease;
}
.thread-row:hover,
.thread-row:focus-visible {
  background: rgba(255, 255, 255, 0.04);
  outline: none;
}

.thread-row-title {
  font-weight: 700;
  font-size: 15px;
  color: var(--txt);
  margin-bottom: 6px;
}

.thread-row-excerpt {
  font-size: 13px;
  color: var(--muted);
  line-height: 1.45;
  margin-bottom: 8px;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.thread-row-meta {
  font-size: 12px;
  color: var(--muted);
}

.padded {
  padding: 20px;
}

.thread-detail {
  border: 1px solid var(--b2);
  border-radius: 12px;
  padding: 16px;
  background: rgba(0, 0, 0, 0.12);
}

.back-btn {
  margin-bottom: 12px;
}

.thread-title {
  margin: 0 0 16px;
  font-size: 20px;
  color: var(--txt);
}

.post-list {
  list-style: none;
  margin: 0;
  padding: 0;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.post-card {
  padding: 14px;
  border-radius: 10px;
  border: 1px solid var(--b);
  background: rgba(0, 0, 0, 0.15);
}

.post-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  font-size: 12px;
  color: var(--muted);
  margin-bottom: 8px;
}

.post-author {
  font-weight: 600;
  color: var(--txt);
}

.post-body {
  font-size: 14px;
  line-height: 1.5;
  color: var(--txt);
  word-break: break-word;
}

.post-body :deep(p) {
  margin: 0 0 8px;
}
.post-body :deep(p:last-child) {
  margin-bottom: 0;
}
.post-body :deep(a) {
  color: #60a5fa;
}
</style>
