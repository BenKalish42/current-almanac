# State of the Architecture — Current Almanac

**Generated:** March 11, 2025  
**Purpose:** Share with external AI CTO for architecture review.

---

## 1. Project Structure

```
current-almanac/
├── src/
│   ├── App.vue                    # App shell, nav (Astrology | Alchemy | Intelligence)
│   ├── main.ts                    # Vue 3 + Pinia + Router + Capacitor init
│   ├── style.css                  # Global styles, Tailwind entry
│   ├── router/
│   │   └── index.ts               # Vue Router config
│   ├── stores/
│   │   ├── appStore.ts            # Astrology, readings, interpretation
│   │   └── pantryStore.ts        # Practitioner Pantry (herb inventory)
│   ├── views/
│   │   ├── HomeView.vue           # Astrology (Yi Jing, BaZi, Qimen, etc.)
│   │   ├── AlchemyView.vue       # Dual Cultivation (Wei Dan + Nei Dan)
│   │   └── AIChatView.vue        # Chat with Zhuang (DeepSeek)
│   ├── components/
│   │   ├── BirthProfilePanel.vue
│   │   ├── CosmicBoard.vue
│   │   ├── DaLiuRenBoard.vue
│   │   ├── GanzhiSeal.vue
│   │   ├── HelloWorld.vue
│   │   ├── HexagramLines.vue
│   │   ├── HexagramModal.vue
│   │   ├── JingBattery.vue
│   │   ├── QimenChart.vue
│   │   ├── QMDJBoard.vue
│   │   ├── TaiYiBoard.vue
│   │   └── ...
│   ├── core/                      # Astrology / Yi Jing logic
│   │   ├── advancedAstro.ts
│   │   ├── daliuren.ts
│   │   ├── ganzhi.ts
│   │   ├── hexagramsXKDG.ts
│   │   ├── hexagramsTemporal.ts
│   │   ├── iching.ts
│   │   ├── qimen.ts
│   │   ├── taiyi.ts
│   │   └── zwds.ts
│   ├── composables/
│   │   └── useChat.ts             # AI chat (fetch + SSE)
│   ├── services/
│   │   ├── alchemyApi.ts          # Formula, override-check, merge-formulas
│   │   └── pantryApi.ts           # Pantry fetch/toggle
│   ├── lib/
│   │   └── personal/
│   │       └── baziNineStar.ts
│   ├── types/
│   │   └── astrology.ts
│   └── data/
│       ├── seed_formulas.json     # Alchemy formulas (Jun/Chen/Zuo/Shi)
│       ├── seed_herbs.json        # Alchemy herbs (TCM-style)
│       ├── seed_neidan.json       # Nei Dan practices
│       ├── seed_hexagrams.json    # Hexagram perspectives
│       └── hexagramSummaries.json
│
├── scripts/
│   ├── 01_scrape_legge.py
│   ├── 02_parse_books.py
│   ├── 03_ai_synthesizer.py
│   ├── 04_scrape_ctext.py
│   ├── 05_extract_formulas.py
│   ├── 06_scrape_snbcj_hdnj.py
│   ├── 07_build_master_herbs.py
│   ├── 07_scrape_daoist_canon.py
│   ├── 07_transform_formulas_for_alchemy.py
│   ├── 08_build_graph.py          # Neo4j ingestion (herbs/formulas)
│   ├── 08_scrape_wikisource.py
│   ├── 09_enrich_linguistics.py
│   ├── hexagram_summaries_pipeline.py
│   ├── deploy_to_benkalish.sh
│   └── requirements.txt          # Python deps (neo4j, pandas, openai, etc.)
│
├── data/
│   ├── raw/                       # Scraped TCM texts, SymMap CSV/XLSX
│   ├── chunked/                   # Hexagram chunks by perspective
│   │   ├── daoist_1_cleary/
│   │   ├── confucian_1_cleary/
│   │   ├── buddhist_1_cleary/
│   │   ├── psychological_1_wilhelm/
│   │   ├── human_design_1_ra/
│   │   ├── gene_keys_1_rudd/
│   │   └── ...
│   └── output/
│       ├── seed_herbs.json        # SymMap-style herbs (for Neo4j)
│       ├── seed_formulas.json    # Neo4j-style formulas (herb_pinyin)
│       └── enriched_herbs.json
│
├── backend/
│   ├── main.py                    # FastAPI app
│   ├── db.py                      # Supabase + seed JSON fallback
│   ├── schemas.py                 # Pydantic models
│   ├── core/
│   │   └── safety.py
│   └── services/
│       ├── alchemy_math.py
│       └── llm_service.py        # DeepSeek (interpret, chat)
│
├── docker-compose.yml             # Neo4j only (7474, 7687)
├── package.json
├── vite.config.ts
└── capacitor.config.ts
```

---

## 2. Tech Stack & Dependencies

### Frontend (`package.json`)

