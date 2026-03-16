# Task 12.2 — Oracle Engine

**Domain:** Phase 3.0 — Alpha Web Prototype (The Oracle Engine)  
**Date:** 2026-03-16  
**Status:** Implemented

---

## Overview

Task 12.2 fixes the DeepSeek API 404 errors, re-enables auto-generation of Past/Present baseline summaries, and builds the primary "Generate Current Flow Analysis" button that synthesizes the user's BaZi, the Moment's BaZi, and the Active Meridian.

---

## Requirements Summary

| Requirement | Implementation |
|-------------|----------------|
| **Fix DeepSeek 404** | Explicit `https://api.deepseek.com/v1/chat/completions` URL in `llmService.ts` |
| **Auth** | `Authorization: Bearer ${VITE_DEEPSEEK_API_KEY}` or `VITE_LLM_API_KEY` |
| **Model** | `deepseek-chat` |
| **Auto-gen Past Summary** | Vue watch on `birthDatetimeLocal` (debounced 1200ms) → `requestPastSummary()` |
| **Auto-gen Present Summary** | Vue watch on `dateISO`, `timeHHMM` (debounced 1200ms) → `requestPresentSummary()` |
| **Generate Current Flow** | Prominent button → `requestCurrentFlowAnalysis()` → synthesis of Birth + Moment + Active Meridian |
| **Loading state** | "Consulting the Heavens…" |

---

## Implementation Details

### 1. DeepSeek API Bridge (`src/services/llmService.ts`)

- **Base URL:** `https://api.deepseek.com`
- **Endpoint:** `/v1/chat/completions` (full: `https://api.deepseek.com/v1/chat/completions`)
- **Auth:** `VITE_DEEPSEEK_API_KEY` with fallback to `VITE_LLM_API_KEY`
- **Override:** `VITE_LLM_API_URL` for custom endpoint
- **Model:** `deepseek-chat` (or `VITE_LLM_MODEL`)

### 2. intelligenceService.ts

- `fetchDaoistReading()` and `analyzeCauldronSynergy()` now use `llmService.fetchDeepSeekChat()` for direct DeepSeek calls.

### 3. appStore.ts

- **404 fallback:** When backend `/api/interpret` returns 404, falls back to `interpretViaDeepSeekDirect()` (direct DeepSeek call).
- **pastSummary, presentSummary:** Auto-generated baseline summaries.
- **currentFlowAnalysis, currentFlowLoading:** State for the primary synthesis.
- **requestPastSummary():** Lightweight 2–3 sentence summary of birth chart.
- **requestPresentSummary():** Lightweight 2–3 sentence summary of present moment + active meridian.
- **requestCurrentFlowAnalysis():** Full synthesis with master prompt:
  > "You are a Master Daoist Astrologer. Synthesize the user's Birth chart with the Current Moment's chart and the currently active Meridian. Explain what the user might be experiencing energetically right now, and offer ancient Chinese wisdom on how to move forward."

### 4. HomeView.vue

- **Watchers:** Debounced (1200ms) on `birthDatetimeLocal` and `[dateISO, timeHHMM]` for silent auto-generation.
- **Past/Present panels:** Display `pastSummary` and `presentSummary` in `baselineSummary` blocks.
- **Generate Current Flow:** Prominent `🌊 Generate Current Flow Analysis` button above the Current (Flow) section.
- **Response block:** Elegant `currentFlowBlock` with loading state "Consulting the Heavens…".

---

## Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `VITE_DEEPSEEK_API_KEY` | Yes* | — | DeepSeek API key (preferred) |
| `VITE_LLM_API_KEY` | Yes* | — | Fallback API key |
| `VITE_LLM_API_URL` | No | `https://api.deepseek.com/v1/chat/completions` | Override endpoint |
| `VITE_LLM_MODEL` | No | `deepseek-chat` | Model identifier |

*At least one of `VITE_DEEPSEEK_API_KEY` or `VITE_LLM_API_KEY` must be set.

---

## Files Modified

| File | Changes |
|------|---------|
| `src/services/llmService.ts` | **New.** DeepSeek API bridge with explicit URL and auth. |
| `src/services/intelligenceService.ts` | Uses `fetchDeepSeekChat` from llmService. |
| `src/stores/appStore.ts` | 404 fallback, pastSummary, presentSummary, currentFlowAnalysis, requestPastSummary, requestPresentSummary, requestCurrentFlowAnalysis. |
| `src/views/HomeView.vue` | Watchers for auto-gen, Generate Current Flow button, baseline summary blocks, styles. |
| `.env.example` | VITE_DEEPSEEK_API_KEY, DeepSeek defaults. |

---

## UX Notes

- **Auto-generation:** Silent; no loading indicators for baseline summaries. User sees results after ~1.2s debounce.
- **Generate Current Flow:** Highly prominent button; loading state "Consulting the Heavens…" during synthesis.
- **Past/Present interpretation:** Existing "Past" and "Present" buttons still trigger `requestInterpretation()` (backend or DeepSeek fallback).
