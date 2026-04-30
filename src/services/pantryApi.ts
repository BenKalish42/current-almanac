/**
 * Pantry API - inventory management for Practitioner Pantry.
 */

import { apiFetch } from "@/services/apiClient";

export interface PantryItem {
  herb_id: string;
  in_stock: boolean;
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
