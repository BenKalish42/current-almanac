/**
 * Intelligence Workbench — frontend metadata mirror.
 *
 * Mirrors the backend MODEL_CATALOG + ENSEMBLE_STRATEGIES so the workbench can
 * render even before /api/models responds, and for client-side rendering of
 * routing summaries and labels. Live key-configuration status comes from the
 * backend response (see ./intelligenceApi.ts).
 */

export type FamilyId = "claude" | "chatgpt" | "gemini" | "deepseek";

export type SubtypeMeta = {
  id: string;
  label: string;
  /** LiteLLM model name (informational; backend resolves the real model). */
  model: string;
  description: string;
};

export type FamilyMeta = {
  id: FamilyId;
  label: string;
  provider: string;
  envKeys: string[];
  /** Tailwind classes — accent stripe + selected ring colors. */
  accent: {
    /** Border / stripe color when card is selected. */
    border: string;
    /** Subtle bg when selected. */
    bg: string;
    /** Text accent. */
    text: string;
  };
  subtypes: SubtypeMeta[];
};

export type StrategyId =
  | "single"
  | "fallback"
  | "parallel_judge"
  | "specialist_committee"
  | "self_consistency"
  | "critic_reviser"
  | "confidence_escalation"
  | "structured_verifier";

export type StrategyMeta = {
  id: StrategyId;
  label: string;
  description: string;
  needsMultipleProviders?: boolean;
};

export type IntelligenceOptions = {
  family: FamilyId;
  /** Subtype id within the selected family. */
  model: string;
  strategy: StrategyId;
  /** Per-family preferred subtype id. */
  selectedModelsByFamily: Record<FamilyId, string>;
  ragEnabled: boolean;
};

export const INTELLIGENCE_FAMILIES: FamilyMeta[] = [
  {
    id: "claude",
    label: "Claude",
    provider: "Anthropic",
    envKeys: ["ANTHROPIC_API_KEY"],
    accent: {
      border: "border-amber-500/60",
      bg: "bg-amber-500/10",
      text: "text-amber-300",
    },
    subtypes: [
      {
        id: "sonnet",
        label: "Sonnet",
        model: "claude-3-5-sonnet-20241022",
        description: "Balanced flagship — best for most prompts.",
      },
      {
        id: "opus",
        label: "Opus",
        model: "claude-3-opus-20240229",
        description: "Deep reasoning for complex synthesis.",
      },
      {
        id: "haiku",
        label: "Haiku",
        model: "claude-3-5-haiku-20241022",
        description: "Fast, lightweight responses.",
      },
    ],
  },
  {
    id: "chatgpt",
    label: "ChatGPT",
    provider: "OpenAI",
    envKeys: ["OPENAI_API_KEY"],
    accent: {
      border: "border-emerald-500/60",
      bg: "bg-emerald-500/10",
      text: "text-emerald-300",
    },
    subtypes: [
      {
        id: "gpt-4o",
        label: "GPT-4o",
        model: "gpt-4o",
        description: "OpenAI flagship multimodal.",
      },
      {
        id: "gpt-4o-mini",
        label: "GPT-4o mini",
        model: "gpt-4o-mini",
        description: "Fast & cheap general model.",
      },
      {
        id: "reasoning",
        label: "Reasoning (o-series)",
        model: "o3-mini",
        description: "Step-by-step reasoning model.",
      },
    ],
  },
  {
    id: "gemini",
    label: "Gemini",
    provider: "Google",
    envKeys: ["GEMINI_API_KEY", "GOOGLE_API_KEY"],
    accent: {
      border: "border-sky-500/60",
      bg: "bg-sky-500/10",
      text: "text-sky-300",
    },
    subtypes: [
      {
        id: "pro",
        label: "Pro",
        model: "gemini/gemini-1.5-pro",
        description: "Google flagship long-context.",
      },
      {
        id: "flash",
        label: "Flash",
        model: "gemini/gemini-1.5-flash",
        description: "Fast, cheap general model.",
      },
    ],
  },
  {
    id: "deepseek",
    label: "DeepSeek",
    provider: "DeepSeek",
    envKeys: ["DEEPSEEK_API_KEY"],
    accent: {
      border: "border-violet-500/60",
      bg: "bg-violet-500/10",
      text: "text-violet-300",
    },
    subtypes: [
      {
        id: "chat",
        label: "Chat",
        model: "deepseek/deepseek-chat",
        description: "DeepSeek V3 general chat.",
      },
      {
        id: "reasoner",
        label: "Reasoner",
        model: "deepseek/deepseek-reasoner",
        description: "DeepSeek R1 reasoning model.",
      },
    ],
  },
];

export const ENSEMBLE_STRATEGIES: StrategyMeta[] = [
  {
    id: "single",
    label: "Single",
    description: "Use only the selected model.",
  },
  {
    id: "fallback",
    label: "Fallback",
    description: "Try the selected model, then configured providers in priority order.",
  },
  {
    id: "parallel_judge",
    label: "Parallel Judge",
    description: "Each configured family drafts; the selected model synthesizes.",
    needsMultipleProviders: true,
  },
  {
    id: "specialist_committee",
    label: "Specialist Committee",
    description: "DeepSeek = Astrology · ChatGPT = Herbal · Claude = Plain Language · Gemini = Synthesis.",
    needsMultipleProviders: true,
  },
  {
    id: "self_consistency",
    label: "Self-Consistency",
    description: "Three drafts on the selected model, then a consolidator pass.",
  },
  {
    id: "critic_reviser",
    label: "Critic / Reviser",
    description: "Draft, then critique, then revise — all on the selected model.",
  },
  {
    id: "confidence_escalation",
    label: "Confidence Escalation",
    description: "Cheap model first; escalate to the strongest model if uncertainty appears.",
  },
  {
    id: "structured_verifier",
    label: "Structured Verifier",
    description: "Primary draft + verifier audit pass for safety and herb grounding.",
  },
];

export const DEFAULT_INTELLIGENCE_OPTIONS: IntelligenceOptions = {
  family: "chatgpt",
  model: "gpt-4o-mini",
  strategy: "single",
  selectedModelsByFamily: {
    claude: "sonnet",
    chatgpt: "gpt-4o-mini",
    gemini: "flash",
    deepseek: "chat",
  },
  ragEnabled: false,
};

export function findFamily(id: FamilyId): FamilyMeta | undefined {
  return INTELLIGENCE_FAMILIES.find((f) => f.id === id);
}

export function findSubtype(family: FamilyId, subtypeId: string): SubtypeMeta | undefined {
  return findFamily(family)?.subtypes.find((s) => s.id === subtypeId);
}

export function findStrategy(id: StrategyId): StrategyMeta | undefined {
  return ENSEMBLE_STRATEGIES.find((s) => s.id === id);
}

/**
 * Render a one-line summary suitable for the active routing card.
 * Example: "Claude · Sonnet · Single · RAG: Off"
 */
export function summarizeRouting(options: IntelligenceOptions): string {
  const fam = findFamily(options.family);
  const sub = findSubtype(options.family, options.model);
  const strat = findStrategy(options.strategy);
  const parts = [
    fam?.label ?? options.family,
    sub?.label ?? options.model,
    strat?.label ?? options.strategy,
    `RAG: ${options.ragEnabled ? "On" : "Off"}`,
  ];
  return parts.join(" · ");
}
