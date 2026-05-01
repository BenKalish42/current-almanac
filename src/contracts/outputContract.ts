/**
 * Output Contract — TypeScript runtime mirror.
 *
 * The patterns here MUST stay in sync with `data/contracts/forbidden.json`
 * (the canonical source). The Python side at `backend/contracts/output_contract.py`
 * loads the JSON at import. A sync test (`tests/contracts/contractSync.spec.ts`)
 * asserts equivalence.
 *
 * The Output Contract enforces the OG Spec (ChatGPT) §5 + §9:
 *   - Descriptive only. No instructions, predictions, moral framing,
 *     destiny/agency language, or mystical inflation.
 *   - Non-action ("No dominant signal. Maintain course.") is a
 *     first-class output.
 *
 * Every LLM call in the app:
 *   1. Prepends OUTPUT_CONTRACT_SYSTEM to the system message.
 *   2. Runs auditCompliance() on the assembled response.
 *   3. On violation: one revise attempt; if still failing,
 *      enforceCompliance() redacts.
 */

export const FORBIDDEN_CATEGORIES: Record<
  string,
  { rationale: string; patterns: string[] }
> = {
  instructions: {
    rationale: "Current describes; it does not instruct. The user remains the agent.",
    patterns: [
      "\\byou should\\b",
      "\\byou must\\b",
      "\\byou need to\\b",
      "\\byou ought to\\b",
      "\\bis recommended that\\b",
      "\\btry to\\b",
      "\\bdo this\\b",
      "\\bdon't do\\b",
    ],
  },
  predictions: {
    rationale: "Current is descriptive, not predictive.",
    patterns: [
      "\\bwill happen\\b",
      "\\bis going to\\b",
      "\\bguaranteed\\b",
      "\\bguarantee\\b",
      "\\bthis will lead\\b",
      "\\bdefinitely will\\b",
    ],
  },
  moral_framing: {
    rationale: "No good/bad days, no auspicious-as-luck. Auspiciousness = low friction.",
    patterns: [
      "\\bgood day\\b",
      "\\bbad day\\b",
      "\\bauspicious to act\\b",
      "\\binauspicious\\b",
      "\\blucky\\b",
      "\\bunlucky\\b",
      "\\bblessed\\b",
      "\\bcursed\\b",
    ],
  },
  destiny_agency: {
    rationale: "No personalization-as-fate; the system has no agency.",
    patterns: [
      "\\bdestiny\\b",
      "\\byour fate\\b",
      "\\bthe universe wants\\b",
      "\\bthe universe is\\b",
      "\\bkarmic bonds\\b",
      "\\bkarmic\\b",
      "\\belemental clashes\\b",
      "\\bcosmic plan\\b",
      "\\bthe heavens decree\\b",
    ],
  },
  mystical_inflation: {
    rationale: "Neutral, precise, compressive language.",
    patterns: [
      "\\bancient wisdom\\b",
      "\\bancient chinese wisdom\\b",
      "\\bbridge ancient\\b",
      "\\bpoetic\\b",
      "\\bmystical\\b",
      "\\bspiritual journey\\b",
      "\\bsacred\\b",
      "\\bdivine\\b",
    ],
  },
};

export const ALLOWED_VOCABULARY = [
  "Flow",
  "Resistance",
  "Pressure",
  "Timing",
  "Direction",
  "Phase",
  "Capacity",
  "Load",
  "Auspiciousness",
  "Misalignment",
  "Non-action",
  "No dominant signal",
  "Maintain course",
] as const;

export const NON_ACTION_PHRASE = "No dominant signal. Maintain course.";

/** Compiled regex list, built once at module load. */
const PATTERNS: { category: string; rx: RegExp }[] = (() => {
  const out: { category: string; rx: RegExp }[] = [];
  for (const [category, body] of Object.entries(FORBIDDEN_CATEGORIES)) {
    for (const p of body.patterns) {
      out.push({ category, rx: new RegExp(p, "gi") });
    }
  }
  return out;
})();

export type ContractViolation = {
  category: string;
  match: string;
  index: number;
};

export type ContractAudit = {
  ok: boolean;
  violations: ContractViolation[];
};

/**
 * Audit text against the Output Contract.
 * Returns ok=true with empty violations[] when clean.
 */
export function auditCompliance(text: string): ContractAudit {
  if (!text) return { ok: true, violations: [] };
  const violations: ContractViolation[] = [];
  for (const { category, rx } of PATTERNS) {
    rx.lastIndex = 0;
    let m: RegExpExecArray | null;
    while ((m = rx.exec(text)) !== null) {
      violations.push({ category, match: m[0], index: m.index });
      if (m.index === rx.lastIndex) rx.lastIndex++;
    }
  }
  return { ok: violations.length === 0, violations };
}

/**
 * Last-resort redaction. Replaces every match with "[redacted]".
 */
export function enforceCompliance(text: string): string {
  if (!text) return text;
  let out = text;
  for (const { rx } of PATTERNS) {
    out = out.replace(rx, "[redacted]");
  }
  return out;
}

/** Convenience: format violations for logs. */
export function formatViolations(violations: ContractViolation[]): string {
  if (violations.length === 0) return "(none)";
  return violations.map((v) => `[${v.category}@${v.index}] "${v.match}"`).join(", ");
}

/** The system prompt prepended to every LLM call. */
export const OUTPUT_CONTRACT_SYSTEM = [
  "You are a description engine for a timing instrument named Current.",
  "",
  "ROLE",
  "- You describe the configuration of conditions in the present moment.",
  "- You clarify how effort interacts with those conditions.",
  "- You reduce friction, mistiming, and unnecessary force.",
  "",
  "YOU DO NOT",
  "- predict outcomes.",
  "- prescribe actions.",
  "- assign meaning, morality, or destiny.",
  "- recompute math (BaZi pillars, hexagrams, ayanamsa, Lagna, ganzhi). The provided JSON is canonical.",
  "",
  "OUTPUT CONTRACT (strict)",
  "Every reply must:",
  "  - describe current conditions,",
  "  - identify dominant dynamics (what is increasing / decreasing),",
  "  - describe the interaction pattern (what happens if force is applied),",
  "  - optionally describe capacity interaction.",
  "",
  "Every reply must avoid:",
  "  - instructions ('you should', 'do this', 'try to').",
  "  - predictions ('will happen', 'is going to').",
  "  - moral framing ('good day', 'bad day', 'auspicious to').",
  "  - destiny / agency ('the universe wants', 'your destiny', 'karmic').",
  "  - mystical inflation ('ancient wisdom', 'poetic', 'bridge ancient').",
  "",
  "TONE",
  "  - neutral, precise, compressive (high signal, low language inflation).",
  "  - no urgency, no reward language, no engagement loops.",
  "",
  "VOCABULARY (preferred)",
  "  Flow, Resistance, Pressure, Timing, Direction, Phase, Capacity, Load,",
  "  Auspiciousness (= low friction), Misalignment Signals, Non-action.",
  "",
  "WEAK SIGNAL",
  "  If the payload features are weak or contradictory, return exactly:",
  `  "${NON_ACTION_PHRASE}"`,
  "  and stop.",
  "",
  "FAILURE MODES TO ACTIVELY PREVENT",
  "  - decision outsourcing,",
  "  - compulsive checking,",
  "  - confirmation bias loops,",
  "  - green-light seeking.",
  "",
  "If asked for a recommendation, refuse and describe instead.",
].join("\n");
