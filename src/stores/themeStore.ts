import { defineStore } from "pinia";
import { computed, ref, watch } from "vue";

const LS_KEY = "current_almanac_chosen_skin_v1";

/** Must match `body[data-theme]` and theme CSS files in `src/assets/themes/`. */
export type ChosenSkin =
  | "daoist"
  | "classic-90s-os"
  | "cosmic-crawl"
  | "frostwire"
  | "monastic-terminal"
  | "old-school-aol"
  | "plaintext-brutalist"
  | "retro-terminal"
  | "tranceaddict-forum"
  | "vintage-print-almanac";

export const SKIN_OPTIONS: { id: ChosenSkin; label: string }[] = [
  { id: "daoist", label: "Daoist (default)" },
  { id: "classic-90s-os", label: "Classic 90s OS" },
  { id: "cosmic-crawl", label: "Cosmic crawl" },
  { id: "frostwire", label: "FrostWire" },
  { id: "monastic-terminal", label: "Monastic terminal" },
  { id: "old-school-aol", label: "Old-school AOL" },
  { id: "plaintext-brutalist", label: "Plaintext brutalist" },
  { id: "retro-terminal", label: "Retro terminal" },
  { id: "tranceaddict-forum", label: "TranceAddict forum" },
  { id: "vintage-print-almanac", label: "Vintage print almanac" },
];

function readStoredSkin(): ChosenSkin {
  try {
    const raw = localStorage.getItem(LS_KEY);
    if (raw && SKIN_OPTIONS.some((o) => o.id === raw)) return raw as ChosenSkin;
  } catch {
    /* ignore */
  }
  return "daoist";
}

function writeStoredSkin(skin: ChosenSkin) {
  try {
    localStorage.setItem(LS_KEY, skin);
  } catch {
    /* ignore */
  }
}

/** Which app chrome layout shell to render (structural HTML differences). */
export type ThemeLayoutKind = "default" | "frostwire" | "forum" | "classic90s" | "aol";

const SKIN_TO_LAYOUT: Record<ChosenSkin, ThemeLayoutKind> = {
  daoist: "default",
  "classic-90s-os": "classic90s",
  "cosmic-crawl": "default",
  frostwire: "frostwire",
  "monastic-terminal": "default",
  "old-school-aol": "aol",
  "plaintext-brutalist": "default",
  "retro-terminal": "default",
  "tranceaddict-forum": "forum",
  "vintage-print-almanac": "default",
};

/**
 * Optional Home (astrology) chrome per skin — keeps dense Win95/forum/AOL shells
 * free of the ambient water layer; cosmic gets crawl + starfield as its hero.
 */
export type SkinFeatureFlags = {
  /** River / brook background layer + wave/ripple/brook controls in the header */
  homeWaveLayer: boolean;
  /** Starfield CSS + scroll crawl backdrop (dialect-aware) */
  cosmicCrawlBackdrop: boolean;
};

export const SKIN_FEATURES: Record<ChosenSkin, SkinFeatureFlags> = {
  daoist: { homeWaveLayer: true, cosmicCrawlBackdrop: false },
  "cosmic-crawl": { homeWaveLayer: true, cosmicCrawlBackdrop: true },
  "classic-90s-os": { homeWaveLayer: false, cosmicCrawlBackdrop: false },
  frostwire: { homeWaveLayer: false, cosmicCrawlBackdrop: false },
  "monastic-terminal": { homeWaveLayer: true, cosmicCrawlBackdrop: false },
  "old-school-aol": { homeWaveLayer: false, cosmicCrawlBackdrop: false },
  "plaintext-brutalist": { homeWaveLayer: true, cosmicCrawlBackdrop: false },
  "retro-terminal": { homeWaveLayer: true, cosmicCrawlBackdrop: false },
  "tranceaddict-forum": { homeWaveLayer: false, cosmicCrawlBackdrop: false },
  "vintage-print-almanac": { homeWaveLayer: true, cosmicCrawlBackdrop: false },
};

/**
 * Apply theme to `document.body` for token CSS + optional classes (e.g. cosmic starfield).
 */
export function applyBodyTheme(skin: ChosenSkin) {
  if (typeof document === "undefined") return;
  document.body.dataset.theme = skin;
  const html = document.documentElement;
  const lightSkins: ChosenSkin[] = [
    "classic-90s-os",
    "frostwire",
    "old-school-aol",
    "plaintext-brutalist",
    "vintage-print-almanac",
  ];
  html.style.colorScheme = lightSkins.includes(skin) ? "light" : "dark";
}

export const useThemeStore = defineStore("theme", () => {
  const chosenSkin = ref<ChosenSkin>(readStoredSkin());

  const layoutKind = computed(() => SKIN_TO_LAYOUT[chosenSkin.value]);

  const skinFeatures = computed(() => SKIN_FEATURES[chosenSkin.value]);

  function setChosenSkin(skin: ChosenSkin) {
    chosenSkin.value = skin;
    writeStoredSkin(skin);
    applyBodyTheme(skin);
  }

  watch(
    chosenSkin,
    (s) => {
      applyBodyTheme(s);
    },
    { immediate: true }
  );

  return {
    chosenSkin,
    layoutKind,
    skinFeatures,
    setChosenSkin,
    /** Idempotent: re-apply body classes (e.g. after navigation). */
    syncDocumentTheme() {
      applyBodyTheme(chosenSkin.value);
    },
  };
});
