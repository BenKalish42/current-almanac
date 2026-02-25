/**
 * Pantry store - Practitioner Pantry inventory management.
 * Tracks which herbs the user has in stock.
 */

import { defineStore } from "pinia";
import { ref, computed } from "vue";
import { fetchPantry, togglePantryHerb } from "@/services/pantryApi";

const LS_KEY_USER_ID = "current_pantry_user_id";

function getOrCreateUserId(): string {
  try {
    let id = localStorage.getItem(LS_KEY_USER_ID);
    if (!id) {
      id = crypto.randomUUID();
      localStorage.setItem(LS_KEY_USER_ID, id);
    }
    return id;
  } catch {
    return "default";
  }
}

export const usePantryStore = defineStore("pantry", () => {
  const inventory = ref<Map<string, boolean>>(new Map());
  const loading = ref(false);
  const error = ref<string | null>(null);

  const userId = getOrCreateUserId();

  const isHerbInStock = computed(() => (herbId: string) => {
    return inventory.value.get(herbId) ?? false;
  });

  async function fetchInventory() {
    loading.value = true;
    error.value = null;
    try {
      const items = await fetchPantry(userId);
      const map = new Map<string, boolean>();
      for (const item of items) {
        map.set(item.herb_id, item.in_stock);
      }
      inventory.value = map;
    } catch (e) {
      error.value = e instanceof Error ? e.message : "Failed to load pantry";
      inventory.value = new Map();
    } finally {
      loading.value = false;
    }
  }

  async function toggleHerb(herbId: string) {
    error.value = null;
    try {
      const res = await togglePantryHerb(herbId, userId);
      const next = new Map(inventory.value);
      next.set(herbId, res.in_stock);
      inventory.value = next;
    } catch (e) {
      error.value = e instanceof Error ? e.message : "Failed to toggle herb";
    }
  }

  return {
    inventory,
    loading,
    error,
    isHerbInStock,
    fetchInventory,
    toggleHerb,
  };
});
