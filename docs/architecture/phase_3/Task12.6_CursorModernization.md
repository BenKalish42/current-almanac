# Task 12.6 — Cursor Context Modernization

**Domain:** Phase 3.5 — AI-Native Architecture Governance  
**Date:** 2026-03-17  
**Status:** Implemented

---

## Overview

Task 12.6 transitions the project away from a monolithic instruction set to a modular, frontmatter-driven rule architecture under `.cursor/rules/`. This preserves token budgets and reduces agent hallucinations when working across the stack (Vue 3, Neo4j, Python, Matrix).

---

## Requirements Summary

| Requirement | Implementation |
|-------------|----------------|
| **Directory** | `.cursor/rules/` at project root |
| **Vue rule** | `vue-composition.mdc` — Composition API, `<script setup>`, TypeScript strict, Tailwind |
| **Neo4j rule** | `neo4j-cypher.mdc` — parameterized queries only, no string concatenation |
| **Matrix E2EE rule** | `matrix-e2ee.mdc` — vodozemac, spec-first, no crypto mocks |
| **Codebase primer** | `CODEBASE_PRIMER.md` — 2-paragraph project summary |

---

## Artifacts Created

### `.cursor/rules/` Directory

| File | Description | Globs |
|------|-------------|-------|
| `vue-composition.mdc` | Patterns for Vue 3 Composition API | `**/*.vue` |
| `neo4j-cypher.mdc` | Guardrails for Neo4j Cypher queries | `**/*.py` |
| `matrix-e2ee.mdc` | Matrix protocol E2EE crypto standards | `**/crypto/*.ts` |

### `CODEBASE_PRIMER.md`

High-level summary defining Current as:
- Offline-first Daoist astrology and alchemy PWA
- Vue 3 frontend with edge SQLite/IndexedDB
- Sync to central Neo4j graph
- DeepSeek for LLM synthesis

---

## Rationale

- **Modular rules**: Each rule applies only when matching files are open, conserving context window.
- **Frontmatter-driven**: `description` and `globs` enable precise rule selection and discovery.
- **Stack-specific guardrails**: Vue, Neo4j, and Matrix each have dedicated rules to enforce best practices and security (e.g., Cypher parameterization, spec-first E2EE).

---

## Files Touched

| File | Change |
|------|--------|
| `.cursor/rules/vue-composition.mdc` | Updated with 2026 standards |
| `.cursor/rules/neo4j-cypher.mdc` | Updated with 2026 standards |
| `.cursor/rules/matrix-e2ee.mdc` | Updated with 2026 standards |
| `src/components/canonical-example.vue` | Created |
| `docs/prompts/phase_3/task12.6_update.md` | Created |
| `CODEBASE_PRIMER.md` | Created |
| `docs/architecture/phase_3/Task12.6_CursorModernization.md` | Created |

---

## Future Work

- Add rules for Python backend conventions (e.g., `backend/**/*.py`)
- Add rules for TypeScript/Vite tooling if needed
- Consider `alwaysApply` rules for cross-cutting standards
