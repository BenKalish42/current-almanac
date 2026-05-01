# Current — v1

> *Current makes the structure of the moment visible, so the user stops forcing
> what isn't ready and stops missing what already is.*

---

## What Current is

A timing instrument. It describes the configuration of conditions in the
present moment, clarifies how effort interacts with those conditions, and
reduces friction, mistiming, and unnecessary force.

It does not predict outcomes. It does not prescribe actions. It does not
assign meaning, morality, or destiny.

A correct reading does not tell you what to do. It makes the structure of
the moment visible enough that unnecessary action drops away.

---

## Three pillars

### Pillar 1 — Astrology (the cosmic blueprint)

The natal **Four Pillars (BaZi)** + present-moment pillars, the **Nine
Palaces matrix** (Lo Shu / Mewa / Nine Star Ki — multi-tradition stack),
the **Vedic chart** (Lahiri sidereal: Lagna + planetary positions +
Nakshatras), and the **Hourglass timer** that tracks the boundary of
the active two-hour Shi or fifteen-minute Ke. **Synthesize the Heavens**
fires the contract-bound Oracle.

### Pillar 2 — Alchemy (the earthly vessel)

The **Eight Principles (Ba Gang)** symptom matrix — Hot/Cold, Wet/Dry,
Deficient/Excess, Interior/Exterior. The **Alchemical Graph** renders
the local triplestore subgraph for the current configuration. The
**Ontology Lens** swaps vocabulary between TCM and Ayurveda without
touching the underlying graph. **Synthesize the Earth** fires the
contract-bound Apothecary; it describes the configuration, never
prescribes.

### Pillar 3 — Sovereign Courtyard

A local Ed25519 **Identity Forge**: device generates a key pair, public
key is rendered as a deterministic glyph talisman. The Courtyard shell
is in place; live peer-to-peer Matrix exchange activates when
`VITE_MATRIX_HOMESERVER_URL` is set (off by default).

---

## Output Contract

Every LLM call wraps with `OUTPUT_CONTRACT_SYSTEM`. Every reply is
audited; on violation we attempt a single revise; failure redacts. The
non-action phrase — *"No dominant signal. Maintain course."* — is a
first-class, surface-able output.

The contract forbids: instructions, predictions, moral framing,
destiny / agency, and mystical inflation. It allows: Flow, Resistance,
Pressure, Timing, Direction, Phase, Capacity, Load, Auspiciousness
(defined as *low friction*), Misalignment Signals, Non-action.

---

## Architecture

- Vue 3 + Pinia + Tailwind + Vite + Capacitor 7.
- Backend: FastAPI + LiteLLM (Claude / ChatGPT / Gemini / DeepSeek).
- Local triplestore: 13 node labels, 14 edge types — projects Chen's
  Master Knowledge Graph onto in-memory + localStorage in v1; Dexie /
  Capacitor SQLite slot in via the `TriplestoreStorage` interface.
- RAG traversal: 7 steps for Earth, 5 for Heavens — the Oracle is told
  the JSON is canonical and never recomputes math.
- Output Contract: `data/contracts/forbidden.json` + TS mirror + Python
  mirror; CI sync test ensures all three agree.

---

## Test discipline

- 147 unit tests at v1.0.0-rc.1.
- Math fixtures lock BaZi, Nine Star, EoT/solar-time, Vedic rāśi tables,
  hexagram XKDG.
- Output Contract is enforced at three levels: prepended to every LLM
  call, audited on every reply, and audited at build time across the
  Nine Palaces dictionary and Oracle prompt builders.
- Bundle budget: `tests/perf/bundle-budget.spec.ts` fails if the eager
  bundle exceeds 1400 KB gz (current: ~921 KB).

---

## What's deliberately deferred to v1.1

- Auth + subscriptions (parked on `defer/v1.1-accounts`; conflicts with
  the no-accounts ethos until the Jun lifts the bar).
- Live Matrix federation (Tier B in Pillar 3 — homeserver flag stays
  unset; revival from `archive/community-legacy-2026/`).
- Encrypted Payload, Communal Reading, Synaptic Mesh — placeholders ship,
  active wiring is v1.1.
- Full ephemeris (`swisseph` / Vedic fixtures within ±0.05° ayanamsa).
- Store publishing — workflows scaffolded; publish steps `if: false`-gated.

---

## One-line summary

**A description engine for a timing instrument. Honest about its limits.**
