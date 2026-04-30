/**
 * Lightweight client for /api/models — used by the Intelligence workbench
 * to render live key-configuration badges and KnowledgeRAG status.
 *
 * The backend never returns API key values; only booleans.
 */

import {
  ENSEMBLE_STRATEGIES,
  INTELLIGENCE_FAMILIES,
  type FamilyId,
  type FamilyMeta,
  type StrategyId,
  type StrategyMeta,
} from "@/services/intelligenceConfig";

const API_BASE = (import.meta.env.VITE_API_URL as string | undefined) ?? "";
const MODELS_URL = `${API_BASE}/api/models`;

export type ModelsFamily = FamilyMeta & {
  keyConfigured: boolean;
};

export type ModelsResponse = {
  families: ModelsFamily[];
  strategies: StrategyMeta[];
  rag: {
    available: boolean;
    backend: "neo4j" | "seed";
  };
};

/** Backend-shape for the family entry in /api/models response. */
type BackendFamily = {
  id: FamilyId;
  label: string;
  provider: string;
  envKeys: string[];
  keyConfigured: boolean;
  subtypes: Array<{ id: string; label: string; model: string; description: string }>;
};

type BackendModelsResponse = {
  families: BackendFamily[];
  strategies: StrategyMeta[];
  rag: { available: boolean; backend: "neo4j" | "seed" };
};

/**
 * Fetch /api/models. Falls back to local catalog metadata with
 * ``keyConfigured: false`` when the backend is unreachable.
 */
export async function fetchModels(signal?: AbortSignal): Promise<ModelsResponse> {
  try {
    const res = await fetch(MODELS_URL, { signal });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const data = (await res.json()) as BackendModelsResponse;

    // Re-attach the local accent metadata (backend doesn't carry styling).
    const families: ModelsFamily[] = data.families.map((f) => {
      const local = INTELLIGENCE_FAMILIES.find((l) => l.id === f.id);
      return {
        id: f.id,
        label: f.label,
        provider: f.provider,
        envKeys: f.envKeys,
        keyConfigured: f.keyConfigured,
        accent: local?.accent ?? {
          border: "border-white/20",
          bg: "bg-white/5",
          text: "text-white",
        },
        subtypes: f.subtypes.map((s) => ({
          id: s.id,
          label: s.label,
          model: s.model,
          description: s.description,
        })),
      };
    });

    return {
      families,
      strategies: data.strategies,
      rag: data.rag,
    };
  } catch {
    // Offline / unreachable backend — return local catalog with all
    // ``keyConfigured: false``. The view will surface clear hints.
    return {
      families: INTELLIGENCE_FAMILIES.map((f) => ({ ...f, keyConfigured: false })),
      strategies: ENSEMBLE_STRATEGIES,
      rag: { available: false, backend: "seed" },
    };
  }
}

export type { FamilyId, StrategyId };
