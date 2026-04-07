import { ref, computed } from "vue";

/** Normalized category for UI */
export type LayerBBCategory = {
  id: string;
  name: string;
  description: string;
};

/** Thread list item */
export type LayerBBThreadSummary = {
  id: string;
  title: string;
  excerpt: string;
  author: string;
  categoryId: string;
  replyCount: number;
  createdAt: string;
};

/** Single post / reply in a thread */
export type LayerBBPost = {
  id: string;
  body: string;
  author: string;
  createdAt: string;
};

export type LayerBBThreadDetail = {
  id: string;
  title: string;
  posts: LayerBBPost[];
};

function envBaseUrl(): string {
  const raw = (import.meta.env.VITE_LAYERBB_API_URL as string | undefined) ?? "";
  return raw.replace(/\/$/, "");
}

function envToken(): string {
  return (import.meta.env.VITE_LAYERBB_BEARER_TOKEN as string | undefined) ?? "";
}

function asRecord(v: unknown): Record<string, unknown> | null {
  return v && typeof v === "object" && !Array.isArray(v) ? (v as Record<string, unknown>) : null;
}

/** Pull first array found under common keys or root array */
function extractArray(json: unknown, keys: string[]): unknown[] {
  if (Array.isArray(json)) return json;
  const o = asRecord(json);
  if (!o) return [];
  for (const k of keys) {
    const v = o[k];
    if (Array.isArray(v)) return v;
  }
  const data = o.data;
  if (Array.isArray(data)) return data;
  const dataObj = asRecord(data);
  if (dataObj) {
    for (const k of keys) {
      const v = dataObj[k];
      if (Array.isArray(v)) return v;
    }
  }
  return [];
}

function str(v: unknown, fallback = ""): string {
  if (v === null || v === undefined) return fallback;
  if (typeof v === "string") return v;
  if (typeof v === "number" || typeof v === "boolean") return String(v);
  return fallback;
}

function num(v: unknown, fallback = 0): number {
  if (typeof v === "number" && !Number.isNaN(v)) return v;
  return fallback;
}

function normalizeCategory(raw: unknown): LayerBBCategory | null {
  const o = asRecord(raw);
  if (!o) return null;
  const id = str(o.id ?? o.slug ?? o.uuid);
  if (!id) return null;
  return {
    id,
    name: str(o.name ?? o.title, "Untitled"),
    description: str(o.description ?? o.summary ?? ""),
  };
}

function normalizeThreadSummary(raw: unknown): LayerBBThreadSummary | null {
  const o = asRecord(raw);
  if (!o) return null;
  const id = str(o.id ?? o.uuid ?? o.thread_id);
  if (!id) return null;
  return {
    id,
    title: str(o.title ?? o.subject ?? o.name, "Untitled"),
    excerpt: str(o.excerpt ?? o.preview ?? o.summary ?? o.body ?? "").slice(0, 500),
    author: str(
      o.author ?? o.username ?? asRecord(o.user)?.username ?? asRecord(o.user)?.name ?? "—",
    ),
    categoryId: str(o.category_id ?? o.categoryId ?? o.forum_id ?? o.forumId ?? ""),
    replyCount: num(o.reply_count ?? o.replies_count ?? o.replyCount ?? o.comments_count),
    createdAt: str(o.created_at ?? o.createdAt ?? o.date ?? ""),
  };
}

function normalizePost(raw: unknown): LayerBBPost | null {
  const o = asRecord(raw);
  if (!o) return null;
  const id = str(o.id ?? o.uuid);
  if (!id) return null;
  const body = str(o.body ?? o.content ?? o.message ?? o.text ?? "");
  return {
    id,
    body,
    author: str(
      o.author ?? o.username ?? asRecord(o.user)?.username ?? asRecord(o.user)?.name ?? "—",
    ),
    createdAt: str(o.created_at ?? o.createdAt ?? o.date ?? ""),
  };
}

/**
 * LayerBB / forum REST helper. Point VITE_LAYERBB_API_URL at your install’s API root
 * (e.g. https://forum.example.com/api/v1 — no trailing slash).
 */
