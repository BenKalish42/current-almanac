import { defineStore } from "pinia";
import { computed } from "vue";
import { Lunar } from "lunar-javascript";
import { useAppStore } from "@/stores/appStore";
import { parseGanZhi } from "@/core/ganzhi";
import type { Element } from "@/core/ganzhi";

/** Pinyin for stems and branches (tonal) */
const STEM_PINYIN: Record<string, string> = {
  甲: "Jiǎ", 乙: "Yǐ", 丙: "Bǐng", 丁: "Dīng", 戊: "Wù",
  己: "Jǐ", 庚: "Gēng", 辛: "Xīn", 壬: "Rén", 癸: "Guǐ",
};
const BRANCH_PINYIN: Record<string, string> = {
  子: "Zǐ", 丑: "Chǒu", 寅: "Yín", 卯: "Mǎo", 辰: "Chén",
  巳: "Sì", 午: "Wǔ", 未: "Wèi", 申: "Shēn", 酉: "Yǒu",
  戌: "Xū", 亥: "Hài",
};

export type PillarItem = {
  hanzi: string;
  pinyin: string;
  wuXing: Element;
};

export type BaZiPillar = {
  label: "Year" | "Month" | "Day" | "Hour";
  stem: PillarItem;
  branch: PillarItem;
};

function gzToPillarItems(gz: string | null | undefined): { stem: PillarItem | null; branch: PillarItem | null } {
  if (!gz || gz.length < 2) return { stem: null, branch: null };
  const parsed = parseGanZhi(gz);
  if (!parsed.stem || !parsed.branch) return { stem: null, branch: null };
  return {
    stem: {
      hanzi: parsed.stem.char,
      pinyin: STEM_PINYIN[parsed.stem.char] ?? parsed.stem.char,
      wuXing: parsed.stem.element,
    },
    branch: {
      hanzi: parsed.branch.char,
      pinyin: BRANCH_PINYIN[parsed.branch.char] ?? parsed.branch.char,
      wuXing: parsed.branch.element,
    },
  };
}

export const useAstrologyStore = defineStore("astrology", () => {
  const appStore = useAppStore();

  const fourPillars = computed<BaZiPillar[]>(() => {
    const date = appStore.selectedDate;
    if (!date || Number.isNaN(date.getTime())) return [];

    const lunar = Lunar.fromDate(date);

    const yearGZ = lunar.getYearInGanZhi?.() ?? "";
    const monthGZ = lunar.getMonthInGanZhi?.() ?? "";
    const dayGZ = lunar.getDayInGanZhi?.() ?? "";
    const hourGZ = (lunar as { getTimeInGanZhi?: () => string }).getTimeInGanZhi?.()
      ?? (lunar as { getHourInGanZhi?: () => string }).getHourInGanZhi?.()
      ?? "";

    const labels: BaZiPillar["label"][] = ["Year", "Month", "Day", "Hour"];
    const gzList = [yearGZ, monthGZ, dayGZ, hourGZ];

    return gzList.map((gz, i) => {
      const { stem, branch } = gzToPillarItems(gz);
      return {
        label: labels[i]!,
        stem: stem ?? { hanzi: "—", pinyin: "", wuXing: "Earth" as Element },
        branch: branch ?? { hanzi: "—", pinyin: "", wuXing: "Earth" as Element },
      };
    });
  });

  return { fourPillars };
});
