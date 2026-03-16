/**
 * Phase 3 — Intelligence Pillar: Synthesis Engine
 * Aggregates Alchemical, Astrological, and Somatic data into LLM prompts.
 */

/** Snapshot of app store state needed for prompt building */
export type AppStoreSnapshot = {
  intentDomain: string;
  intentGoalConstraint: string;
  userCapacity: number | null;
  userLoad: number | null;
  userSleepQuality: number | null;
  userCognitiveNoise: number | null;
  userSocialLoad: number | null;
  userEmotionalTone: string;
  advancedAstroMoment: Record<string, unknown> | null;
  advancedAstroBirth: Record<string, unknown> | null;
};

/** Snapshot of alchemy store state needed for prompt building */
export type AlchemyStoreSnapshot = {
  activeFormula: Array<{
    id: string;
    pinyin_name: string;
    common_name: string;
    english_name?: string;
    properties: {
      temperature: string;
      flavor: string[];
      meridians: string[];
    };
    actions: string[];
  }>;
  herbRoles: Record<string, string>;
};

export type CauldronHerbSnapshot = {
  id: string;
  pinyin_name: string;
  common_name: string;
  english_name?: string;
  properties?: {
    temperature?: string;
    flavor?: string[];
    meridians?: string[];
  };
  actions?: string[];
};

/**
 * Extracts User State, Astrology, and Alchemy data into a strict Markdown system prompt
 * for the LLM. Used as context when generating the Daoist reading.
 */
export function buildSystemPrompt(
  appStore: AppStoreSnapshot,
  alchemyStore: AlchemyStoreSnapshot
): string {
  const sections: string[] = [];

  // --- User Somatic State ---
  sections.push("### User Somatic State");
  sections.push(`- Capacity: ${appStore.userCapacity ?? "—"}/10`);
  sections.push(`- Load: ${appStore.userLoad ?? "—"}/10`);
  sections.push(`- Sleep Quality: ${appStore.userSleepQuality ?? "—"}/10`);
  sections.push(`- Cognitive Noise: ${appStore.userCognitiveNoise ?? "—"}/10`);
  sections.push(`- Social Load: ${appStore.userSocialLoad ?? "—"}/10`);
  sections.push(`- Emotional Tone: ${appStore.userEmotionalTone?.trim() || "—"}`);
  sections.push("");

  // --- User Intent ---
  sections.push("### User Intent");
  sections.push(`- Domain: ${appStore.intentDomain?.trim() || "—"}`);
  sections.push(`- Goal Constraint: ${appStore.intentGoalConstraint?.trim() || "—"}`);
  sections.push("");

  // --- Astrology (Present Moment BaZi/Hexagrams) ---
  sections.push("### Astrology — Present Moment (Solar-Adjusted)");
  if (appStore.advancedAstroMoment) {
    sections.push("```json");
    sections.push(JSON.stringify(appStore.advancedAstroMoment, null, 2));
    sections.push("```");
  } else {
    sections.push("(No present-moment astro data)");
  }
  sections.push("");

  // --- Astrology (Birth / Natal) ---
  sections.push("### Astrology — Birth (Natal)");
  if (appStore.advancedAstroBirth) {
    sections.push("```json");
    sections.push(JSON.stringify(appStore.advancedAstroBirth, null, 2));
    sections.push("```");
  } else {
    sections.push("(No birth astro data — enter birth datetime to include)");
  }
  sections.push("");

  // --- Alchemy (Active Formula) ---
  sections.push("### Alchemy — Active Formula");
  const formula = alchemyStore.activeFormula;
  const roles = alchemyStore.herbRoles ?? {};
  if (formula && formula.length > 0) {
    for (const herb of formula) {
      const role = roles[herb.id] ?? "—";
      sections.push(`- **${herb.common_name || herb.pinyin_name}** (${herb.english_name || herb.pinyin_name})`);
      sections.push(`  - Role: ${role}`);
      sections.push(`  - Properties: ${herb.properties?.temperature ?? "—"} | ${(herb.properties?.flavor ?? []).join(", ") || "—"}`);
      sections.push(`  - Meridians: ${(herb.properties?.meridians ?? []).join(", ") || "—"}`);
      sections.push(`  - Actions: ${(herb.actions ?? []).slice(0, 3).join("; ") || "—"}`);
    }
  } else {
    sections.push("(No herbs in active formula)");
  }

  return sections.join("\n");
}

import { fetchDeepSeekChat } from "@/services/llmService";

/**
 * Sends the synthesized prompt to the LLM (DeepSeek by default).
 * Task 12.2: Uses llmService for correct DeepSeek API URL and auth.
 */
export async function fetchDaoistReading(promptText: string): Promise<string> {
  const systemPrompt =
    "You are a Daoist almanac consultant. Synthesize the user's somatic state, astrological context, and alchemical formula into a grounded, descriptive reading. Be neutral and descriptive. No predictions, moralizing, or destiny language. Write in clear paragraphs.";

  return fetchDeepSeekChat(
    [
      { role: "system", content: systemPrompt },
      { role: "user", content: promptText },
    ],
    { maxTokens: 1024, temperature: 0.7 }
  );
}

/**
 * Analyze a combined multi-formula cauldron for vector direction, synergy, and collisions.
 * Task 12.2: Uses llmService for DeepSeek.
 */
export async function analyzeCauldronSynergy(
  activeFormula: CauldronHerbSnapshot[],
  herbDosages: Record<string, number>
): Promise<string> {
  const systemPrompt =
    "You are a Master Daoist Clinical Architect. The user has combined multiple classical formulas. Analyze the combined ingredient list and dosages. Output your analysis in strict Markdown with three sections: 1. OVERALL VECTOR (Is it lifting, sinking, warming, cooling?), 2. SYNERGIES & FLOWS (Where do the formulas support each other?), 3. TRAFFIC JAMS & COLLISIONS (Where do the vectors fight? e.g., heavy cloying Yin trapping ascending Yang).";

  const payload = activeFormula.map((herb) => ({
    herb_id: herb.id,
    name: herb.common_name || herb.pinyin_name,
    pinyin_name: herb.pinyin_name,
    dosage: herbDosages[herb.id] ?? 0,
    temperature: herb.properties?.temperature ?? "—",
    flavor: herb.properties?.flavor ?? [],
    meridians: herb.properties?.meridians ?? [],
    actions: (herb.actions ?? []).slice(0, 5),
  }));

  const userPrompt = [
    "Combined Cauldron Payload:",
    "```json",
    JSON.stringify(payload, null, 2),
    "```",
    "",
    "Assess vector direction, support patterns, and conflict hotspots.",
  ].join("\n");

  return fetchDeepSeekChat(
    [
      { role: "system", content: systemPrompt },
      { role: "user", content: userPrompt },
    ],
    { maxTokens: 1200, temperature: 0.4 }
  );
}