| Category | Package | Version |
|----------|---------|---------|
| **Framework** | Vue | ^3.5.24 |
| **State** | Pinia | ^3.0.4 |
| **Routing** | vue-router | ^5.0.3 |
| **Styling** | Tailwind CSS | ^4.2.1 |
| **Build** | Vite | ^7.2.4 |
| **AI UI** | @ai-sdk/vue | ^3.0.97 |
| **Astrology** | lunar-typescript | ^1.8.6 |
| **Astrology** | lunar-javascript | ^1.7.7 |
| **Astrology** | iztro | ^2.5.7 |

### Capacitor (Mobile)

- **@capacitor/core**, **ios**, **android** — ^7.0.0
- **@capacitor/splash-screen**, **status-bar** — ^7.0.0
- App ID: `com.current.almanac`

### Backend (Python)

- **FastAPI** — API server
- **Supabase** — Primary DB (herbs, formulas, formula_architecture, nei_dan_practices, user_pantry)
- **OpenAI-compatible client** — DeepSeek API (interpret, chat)
- **Pydantic** — Request/response schemas

### Scripts / Data Pipeline

- **neo4j** (Python driver) — Used only by `08_build_graph.py`; **not** in frontend or backend
- **pandas**, **beautifulsoup4**, **openpyxl** — Scraping and data transformation
- **openai** — AI synthesis (hexagram summaries, etc.)

### Notable Absences

- **No Neo4j driver in frontend** — Graph data is not consumed by the app yet
- **No Neo4j in backend** — Backend uses Supabase + JSON fallback only

---

## 3. Frontend Routing & Views

| Path | Name | Component | Description |
|------|------|-----------|-------------|
| `/` | — | redirect | → `/astrology` |
| `/astrology` | astrology | `HomeView.vue` | Daoist astrology: BaZi, Yi Jing, Qimen, Zi Wei Dou Shu, organ clock |
| `/alchemy` | alchemy | `AlchemyView.vue` | Dual Cultivation: Wei Dan (herbal formulas) + Nei Dan (internal practices) |
| `/ai` | ai | `AIChatView.vue` | Chat with Zhuang (DeepSeek streaming) |

### Nav Labels (from `App.vue`)

- **Astrology** → HomeView
- **Alchemy** → AlchemyView
- **Intelligence** → AIChatView

### Key Components by View

- **Astrology:** `HexagramLines`, `HexagramModal`, `CosmicBoard`, `BirthProfilePanel`, `GanzhiSeal`, `JingBattery`, `QimenChart`, `TaiYiBoard`, `DaLiuRenBoard`, `QMDJBoard`
- **Alchemy:** Uses `seedHerbs`, `seedFormulas` from `@/data/`, `JingBattery`, backend API for prescriptions
- **AI Chat:** `useChat` composable, SSE to `/api/chat`

---

## 4. State Management (Pinia)

### Store 1: `appStore` (`stores/appStore.ts`)

**Purpose:** Astrology context, readings, interpretation, user state.

| Type | Name | Description |
|------|------|-------------|
| **State** | `dateISO`, `timeHHMM`, `location`, `geoCoords`, `timezoneLabel` | Moment (present) inputs |
| | `presentAuto` | Sync time to now |
| | `birthDatetimeLocal`, `birthSect`, `userGender` | Birth data |
| | `intentDomain`, `intentGoalConstraint` | User intent |
| | `userCapacity`, `userLoad`, `userSleepQuality`, `userCognitiveNoise`, `userSocialLoad`, `userEmotionalTone` | User state (0–10) |
| | `log`, `activeReading` | Readings |
| | `interpretationPlaceholder`, `interpretationLoading`, `interpretationBaZiSignature` | AI interpretation |
| **Computed** | `selectedDate`, `birthProfile`, `temporalHex`, `birthTemporalHex` | Calendar / astro |
| | `qimenChartHour`, `qimenChartDay` | Qimen charts |
| | `advancedAstroMoment`, `advancedAstroBirth`, `zwdsMatrix` | Extended astro |
| | `presentOrgan` | Organ clock |
| | `interpretationNeedsRefresh`, `currentBaZiSignature` | Interpretation staleness |
| **Actions** | `loadFromStorage`, `persistUserState` | Persistence |
| | `syncLocalTimeNow`, `shiftPresentHours`, `togglePresentAuto` | Time controls |
| | `hydrateFromGeolocation`, `fetchWeatherSnapshot` | Location / weather |
| | `generate`, `clearLog`, `setActiveReading` | Readings |
| | `requestInterpretation`, `serializeForApi` | Backend interpretation |

### Store 2: `pantryStore` (`stores/pantryStore.ts`)

**Purpose:** Practitioner Pantry (which herbs are in stock).

| Type | Name | Description |
|------|------|-------------|
| **State** | `inventory` | `Map<herb_id, boolean>` (in stock) |
| | `loading`, `error` | UI state |
| | `userId` | From `localStorage` or `crypto.randomUUID()` |
| **Computed** | `isHerbInStock(herbId)` | Check if herb is in stock |
| **Actions** | `fetchInventory()` | GET `/api/pantry` |
| | `toggleHerb(herbId)` | POST `/api/pantry/toggle` |

---

## 5. Data Layer & Neo4j

### How the App Accesses Daoist Data

