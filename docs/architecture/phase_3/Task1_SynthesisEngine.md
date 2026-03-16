# Task 1 — Synthesis Engine

**Domain:** Phase 3 — Intelligence Pillar (Synthesis Engine)  
**Date:** 2026-03-11  
**Status:** Implemented

---

## Overview

The Synthesis Engine aggregates the user's **Alchemical**, **Astrological**, and **Somatic** data into a unified LLM prompt and streams the response into the **FUTURE (DESTINY)** UI block. This document details the payload structure, API integration strategy, and wiring.

---

## Architecture

### Data Flow

```
User clicks "Generate Reading"
        ↓
generateDaoistReading() [appStore]
        ↓
buildSystemPrompt(appStore, alchemyStore)
        ↓
fetchDaoistReading(systemPrompt)
        ↓
LLM API (OpenAI-compatible)
        ↓
generatedReading ref → FUTURE (Destiny) textarea
```

### Components

| Component | Path | Responsibility |
|-----------|------|----------------|
| **intelligenceService** | `src/services/intelligenceService.ts` | `buildSystemPrompt()`, `fetchDaoistReading()` |
| **appStore** | `src/stores/appStore.ts` | `generatedReading`, `isGenerating`, `generateDaoistReading()` |
| **HomeView** | `src/views/HomeView.vue` | Generate button, FUTURE textarea, loading state |

---

## Payload Structure

### System Prompt (Markdown)

`buildSystemPrompt(appStore, alchemyStore)` produces a strict Markdown string with these sections:

#### 1. User Somatic State

- Capacity (0–10)
- Load (0–10)
- Sleep Quality (0–10)
- Cognitive Noise (0–10)
- Social Load (0–10)
- Emotional Tone (free text)

#### 2. User Intent

- Domain (e.g., work, relationships)
- Goal Constraint (one sentence)

#### 3. Astrology — Present Moment (Solar-Adjusted)

- Full `advancedAstroMoment` JSON (BaZi, Shen Sha, 24 Solar Terms, Na Yin, etc.)
- Uses True Solar Time when `geoCoords` available

#### 4. Astrology — Birth (Natal)

- Full `advancedAstroBirth` JSON ( natal pillars, sect, etc.)
- Omitted if no birth datetime provided

#### 5. Alchemy — Active Formula

- For each herb in `activeFormula`:
  - Name (common, pinyin, english)
  - Role (from herbRoles)
  - Properties: temperature, flavor, meridians
  - Actions (first 3)

---

## API Integration Strategy

### V1: OpenAI-Compatible Chat Completions

- **Endpoint:** `VITE_LLM_API_URL` or default `https://api.openai.com/v1/chat/completions`
- **Auth:** `VITE_LLM_API_KEY` (Bearer token)
- **Model:** `VITE_LLM_MODEL` or default `gpt-4o-mini`

### Request Format

```json
{
  "model": "gpt-4o-mini",
  "messages": [
    {
      "role": "system",
      "content": "You are a Daoist almanac consultant. Synthesize..."
    },
    {
      "role": "user",
      "content": "<buildSystemPrompt output>"
    }
  ],
  "max_tokens": 1024,
  "temperature": 0.7
}
```

### Error Handling

- **Missing API key:** Throws `"VITE_LLM_API_KEY is not set"`
- **HTTP error:** Throws `"LLM API error (status): message"`
- **No content:** Throws `"LLM returned no content"`
- **Caught in appStore:** Error message written to `generatedReading`; `isGenerating` reset

### Env Vars

| Variable | Required | Default | Description |
|----------|----------|--------|-------------|
| `VITE_LLM_API_KEY` | Yes | — | API key (OpenAI, Anthropic, or compatible provider) |
| `VITE_LLM_API_URL` | No | `https://api.openai.com/v1/chat/completions` | Full endpoint URL |
| `VITE_LLM_MODEL` | No | `gpt-4o-mini` | Model identifier |

---

## UI Wiring

### Generate Reading Button

- **Disabled when:** `store.isGenerating`
- **Label when idle:** "Generate Reading"
- **Label when loading:** "Consulting the Oracle…"
- **Action:** `store.generateDaoistReading`

### FUTURE (Destiny) Textarea

- **Bound to:** `store.generatedReading` (v-model)
- **Read-only when:** `store.isGenerating`
- **Placeholder:** "Destiny is yours to write. Click Generate Reading to consult the oracle."

---

## Future Considerations

1. **Streaming:** V1 returns the full response. Streaming (SSE) could be added for real-time display.
2. **Backend proxy:** Route LLM calls through `/api/` to avoid exposing API key; use `VITE_API_URL`.
3. **Prompt templates:** Move system prompt to config or allow per-domain variants.
4. **Rate limiting:** Add client-side throttling or backend rate limits.
