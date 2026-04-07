import { ref, shallowRef } from "vue";
import { createRestAPIClient } from "masto";

/** Minimal shape used by MastodonFeed (masto Status entity). */
export type MastodonStatus = {
  id: string;
  content: string;
  account?: {
    avatar?: string;
    displayName?: string;
    username?: string;
    acct?: string;
  };
  repliesCount?: number;
  reblogsCount?: number;
  favouritesCount?: number;
};

type RestClient = ReturnType<typeof createRestAPIClient>;

export function useMastodon() {
  const isLoading = ref(false);
  const error = ref<string | null>(null);
  const timeline = ref<MastodonStatus[]>([]);
  const isAuthenticated = ref(false);

  const instanceUrl = ref("");
  const accessToken = ref("");
  const client = shallowRef<RestClient | null>(null);

  function buildClient(url: string, token?: string) {
    const normalized = url.replace(/\/$/, "");
    return createRestAPIClient({
      url: normalized,
      ...(token ? { accessToken: token } : {}),
    });
  }

  /** Stub login: stores token and rebuilds client. Real OAuth can replace this. */
  const login = async (url: string, token: string) => {
    isLoading.value = true;
    error.value = null;
    try {
      instanceUrl.value = url.replace(/\/$/, "");
      accessToken.value = token;
      client.value = buildClient(instanceUrl.value, token);
      isAuthenticated.value = true;
      await fetchTimeline(instanceUrl.value);
    } catch (err: unknown) {
      error.value = err instanceof Error ? err.message : "Failed to authenticate";
      isAuthenticated.value = false;
    } finally {
      isLoading.value = false;
    }
  };

  const fetchTimeline = async (url: string = instanceUrl.value || "https://mastodon.social") => {
    isLoading.value = true;
    error.value = null;
    const normalized = url.replace(/\/$/, "");
    instanceUrl.value = normalized;
    try {
      const rest = isAuthenticated.value && accessToken.value
        ? buildClient(normalized, accessToken.value)
        : buildClient(normalized);

      const page = isAuthenticated.value
        ? await rest.v1.timelines.home.list({ limit: 20 })
        : await rest.v1.timelines.public.list({ local: true, limit: 20 });

      timeline.value = [...page] as MastodonStatus[];
    } catch (err: unknown) {
      error.value = err instanceof Error ? err.message : "Failed to fetch timeline";
      timeline.value = [];
    } finally {
      isLoading.value = false;
    }
  };

  const postStatus = async (content: string) => {
    if (!client.value || !isAuthenticated.value) {
      error.value = "Not authenticated";
      return;
    }
    try {
      await client.value.v1.statuses.create({ status: content, visibility: "public" });
      await fetchTimeline();
    } catch (err: unknown) {
      error.value = err instanceof Error ? err.message : "Failed to post";
    }
  };

  const boostStatus = async (id: string) => {
    if (!client.value || !isAuthenticated.value) {
      error.value = "Not authenticated";
      return;
    }
    try {
      await client.value.v1.statuses.$select(id).reblog();
      await fetchTimeline();
    } catch (err: unknown) {
      error.value = err instanceof Error ? err.message : "Failed to boost";
    }
  };

  const replyToStatus = async (id: string, content: string) => {
    if (!client.value || !isAuthenticated.value) {
      error.value = "Not authenticated";
      return;
    }
    try {
      await client.value.v1.statuses.create({
        status: content,
        inReplyToId: id,
        visibility: "public",
      });
      await fetchTimeline();
    } catch (err: unknown) {
      error.value = err instanceof Error ? err.message : "Failed to reply";
    }
  };

  return {
    isLoading,
    error,
    timeline,
    isAuthenticated,
    login,
    fetchTimeline,
    postStatus,
    boostStatus,
    replyToStatus,
  };
}
