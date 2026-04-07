<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { useMastodon } from '@/composables/useMastodon';

const {
  isLoading,
  error,
  timeline,
  isAuthenticated,
  login,
  fetchTimeline,
  postStatus,
  boostStatus,
  replyToStatus
} = useMastodon();

const instanceUrl = ref('https://mastodon.social');
const accessToken = ref('');
const newPostContent = ref('');
const replyContent = ref<{ [key: string]: string }>({});
const showReplyInput = ref<{ [key: string]: boolean }>({});

onMounted(() => {
  // Fetch initial public timeline
  fetchTimeline(instanceUrl.value);
});

const handleLogin = () => {
  const token = accessToken.value.trim();
  if (!token) {
    error.value = "Paste a Mastodon access token to use your home timeline, post, boost, and reply.";
    return;
  }
  void login(instanceUrl.value, token);
};

const handlePost = async () => {
  if (!newPostContent.value.trim()) return;
  await postStatus(newPostContent.value);
  newPostContent.value = '';
};

const handleBoost = async (id: string) => {
  await boostStatus(id);
};

const toggleReply = (id: string) => {
  showReplyInput.value[id] = !showReplyInput.value[id];
};

const submitReply = async (id: string) => {
  const content = replyContent.value[id];
  if (!content?.trim()) return;
  await replyToStatus(id, content);
  replyContent.value[id] = '';
  showReplyInput.value[id] = false;
};
</script>

<template>
  <div class="mastodon-feed">
    <div class="feed-header">
      <h2 class="title">Public Square (Federated)</h2>
      <div class="auth-section">
        <input 
          v-model="instanceUrl" 
          class="input instance-input" 
          placeholder="Instance URL (e.g. https://mastodon.social)" 
          @keyup.enter="fetchTimeline(instanceUrl)"
        />
        <input
          v-if="!isAuthenticated"
          v-model="accessToken"
          class="input token-input"
          type="password"
          autocomplete="off"
          placeholder="Access token (optional for read-only)"
        />
        <button 
          v-if="!isAuthenticated" 
          class="btn primary" 
          @click="handleLogin"
        >
          Connect
        </button>
        <span v-else class="auth-status">Authenticated</span>
        
        <button class="btn" @click="fetchTimeline(instanceUrl)" :disabled="isLoading">
          Refresh
        </button>
      </div>
    </div>

    <div v-if="error" class="error-msg">{{ error }}</div>

    <div v-if="isAuthenticated" class="compose-section">
      <textarea 
        v-model="newPostContent" 
        class="input compose-box" 
        placeholder="What is happening in the Dao?"
        rows="3"
      ></textarea>
      <div class="compose-actions">
        <button class="btn primary" @click="handlePost">Post</button>
      </div>
    </div>

    <div class="timeline">
      <div v-if="isLoading && timeline.length === 0" class="loading">
        Loading timeline...
      </div>
      
      <div v-for="status in timeline" :key="status.id" class="status-card">
        <div class="status-author">
          <img v-if="status.account?.avatar" :src="status.account.avatar" class="avatar" alt="avatar" />
          <div class="author-info">
            <div class="author-name">{{ status.account?.displayName || status.account?.username }}</div>
            <div class="author-handle">@{{ status.account?.acct }}</div>
          </div>
        </div>
        
        <div class="status-content" v-html="status.content"></div>
        
        <div class="status-actions">
          <button class="btn small action-btn" @click="toggleReply(status.id)">
            Reply ({{ status.repliesCount || 0 }})
          </button>
          <button class="btn small action-btn" @click="handleBoost(status.id)">
            Boost ({{ status.reblogsCount || 0 }})
          </button>
          <span class="status-meta">Favorites: {{ status.favouritesCount || 0 }}</span>
        </div>

        <div v-if="showReplyInput[status.id]" class="reply-section">
          <textarea 
            v-model="replyContent[status.id]" 
            class="input compose-box" 
            placeholder="Write your reply..."
            rows="2"
          ></textarea>
          <div class="compose-actions">
            <button class="btn primary small" @click="submitReply(status.id)">Send Reply</button>
            <button class="btn small" @click="toggleReply(status.id)">Cancel</button>
          </div>
        </div>
      </div>
      
      <div v-if="!isLoading && timeline.length === 0" class="empty-state">
        No statuses found.
      </div>
    </div>
  </div>
