import { describe, it, expect, beforeEach } from "vitest";
import { createPinia, setActivePinia } from "pinia";
import { useAlchemyStore } from "@/stores/alchemyStore";
import type { Herb } from "@/stores/alchemyStore";

const mockHerb: Herb = {
  id: "herb_test_001",
  pinyin_name: "Test Herb",
  common_name: "Test Root",
  safety_tier: 1,
  properties: {
    temperature: "Warm",
    flavor: ["Sweet"],
    meridians: ["Spleen", "Stomach"],
  },
  actions: ["Tonifies Qi"],
  contraindications: "None for testing.",
};

describe("alchemyStore", () => {
  beforeEach(() => {
    setActivePinia(createPinia());
  });

  it("adds herb via addHerbToFormula and clears via clearFormula", () => {
    const store = useAlchemyStore();
    expect(store.activeFormula).toHaveLength(0);

    store.addHerbToFormula(mockHerb);
    expect(store.activeFormula).toHaveLength(1);
    expect(store.activeFormula[0]?.id).toBe("herb_test_001");

    store.clearFormula();
    expect(store.activeFormula).toHaveLength(0);
  });
});
