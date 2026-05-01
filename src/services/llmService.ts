/**
 * Oracle Engine: DeepSeek API bridge.
 *
 * Every call is wrapped by the Output Contract:
 *   1. The system message is prepended with OUTPUT_CONTRACT_SYSTEM
 *      via fetchContractBoundChat() (preferred entry).
 *   2. The response is audited; on violation we attempt one revise,
 *      then enforceCompliance() redacts as a last resort.
 *
 * Uses https://api.deepseek.com/v1/chat/completions (OpenAI-compatible).
 */

import {
  OUTPUT_CONTRACT_SYSTEM,
  auditCompliance,
  enforceCompliance,
  formatViolations,
} from "@/contracts/outputContract";

const DEEPSEEK_BASE = "https://api.deepseek.com";
const DEEPSEEK_CHAT_URL = `${DEEPSEEK_BASE}/v1/chat/completions`;
const DEFAULT_MODEL = "deepseek-chat";

export type ChatMessage = { role: "system" | "user" | "assistant"; content: string };

export type ChatOptions = {
  model?: string;
  maxTokens?: number;
  temperature?: number;
  /** AbortSignal for timeout; e.g. AbortSignal.timeout(60000) for 60s */
  signal?: AbortSignal;
  /** When true, skip contract wrapping (for back-of-house workbench calls
   *  that compose the contract themselves). Default: false. */
  skipContract?: boolean;
};

function getApiKey(): string {
  const key =
    (import.meta.env.VITE_DEEPSEEK_API_KEY as string | undefined) ??
    (import.meta.env.VITE_LLM_API_KEY as string | undefined);
  if (!key?.trim()) {
    throw new Error(
      "VITE_DEEPSEEK_API_KEY or VITE_LLM_API_KEY is not set. Add it to your .env file."
    );
  }
  return key;
}

function getChatUrl(): string {
  const override = import.meta.env.VITE_LLM_API_URL as string | undefined;
  if (override?.trim()) return override;
  return DEEPSEEK_CHAT_URL;
}

function getModel(): string {
  return (import.meta.env.VITE_LLM_MODEL as string | undefined) ?? DEFAULT_MODEL;
}

/**
 * Send messages to DeepSeek chat completions API.
 * Uses explicit https://api.deepseek.com/v1/chat/completions when VITE_LLM_API_URL is unset.
 */
export async function fetchDeepSeekChat(
  messages: ChatMessage[],
  options: ChatOptions = {}
): Promise<string> {
  const apiKey = getApiKey();
  const url = getChatUrl();
  const model = options.model ?? getModel();
  const maxTokens = options.maxTokens ?? 1024;
  const temperature = options.temperature ?? 0.6;

  const body = {
    model,
    messages,
    max_tokens: maxTokens,
    temperature,
  };

  const fetchInit: RequestInit = {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${apiKey}`,
    },
    body: JSON.stringify(body),
  };
  if (options.signal) fetchInit.signal = options.signal;
  const res = await fetch(url, fetchInit);

  if (!res.ok) {
    const text = await res.text();
    throw new Error(`DeepSeek API error (${res.status}): ${text || res.statusText}`);
  }

  const data = (await res.json()) as {
    choices?: Array<{ message?: { content?: string } }>;
    error?: { message?: string };
  };

  if (data.error?.message) {
    throw new Error(data.error.message);
  }

  const content = data.choices?.[0]?.message?.content?.trim();
  if (content == null) {
    throw new Error("DeepSeek returned no content");
  }

  return content;
}

/** Check if an LLM API key is configured. */
export function hasLlmKey(): boolean {
  const key =
    (import.meta.env.VITE_DEEPSEEK_API_KEY as string | undefined) ??
    (import.meta.env.VITE_LLM_API_KEY as string | undefined);
  return Boolean(key?.trim());
}

/**
 * Contract-bound chat — the preferred entry point for any descriptive
 * synthesis surface (Synthesize the Heavens, Synthesize the Earth,
 * Past/Present summaries, Current Flow Analysis).
 *
 *   - Prepends OUTPUT_CONTRACT_SYSTEM to the messages.
 *   - Audits the response. On violation: one revise attempt with the
 *     explicit list of violations. If still failing, enforceCompliance()
 *     redacts and we log a console.warn.
 */
export async function fetchContractBoundChat(
  messages: ChatMessage[],
  options: ChatOptions = {}
): Promise<string> {
  const wrapped: ChatMessage[] = [
    { role: "system", content: OUTPUT_CONTRACT_SYSTEM },
    ...messages,
  ];
  const first = await fetchDeepSeekChat(wrapped, options);
  const audit = auditCompliance(first);
  if (audit.ok) return first;

  // One revise attempt — show the model exactly what to fix.
  const revisePrompt: ChatMessage = {
    role: "user",
    content: [
      "Your previous reply violated the Output Contract.",
      `Violations: ${formatViolations(audit.violations)}.`,
      "Return ONLY the revised description. Use Flow / Resistance / Pressure /",
      "Timing / Phase / Capacity vocabulary. No instructions, predictions,",
      "destiny language, moral framing, or mystical inflation.",
    ].join(" "),
  };
  const second = await fetchDeepSeekChat(
    [...wrapped, { role: "assistant", content: first }, revisePrompt],
    options
  );
  const revisedAudit = auditCompliance(second);
  if (revisedAudit.ok) return second;

  // Final fallback: redact and warn.
  console.warn(
    "[outputContract] revise failed; redacting. violations=",
    formatViolations(revisedAudit.violations)
  );
  return enforceCompliance(second);
}