</template>

<style scoped>
.mastodon-feed {
  display: flex;
  flex-direction: column;
  gap: 16px;
  width: 100%;
  max-width: 800px;
  margin: 0 auto;
}

.feed-header {
  display: flex;
  flex-direction: column;
  gap: 12px;
  padding: 16px;
  background: rgba(0,0,0,0.15);
  border: 1px solid var(--b2);
  border-radius: 12px;
}

.title {
  font-size: 18px;
  font-weight: 700;
  color: var(--txt);
  margin: 0;
}

.auth-section {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  align-items: center;
}

.instance-input {
  flex: 1;
  min-width: 200px;
}

.token-input {
  flex: 1;
  min-width: 160px;
}

.auth-status {
  font-size: 13px;
  color: #10b981;
  font-weight: 600;
}

.compose-section {
  padding: 16px;
  background: rgba(0,0,0,0.15);
  border: 1px solid var(--b2);
  border-radius: 12px;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.compose-box {
  resize: vertical;
  width: 100%;
}

.compose-actions {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
}

.timeline {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.status-card {
  padding: 16px;
  background: rgba(0,0,0,0.15);
  border: 1px solid var(--b);
  border-radius: 12px;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.status-author {
  display: flex;
  align-items: center;
  gap: 12px;
}

.avatar {
  width: 40px;
  height: 40px;
  border-radius: 8px;
  background: var(--bg);
  object-fit: cover;
}

.author-info {
  display: flex;
  flex-direction: column;
}

.author-name {
  font-size: 14px;
  font-weight: 700;
  color: var(--txt);
}

.author-handle {
  font-size: 12px;
  color: var(--muted);
}

.status-content {
  font-size: 14px;
  line-height: 1.5;
  color: var(--txt);
  word-break: break-word;
}

/* Deep selector to ensure mastodon HTML content styles properly */
.status-content :deep(p) {
  margin: 0 0 8px 0;
}
.status-content :deep(p:last-child) {
  margin-bottom: 0;
}
.status-content :deep(a) {
  color: #60a5fa;
  text-decoration: none;
}
.status-content :deep(a:hover) {
  text-decoration: underline;
}
.status-content :deep(img), .status-content :deep(video) {
  max-width: 100%;
  height: auto;
  border-radius: 8px;
  margin-top: 8px;
}

.status-actions {
  display: flex;
  align-items: center;
  gap: 12px;
  padding-top: 8px;
  border-top: 1px solid var(--b2);
  flex-wrap: wrap;
}

.action-btn {
  background: transparent;
  color: var(--muted);
}
.action-btn:hover {
  background: var(--bg);
  color: var(--txt);
}

.status-meta {
  font-size: 12px;
  color: var(--muted);
  margin-left: auto;
}

.reply-section {
  margin-top: 8px;
  padding-top: 12px;
  border-top: 1px dashed var(--b2);
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.loading, .empty-state {
  padding: 24px;
  text-align: center;
  color: var(--muted);
  font-size: 14px;
  background: rgba(0,0,0,0.15);
  border: 1px solid var(--b);
  border-radius: 12px;
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
  background: rgba(0,0,0,0.2);
  color: var(--txt);
}
.input:focus {
  border-color: rgba(255,255,255,0.3);
}

.btn {
  padding: 10px 12px;
  border-radius: 10px;
  border: 1px solid var(--b2);
  background: transparent;
  cursor: pointer;
  color: var(--txt);
  transition: all 0.2s ease;
  font-family: inherit;
}
.btn:hover:not(:disabled) {
  background: rgba(255,255,255,0.05);
}
.btn.primary {
  background: var(--bg);
  font-weight: 700;
  border-color: rgba(255,255,255,0.1);
}
.btn.primary:hover:not(:disabled) {
  background: rgba(255,255,255,0.1);
}
.btn.small {
  padding: 6px 10px;
  font-size: 12px;
}
.btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}
</style>