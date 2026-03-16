/**
 * Phase 3 Task 12.2 — Oracle Engine: DeepSeek API bridge.
 * Explicit DeepSeek configuration to fix 404 errors.
 * Uses https://api.deepseek.com/v1/chat/completions (OpenAI-compatible).
 */

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
