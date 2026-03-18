# Subagent Directive: Task 12.6 2026 Modernization Guardrails

**Domain:** Phase 3.5 — AI-Native Architecture Governance
**Task:** Align `.cursor/rules` with 2026 Elite Workflow Standard and complete Task 12.6
**Context:** The Jun requires full adherence to the "Convergence of Agentic Orchestration" standards. Our current `.mdc` files are missing several domain-specific guardrails.

**Action:**
1. Read `.cursor/rules/vue-composition.mdc`, `.cursor/rules/neo4j-cypher.mdc`, and `.cursor/rules/matrix-e2ee.mdc`.
2. Update `vue-composition.mdc` to mandate Framer Motion for animations and reference `src/components/canonical-example.vue` for props and exports.
3. Create `src/components/canonical-example.vue` with a perfect TypeScript strict `<script setup>` pattern, Tailwind styling, and a documented props interface to serve as our architectural anchor.
4. Update `neo4j-cypher.mdc` to include: Weakly Connected Components (WCC) for large refactors, a hard limit on variable-length patterns (e.g., `*1..5`), and GQL-compliant aliases. Add a rule requiring a "Mapping Manifest" when mapping Neo4j to SQLite/relational to prevent schema hallucinations.
5. Update `matrix-e2ee.mdc` to explicitly forbid logging/exporting private keys, treat `m.room.encryption` as permanent to stop MITM attacks, and enforce a 10-minute maximum age and valid transaction ID on `m.key.verification.start` messages.

**Requirements:**
- Do not delete the existing rules in the files (like parameterized queries or `vodozemac` mandates); append the new guardrails logically.
- Ensure the frontmatter descriptions perfectly align with the 2026 template intent.

**When complete, verify your changes and report back.**