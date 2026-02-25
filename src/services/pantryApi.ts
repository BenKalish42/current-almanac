/**
 * Pantry API - inventory management for Practitioner Pantry.
 */

const API_BASE = (import.meta.env.VITE_API_URL as string | undefined) ?? "";

export interface PantryItem {
  herb_id: string;
  in_stock: boolean;
}

async function apiFetch<T>(path: string, options: RequestInit = {}): Promise<T> {
  const url = `${API_BASE}${path}`;
  const res = await fetch(url, {
    headers: { "Content-Type": "application/json", ...options.headers },
    ...options,
  });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(`API error (${res.status}): ${text || res.statusText}`);
  }
  return res.json() as Promise<T>;
}

/**
 * Fetch user's pantry inventory.
 */
export async function fetchPantry(userId: string): Promise<PantryItem[]> {
  const params = new URLSearchParams({ user_id: userId });
  return apiFetch<PantryItem[]>(`/api/pantry?${params}`);
}

/**
 * Toggle herb in/out of pantry.
 */
export async function togglePantryHerb(
  herbId: string,
  userId: string
): Promise<{ herb_id: string; in_stock: boolean }> {
  return apiFetch<{ herb_id: string; in_stock: boolean }>("/api/pantry/toggle", {
    method: "POST",
    body: JSON.stringify({ herb_id: herbId, user_id: userId }),
  });
}
