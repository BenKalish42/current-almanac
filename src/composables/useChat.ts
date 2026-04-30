/**
 * useChat composable - custom implementation for AI chatbot.
 * Uses fetch + SSE stream parsing, compatible with AI SDK UI Message Stream format.
 *
 * The Intelligence workbench passes optional ``intelligence`` options through
 * to the backend so /api/chat can route to the selected family + ensemble.
 */
import type { UIMessage } from "ai";
import { generateId } from "ai";
import { ref } from "vue";
import type { IntelligenceOptions } from "@/services/intelligenceConfig";

const API_BASE = import.meta.env.VITE_API_URL || "";
const CHAT_API = `${API_BASE}/api/chat`;

export type SendMessageOptions = {
  text: string;
  intelligence?: IntelligenceOptions;
};

export function useChat() {
  const messages = ref<UIMessage[]>([]);
  const status = ref<"submitted" | "streaming" | "ready" | "error">("ready");
  const error = ref<Error | undefined>(undefined);
  let abortController: AbortController | null = null;

  async function sendMessage(opts: SendMessageOptions) {
    const text = opts.text?.trim();
    if (!text) return;

    const userMessage: UIMessage = {
      id: generateId(),
      role: "user",
      parts: [{ type: "text", text }],
    };
    messages.value = [...messages.value, userMessage];

    const assistantMessage: UIMessage = {
      id: generateId(),
      role: "assistant",
      parts: [],
    };
    messages.value = [...messages.value, assistantMessage];

    status.value = "submitted";
    error.value = undefined;
    abortController = new AbortController();

    try {
      const body: {
        messages: UIMessage[];
        intelligence?: IntelligenceOptions;
      } = { messages: messages.value.slice(0, -1) };
      if (opts.intelligence) body.intelligence = opts.intelligence;

      const res = await fetch(CHAT_API, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
        signal: abortController.signal,
      });

      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      if (!res.body) throw new Error("No response body");

      status.value = "streaming";
      const reader = res.body.getReader();
      const decoder = new TextDecoder();
      let buffer = "";

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split("\n\n");
        buffer = lines.pop() ?? "";

        for (const line of lines) {
          if (!line.startsWith("data: ")) continue;
          try {
            const data = JSON.parse(line.slice(6)) as {
              type: string;
              id?: string;
              delta?: string;
              messageId?: string;
            };
            if (data.type === "text-delta" && data.delta) {
              const last = messages.value[messages.value.length - 1];
              if (!last) continue;
              const parts = [...last.parts];
              const textIdx = parts.findIndex((p) => p.type === "text");
              if (textIdx >= 0) {
                const p = parts[textIdx] as { type: "text"; text: string };
                parts[textIdx] = { type: "text", text: p.text + data.delta };
              } else {
                parts.push({ type: "text", text: data.delta });
              }
              messages.value = [
                ...messages.value.slice(0, -1),
                { ...last, id: last.id ?? generateId(), parts },
              ];
            }
          } catch {
            // ignore parse errors
          }
        }
      }

      status.value = "ready";
    } catch (err) {
      if ((err as Error).name === "AbortError") return;
      error.value = err instanceof Error ? err : new Error(String(err));
      status.value = "error";
      messages.value = messages.value.slice(0, -1);
    } finally {
      abortController = null;
    }
  }

  function stop() {
    if (abortController) {
      abortController.abort();
    }
  }

  return {
    messages,
    status,
    error,
    sendMessage,
    stop,
  };
}