| Layer | Source | Details |
|-------|--------|---------|
| **Backend** | Supabase | Primary: `herbs`, `formulas`, `formula_architecture`, `nei_dan_practices`, `user_pantry` |
| **Backend** | Seed JSON (fallback) | `src/data/seed_herbs.json`, `seed_formulas.json`, `seed_neidan.json` when Supabase unavailable |
| **Frontend** | Static imports | `AlchemyView` imports `@/data/seed_herbs.json`, `@/data/seed_formulas.json` for local lookup/search |
| **Frontend** | Backend API | Formula prescriptions, override checks, merge, pantry via `VITE_API_URL` (or dev proxy) |

### Neo4j Status

- **Docker:** `docker-compose up -d` runs Neo4j on ports 7474 (browser) and 7687 (bolt).
- **Script:** `scripts/08_build_graph.py` ingests `data/output/seed_herbs.json` and `data/output/seed_formulas.json` into Neo4j (Herb, Formula, Meridian nodes; INCLUDED_IN, ENTERS relationships).
- **App usage:** **No** frontend or backend code connects to Neo4j. The graph is built but not queried by the app.

### Seed File Locations

| File | In Project? | Used By |
|------|-------------|---------|
| `src/data/seed_herbs.json` | ✅ | Backend fallback, AlchemyView |
| `src/data/seed_formulas.json` | ✅ | Backend fallback, AlchemyView |
| `src/data/seed_neidan.json` | ✅ | Backend fallback |
| `data/output/seed_herbs.json` | ✅ | `08_build_graph.py` (Neo4j) |
| `data/output/seed_formulas.json` | ✅ | `08_build_graph.py` (Neo4j) |
| `data/output/enriched_herbs.json` | ✅ | Pipeline output; not wired into app |

### API Base URL

- **Build:** `VITE_API_URL` (e.g. `https://your-backend.onrender.com`)
- **Dev:** Vite proxy sends `/api` to `http://localhost:8000` when `VITE_API_URL` is unset

---

## 6. Data Schemas

### Herb (Alchemy — `src/data/seed_herbs.json`)

```json
{
  "id": "herb_001",
  "pinyin_name": "Ren Shen",
  "common_name": "Ginseng Root",
  "safety_tier": 2,
  "properties": {
    "temperature": "Slightly Warm",
    "flavor": ["Sweet", "Slightly Bitter"],
    "meridians": ["Heart", "Lung", "Spleen"]
  },
  "actions": [
    "Powerfully tonifies Primal Qi (Yuan Qi)",
    "Strengthens Spleen and tonifies Stomach"
  ],
  "contraindications": "Incompatible with Li Lu..."
}
```

**Keys:** `id`, `pinyin_name`, `common_name`, `safety_tier`, `properties` (temperature, flavor, meridians), `actions`, `contraindications`.

### Herb (SymMap / Neo4j — `data/output/seed_herbs.json`)

```json
{
  "id": "herb_sym_001",
  "pinyin_name": "Aidicha",
  "chinese_name": "矮地茶",
  "english_name": "Japanese Ardisia Herb",
  "meridians": ["Lung", "Liver"],
  "properties": ["Pungent", "Slightly Bitter", "Calm"],
  "safety_tier": 1,
  "external_ids": {
    "TCMSP_id": "1",
    "TCMID_id": "5072"
  }
}
```

**Keys:** `id`, `pinyin_name`, `chinese_name`, `english_name`, `meridians`, `properties`, `safety_tier`, `external_ids`.

### Formula (Alchemy — `src/data/seed_formulas.json`)

```json
{
  "id": "form_shl_001",
  "pinyin_name": "Gui Zhi Tang",
  "common_name": "Cinnamon Twig Decoction",
  "primary_pattern": "Taiyang Wind-Strike (Deficiency)",
  "actions": ["Releases the exterior", "Harmonizes Ying and Wei"],
  "architecture": [
    {
      "role": "King (Jun)",
      "herb_id": "herb_gui_zhi",
      "pinyin_name": "Gui Zhi",
      "purpose": "Releases the exterior",
      "dosage_percentage": 26.98
    }
  ],
  "safety_note": ""
}
```

**Keys:** `id`, `pinyin_name`, `common_name`, `primary_pattern`, `actions`, `architecture` (role, herb_id, pinyin_name, purpose, dosage_percentage), `safety_note`.

---

## Summary for CTO

| Area | Status |
|------|--------|
| **Frontend** | Vue 3 + Pinia + Tailwind; three main views (Astrology, Alchemy, AI Chat) |
| **Backend** | FastAPI; Supabase + JSON seed fallback; **no Neo4j** |
| **Neo4j** | Ingested via script; **not** used by app |
| **Data consistency** | Two herb schemas (alchemy vs SymMap) and two formula architectures (herb_id vs herb_pinyin) |
| **AI** | DeepSeek for interpretation and chat; requires `DEEPSEEK_API_KEY` |
| **Mobile** | Capacitor 7; iOS/Android config present |

**Recommendation:** To use Neo4j in the product, add backend Neo4j queries and/or a GraphQL or REST layer that exposes graph data. The current design is Supabase/JSON-first.