export function useLayerBB() {
  const apiBase = ref(envBaseUrl());
  const accessToken = ref(envToken());
  const isAuthenticated = computed(() => !!accessToken.value.trim());

  const isLoading = ref(false);
  const error = ref<string | null>(null);
  const categories = ref<LayerBBCategory[]>([]);
  const threads = ref<LayerBBThreadSummary[]>([]);
  const activeThread = ref<LayerBBThreadDetail | null>(null);

  function authHeaders(): HeadersInit {
    const h: Record<string, string> = { Accept: "application/json" };
    const t = accessToken.value.trim();
    if (t) h.Authorization = `Bearer ${t}`;
    return h;
  }

  async function requestJson(path: string): Promise<unknown> {
    const base = apiBase.value.replace(/\/$/, "");
    if (!base) throw new Error("LayerBB API URL is not configured.");
    const url = `${base}${path.startsWith("/") ? path : `/${path}`}`;
    const res = await fetch(url, { headers: authHeaders() });
    if (!res.ok) {
      const text = await res.text().catch(() => "");
      throw new Error(text || `${res.status} ${res.statusText}`);
    }
    return res.json() as Promise<unknown>;
  }

  /** Optional: user-pasted API token (same as env VITE_LAYERBB_BEARER_TOKEN) */
  function login(token: string) {
    accessToken.value = token.trim();
  }

  function logout() {
    accessToken.value = envToken();
  }

  async function fetchCategories() {
    isLoading.value = true;
    error.value = null;
    try {
      const json = await requestJson("/categories");
      const arr = extractArray(json, ["categories", "forums", "boards", "items"]);
      categories.value = arr.map(normalizeCategory).filter(Boolean) as LayerBBCategory[];
    } catch (e) {
      error.value = e instanceof Error ? e.message : "Failed to load categories";
      categories.value = [];
    } finally {
      isLoading.value = false;
    }
  }

  async function fetchRecentThreads(limit = 30) {
    isLoading.value = true;
    error.value = null;
    try {
      const json = await requestJson(`/threads?limit=${encodeURIComponent(String(limit))}`);
      const arr = extractArray(json, ["threads", "topics", "posts", "discussions", "items"]);
      threads.value = arr.map(normalizeThreadSummary).filter(Boolean) as LayerBBThreadSummary[];
    } catch (e) {
      error.value = e instanceof Error ? e.message : "Failed to load threads";
      threads.value = [];
    } finally {
      isLoading.value = false;
    }
  }

  async function fetchThreadDetail(threadId: string) {
    isLoading.value = true;
    error.value = null;
    try {
      const json = await requestJson(`/threads/${encodeURIComponent(threadId)}`);
      const o = asRecord(json) ?? {};
      const threadObj = asRecord(o.thread ?? o.topic ?? o.data) ?? o;
      const title = str(threadObj.title ?? threadObj.subject ?? o.title, "Thread");
      const postsRaw = extractArray(json, ["posts", "replies", "messages", "comments", "items"]);
      const postsNested = asRecord(o.thread ?? o.topic)?.posts;
      const list = Array.isArray(postsNested) ? postsNested : postsRaw;
      const posts = list.map(normalizePost).filter(Boolean) as LayerBBPost[];
      activeThread.value = { id: threadId, title, posts };
    } catch (e) {
      error.value = e instanceof Error ? e.message : "Failed to load thread";
      activeThread.value = null;
    } finally {
      isLoading.value = false;
    }
  }

  function clearActiveThread() {
    activeThread.value = null;
  }

  /** Load categories + threads; collect errors so one failing endpoint does not hide the other */
  async function loadArchivesHome() {
    const base = apiBase.value.replace(/\/$/, "");
    if (!base) {
      error.value = "LayerBB API URL is not configured.";
      categories.value = [];
      threads.value = [];
      return;
    }
    isLoading.value = true;
    error.value = null;
    const messages: string[] = [];
    try {
      try {
        const json = await requestJson("/categories");
        const arr = extractArray(json, ["categories", "forums", "boards", "items"]);
        categories.value = arr.map(normalizeCategory).filter(Boolean) as LayerBBCategory[];
      } catch (e) {
        messages.push(`Categories: ${e instanceof Error ? e.message : String(e)}`);
        categories.value = [];
      }
      try {
        const json = await requestJson(`/threads?limit=30`);
        const arr = extractArray(json, ["threads", "topics", "posts", "discussions", "items"]);
        threads.value = arr.map(normalizeThreadSummary).filter(Boolean) as LayerBBThreadSummary[];
      } catch (e) {
        messages.push(`Threads: ${e instanceof Error ? e.message : String(e)}`);
        threads.value = [];
      }
      if (messages.length) error.value = messages.join(" ");
    } finally {
      isLoading.value = false;
    }
  }

  return {
    apiBase,
    accessToken,
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
  };
}
