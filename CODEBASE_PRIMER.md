# Current — Codebase Primer

**Current** is an offline-first, Daoist astrology and alchemy PWA. It centers on the Zi Wei Dou Shu (紫微斗數) and I Ching (易經) traditions, providing birth charts, hexagram readings, and synthesized insights. The frontend is built with Vue 3 and a Composition API architecture, using Tailwind CSS for styling, and runs on Capacitor for mobile deployment.

The data layer uses edge SQLite and IndexedDB for local storage with offline capability, syncing to a central Neo4j graph database for knowledge representation and relationship traversal. LLM synthesis is powered by DeepSeek to generate interpretations and commentary from the structured graph data.
