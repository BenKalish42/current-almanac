const API_BASE = (import.meta.env.VITE_API_URL as string | undefined) ?? "";

export type ApiSubscriptionEntitlement = {
  id: string;
  is_active: boolean;
  product_identifier: string | null;
  store: string | null;
  expires_at: string | null;
  will_renew: boolean | null;
  billing_issue_detected_at: string | null;
};

export type ApiSubscriptionState = {
  user_id: string;
  is_paid: boolean;
  active_entitlements: Record<string, ApiSubscriptionEntitlement>;
  active_products: string[];
  active_product_ids?: string[];
  management_url: string | null;
  store: string | null;
  period_type: string | null;
  expires_at: string | null;
  will_renew: boolean | null;
  billing_issue_detected_at: string | null;
  original_app_user_id?: string | null;
  revenuecat_app_user_id?: string | null;
  source: "supabase_cache" | "revenuecat" | "unavailable";
  updated_at: string | null;
};

export type ApiProfile = {
  user_id: string;
  email: string | null;
  is_anonymous: boolean;
};

export type ApiAuthSession = {
  user: Record<string, unknown>;
  profile: ApiProfile | null;
  subscription: ApiSubscriptionState | null;
};

function withApiBase(path: string) {
  if (/^https?:\/\//.test(path)) return path;
  return `${API_BASE}${path}`;
}

export async function apiFetch<T>(path: string, options: RequestInit = {}): Promise<T> {
  const url = withApiBase(path);
  const res = await fetch(url, {
    headers: {
      "Content-Type": "application/json",
      ...options.headers,
    },
    ...options,
  });

  if (!res.ok) {
    const text = await res.text();
    throw new Error(`API error (${res.status}): ${text || res.statusText}`);
  }

  if (res.status === 204) {
    return undefined as T;
  }

  return res.json() as Promise<T>;
}

export function getApiBase() {
  return API_BASE;
}

export async function postEmailOtp(email: string) {
  return apiFetch<{ ok: boolean }>("/api/auth/email-otp", {
    method: "POST",
    body: JSON.stringify({ email }),
  });
}

export async function fetchAuthSession(accessToken: string) {
  return apiFetch<ApiAuthSession>("/api/auth/session", {
    headers: {
      Authorization: `Bearer ${accessToken}`,
    },
  });
}

export async function fetchSubscriptionState(accessToken: string) {
  return apiFetch<ApiSubscriptionState>("/api/subscription/state", {
    headers: {
      Authorization: `Bearer ${accessToken}`,
    },
  });
}
