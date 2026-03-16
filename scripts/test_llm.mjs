#!/usr/bin/env node
/**
 * Test LLM API connectivity (DeepSeek or OpenAI).
 * Run: node --env-file=.env scripts/test_llm.mjs
 * Or:  VITE_DEEPSEEK_API_KEY=sk-xxx node scripts/test_llm.mjs
 */
import { readFileSync } from "fs";
import { fileURLToPath } from "url";
import { dirname, join } from "path";

// Load .env manually if present (Node 18+)
const __dirname = dirname(fileURLToPath(import.meta.url));
const root = join(__dirname, "..");
try {
  const env = readFileSync(join(root, ".env"), "utf8");
  for (const line of env.split("\n")) {
    const m = line.match(/^([^#=]+)=(.*)$/);
    if (m) process.env[m[1].trim()] = m[2].trim().replace(/^["']|["']$/g, "");
  }
} catch {
  // .env not found, use existing env
}

const key = process.env.VITE_DEEPSEEK_API_KEY || process.env.VITE_LLM_API_KEY;
const url = process.env.VITE_LLM_API_URL || "https://api.deepseek.com/v1/chat/completions";
const model = process.env.VITE_LLM_MODEL || "deepseek-chat";

console.log("LLM config:", { url, model, hasKey: !!key });

if (!key?.trim()) {
  console.error("\n❌ No API key. Add VITE_DEEPSEEK_API_KEY or VITE_LLM_API_KEY to .env");
  process.exit(1);
}

const res = await fetch(url, {
  method: "POST",
  headers: {
    "Content-Type": "application/json",
    Authorization: `Bearer ${key}`,
  },
  body: JSON.stringify({
    model,
    messages: [{ role: "user", content: "Say OK in one word." }],
    max_tokens: 10,
  }),
});

const text = await res.text();
if (!res.ok) {
  console.error("\n❌ API error:", res.status, text);
  process.exit(1);
}

let data;
try {
  data = JSON.parse(text);
} catch {
  console.error("\n❌ Invalid JSON response:", text.slice(0, 200));
  process.exit(1);
}

const content = data?.choices?.[0]?.message?.content;
if (content == null) {
  console.error("\n❌ No content in response:", JSON.stringify(data).slice(0, 300));
  process.exit(1);
}

console.log("\n✅ LLM OK — response:", content);
process.exit(0);
