/**
 * Oracle — contract-bound synthesis pipelines.
 *
 * Two entry points, named per Chen's blueprint:
 *
 *   synthesizeHeavens(payload)  → "Synthesize the Heavens" (Pillar 1)
 *   synthesizeEarth(payload)    → "Synthesize the Earth"   (Pillar 2)
 *
 * Each prepends OUTPUT_CONTRACT_SYSTEM, instructs the LLM not to
 * recompute math, runs the RAG traversal as context (when a triplestore
 * is provided), and returns the audited reply via fetchContractBoundChat.
 */

import { fetchContractBoundChat } from "@/services/llmService";
import { NON_ACTION_PHRASE } from "@/contracts/outputContract";
import {
  serializeEarth,
  serializeHeavens,
  traverseEarth,
  traverseHeavens,
} from "@/services/graph/ragTraversal";
import type { Triplestore } from "@/services/graph/triplestore";

export type HeavensPayload = {
  /** Natal pillars, hexagrams, Nine Star numbers — already computed by Stream 2 math. */
  natal: Record<string, unknown>;
  /** Present pillars, hexagrams, organ. */
  present: Record<string, unknown>;
  /** Optional Vedic block (Lagna, Nakshatra). */
  vedic?: Record<string, unknown>;
  /** Optional Nine Palaces matrix snapshot. */
  ninePalaces?: Record<string, unknown>;
};

export type EarthPayload = {
  /** Eight Principles state (Ba Gang sliders, 0..N). */
  baGang: Record<string, number>;
  /** Active meridian name from the organ clock. */
  activeMeridian: string | null;
  /** Optional active formula context (herbs already chosen by user). */
  formula?: Record<string, unknown>;
  /** Optional intent / domain. */
  intent?: { domain?: string; goal_constraint?: string };
};

const SHARED_TAIL = [
  "Treat the JSON above as canonical. Do not recompute math.",
  "Identify dominant dynamics (what is increasing / decreasing) and the",
  "interaction pattern (what happens if force is applied here).",
  "Use Flow / Resistance / Pressure / Timing / Phase / Capacity vocabulary.",
  `If the signal is weak or contradictory, return only "${NON_ACTION_PHRASE}" and stop.`,
].join("\n");

// -----------------------------------------------------------------------------
// Heavens
// -----------------------------------------------------------------------------

export function buildHeavensUserPrompt(
  payload: HeavensPayload,
  store?: Triplestore
): string {
  const sections: string[] = ["### Heavens — canonical configuration"];
  sections.push("```json");
  sections.push(
    JSON.stringify(
      {
        natal: payload.natal,
        present: payload.present,
        ...(payload.vedic ? { vedic: payload.vedic } : {}),
        ...(payload.ninePalaces ? { nine_palaces: payload.ninePalaces } : {}),
      },
      null,
      2
    )
  );
  sections.push("```");

  if (store) {
    const subgraph = traverseHeavens(store);
    sections.push("");
    sections.push("### Triplestore subgraph (read-only context)");
    sections.push("```json");
    sections.push(serializeHeavens(subgraph));
    sections.push("```");
  }

  sections.push("");
  sections.push(SHARED_TAIL);
  return sections.join("\n");
}

export async function synthesizeHeavens(
  payload: HeavensPayload,
  options: { store?: Triplestore; signal?: AbortSignal } = {}
): Promise<string> {
  return fetchContractBoundChat(
    [{ role: "user", content: buildHeavensUserPrompt(payload, options.store) }],
    { maxTokens: 1024, temperature: 0.3, signal: options.signal }
  );
}

// -----------------------------------------------------------------------------
// Earth
// -----------------------------------------------------------------------------

export function buildEarthUserPrompt(
  payload: EarthPayload,
  store?: Triplestore
): string {
  const sections: string[] = ["### Earth — canonical configuration"];
  sections.push("```json");
  sections.push(
    JSON.stringify(
      {
        ba_gang: payload.baGang,
        active_meridian: payload.activeMeridian,
        ...(payload.formula ? { formula: payload.formula } : {}),
        ...(payload.intent ? { intent: payload.intent } : {}),
      },
      null,
      2
    )
  );
  sections.push("```");

  if (store) {
    const subgraph = traverseEarth(store);
    sections.push("");
    sections.push("### Triplestore subgraph (read-only context)");
    sections.push("```json");
    sections.push(serializeEarth(subgraph));
    sections.push("```");
  }

  sections.push("");
  sections.push("Describe properties only. Do not prescribe. Do not diagnose.");
  sections.push("If asked for a recommendation, refuse and describe instead.");
  sections.push("");
  sections.push(SHARED_TAIL);
  return sections.join("\n");
}

export async function synthesizeEarth(
  payload: EarthPayload,
  options: { store?: Triplestore; signal?: AbortSignal } = {}
): Promise<string> {
  return fetchContractBoundChat(
    [{ role: "user", content: buildEarthUserPrompt(payload, options.store) }],
    { maxTokens: 1024, temperature: 0.3, signal: options.signal }
  );
}
