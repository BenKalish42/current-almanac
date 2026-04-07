import { ref } from "vue";

/** Minimal topic row from `/latest.json` `topic_list.topics`. */
export type DiscourseTopicSummary = {
  id: number;
  title: string;
  replyCount: number;
  lastActivity: string | null;
};

/** Single post from topic JSON `post_stream.posts`. */
export type DiscoursePost = {
  id: number;
  cooked: string;
  username: string;
  created_at: string;
};

const MISSING_BASE =
  "Set VITE_DISCOURSE_BASE_URL in your environment (see .env.example). CORS must allow this origin.";

let runtimeApiKeyOverride = "";
let runtimeApiUsernameOverride = "";

function envString(key: string): string {
  const v = (import.meta.env as Record<string, unknown>)[key];
  return typeof v === "string" ? v.trim() : "";
}

function effectiveApiKey(): string {
  return runtimeApiKeyOverride || envString("VITE_DISCOURSE_API_KEY");
}

function effectiveApiUsername(): string {
  return runtimeApiUsernameOverride || envString("VITE_DISCOURSE_API_USERNAME");
}

/** Public forum URL root, no trailing slash. Empty if unset. */
export function getDiscourseBaseUrl(): string {
  const raw = envString("VITE_DISCOURSE_BASE_URL");
  return raw.replace(/\/+$/, "");
}

/**
 * Optional client-side credentials (e.g. pasted in UI). Overrides env until cleared.
 * Discourse global/user API: both key and username must be sent together when used.
 */
export function setDiscourseApiCredentials(apiKey: string, apiUsername: string): void {
  runtimeApiKeyOverride = apiKey.trim();
  runtimeApiUsernameOverride = apiUsername.trim();
}

export function clearDiscourseApiCredentials(): void {
  runtimeApiKeyOverride = "";
  runtimeApiUsernameOverride = "";
}

export async function discourseFetch(path: string): Promise<unknown> {
  const base = getDiscourseBaseUrl();
  if (!base) throw new Error(MISSING_BASE);

  const normalized = path.startsWith("/") ? path : `/${path}`;
  const url = `${base}${normalized}`;

  const headers: Record<string, string> = {
    Accept: "application/json",
  };
  const key = effectiveApiKey();
  const user = effectiveApiUsername();
  if (key && user) {
    headers["Api-Key"] = key;
    headers["Api-Username"] = user;
  }

  const res = await fetch(url, { headers });
  if (!res.ok) {
    throw new Error(`Discourse request failed (${res.status})`);
  }
  return res.json() as Promise<unknown>;
}

function parseTopicSummary(raw: unknown): DiscourseTopicSummary | null {
  if (!raw || typeof raw !== "object") return null;
  const o = raw as Record<string, unknown>;
  const id = o.id;
  const title = o.title;
  if (typeof id !== "number" || typeof title !== "string") return null;

  let replyCount = 0;
  if (typeof o.reply_count === "number") replyCount = o.reply_count;
  else if (typeof o.posts_count === "number") replyCount = Math.max(0, o.posts_count - 1);

  const lastActivity =
    typeof o.last_posted_at === "string"
      ? o.last_posted_at
      : typeof o.bumped_at === "string"
        ? o.bumped_at
        : null;

  return { id, title, replyCount, lastActivity };
}

function parsePost(raw: unknown): DiscoursePost | null {
  if (!raw || typeof raw !== "object") return null;
  const o = raw as Record<string, unknown>;
  const id = o.id;
  const cooked = o.cooked;
  const usernameRaw = o.username ?? o.name;
  const created_at = o.created_at;
  if (typeof id !== "number" || typeof cooked !== "string") return null;
  if (typeof usernameRaw !== "string" || typeof created_at !== "string") return null;
  return { id, cooked, username: usernameRaw, created_at };
}

export async function fetchLatestTopics(limit?: number): Promise<DiscourseTopicSummary[]> {
  const per = limit != null && limit > 0 ? Math.min(limit, 100) : 30;
  const data = (await discourseFetch(`/latest.json?per_page=${per}`)) as Record<string, unknown>;
  const topicList = data.topic_list;
  if (!topicList || typeof topicList !== "object") return [];
  const topicsRaw = (topicList as Record<string, unknown>).topics;
  if (!Array.isArray(topicsRaw)) return [];

  const out: DiscourseTopicSummary[] = [];
  for (const t of topicsRaw) {
    const parsed = parseTopicSummary(t);
    if (parsed) out.push(parsed);
  }
  return out;
}

export async function fetchTopic(
  topicId: number,
): Promise<{ title: string; posts: DiscoursePost[] }> {
  const data = (await discourseFetch(`/t/${topicId}.json`)) as Record<string, unknown>;
  const title = typeof data.title === "string" ? data.title : "";
  const stream = data.post_stream;
  if (!stream || typeof stream !== "object") return { title, posts: [] };
  const postsRaw = (stream as Record<string, unknown>).posts;
  if (!Array.isArray(postsRaw)) return { title, posts: [] };

  const posts: DiscoursePost[] = [];
  for (const p of postsRaw) {
    const parsed = parsePost(p);
    if (parsed) posts.push(parsed);
  }
  return { title, posts };
}

export function useDiscourse() {
  const isLoading = ref(false);
  const error = ref<string | null>(null);
  const topics = ref<DiscourseTopicSummary[]>([]);
  const activeTopic = ref<{ id: number; title: string } | null>(null);
  const activePosts = ref<DiscoursePost[]>([]);

  async function loadLatest(limit?: number) {
    if (!getDiscourseBaseUrl()) {
      error.value = MISSING_BASE;
      topics.value = [];
      return;
    }
    isLoading.value = true;
    error.value = null;
    try {
      topics.value = await fetchLatestTopics(limit);
    } catch (e) {
      error.value = e instanceof Error ? e.message : String(e);
      topics.value = [];
    } finally {
      isLoading.value = false;
    }
  }

  async function openTopic(topicId: number) {
    if (!getDiscourseBaseUrl()) {
      error.value = MISSING_BASE;
      return;
    }
    isLoading.value = true;
    error.value = null;
    try {
      const { title, posts } = await fetchTopic(topicId);
      activeTopic.value = { id: topicId, title: title || `Topic ${topicId}` };
      activePosts.value = posts;
    } catch (e) {
      error.value = e instanceof Error ? e.message : String(e);
      activeTopic.value = null;
      activePosts.value = [];
    } finally {
      isLoading.value = false;
    }
  }

  function clearTopic() {
    activeTopic.value = null;
    activePosts.value = [];
  }

  /** Applies pasted API credentials for subsequent requests (overrides env). */
  function applyApiCredentials(apiKey: string, apiUsername: string) {
    setDiscourseApiCredentials(apiKey, apiUsername);
  }

  function clearApiCredentials() {
    clearDiscourseApiCredentials();
  }

  return {
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
  };
}
