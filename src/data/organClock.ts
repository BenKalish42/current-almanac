/**
 * TCM Organ Clock (Shichen) — 12 two-hour blocks mapping Earthly Branches to organs.
 * Used for temporal diagnostics and Neidan cultivation awareness.
 */

export type WuXingElement = "Wood" | "Fire" | "Earth" | "Metal" | "Water";

export type OrganHourEntry = {
  branch: string;
  branchCn: string;
  startHour: number;
  endHour: number;
  organ: string;
  organHanzi: string;
  organPinyin: string;
  spiritName: string;
  physiological: string;
  neidanSpirit: string;
  wuXing: WuXingElement;
};

/** 12 Shichen entries in order (Zi → Chou → … → Hai) */
export const ORGAN_CLOCK: OrganHourEntry[] = [
  {
    branch: "Zi",
    branchCn: "子",
    startHour: 23,
    endHour: 1,
    organ: "Gallbladder",
    organHanzi: "胆",
    organPinyin: "Dǎn",
    spiritName: "Dan (Courage) / Hun",
    physiological:
      "Gallbladder stores and excretes bile; supports decision-making and courage in TCM. Peak metabolic clearing.",
    neidanSpirit: "The decisive yang rises; clarity of intent for the day ahead.",
    wuXing: "Wood",
  },
  {
    branch: "Chou",
    branchCn: "丑",
    startHour: 1,
    endHour: 3,
    organ: "Liver",
    organHanzi: "肝",
    organPinyin: "Gān",
    spiritName: "Hun (Ethereal Soul)",
    physiological: "Liver stores blood, regulates Qi flow, smooths emotions. Blood detoxification and renewal.",
    neidanSpirit: "Hun (魂) — the ethereal soul; dreams, vision, and planning awaken.",
    wuXing: "Wood",
  },
  {
    branch: "Yin",
    branchCn: "寅",
    startHour: 3,
    endHour: 5,
    organ: "Lung",
    organHanzi: "肺",
    organPinyin: "Fèi",
    spiritName: "Po (Corporeal Soul)",
    physiological: "Lung governs Qi, controls respiration and defensive Qi. Deep breathing and renewal.",
    neidanSpirit: "Po (魄) — the corporeal soul; physical vitality and boundaries.",
    wuXing: "Metal",
  },
  {
    branch: "Mao",
    branchCn: "卯",
    startHour: 5,
    endHour: 7,
    organ: "Large Intestine",
    organHanzi: "大肠",
    organPinyin: "Dàcháng",
    spiritName: "Letting go (Serves the Po)",
    physiological: "Large Intestine receives waste, excretes, and supports letting go.",
    neidanSpirit: "Release and purification; clearing the old to receive the new.",
    wuXing: "Metal",
  },
  {
    branch: "Chen",
    branchCn: "辰",
    startHour: 7,
    endHour: 9,
    organ: "Stomach",
    organHanzi: "胃",
    organPinyin: "Wèi",
    spiritName: "Yi (Intellect)",
    physiological: "Stomach receives and ripens food; the source of postnatal Qi.",
    neidanSpirit: "Receiving and transforming; foundation for the day's nourishment.",
    wuXing: "Earth",
  },
  {
    branch: "Si",
    branchCn: "巳",
    startHour: 9,
    endHour: 11,
    organ: "Spleen",
    organHanzi: "脾",
    organPinyin: "Pí",
    spiritName: "Yi (Intellect)",
    physiological: "Spleen transforms and transports; governs thought, memory, and digestion.",
    neidanSpirit: "Yi (意) — intention and focused thought; clarity of mind.",
    wuXing: "Earth",
  },
  {
    branch: "Wu",
    branchCn: "午",
    startHour: 11,
    endHour: 13,
    organ: "Heart",
    organHanzi: "心",
    organPinyin: "Xīn",
    spiritName: "Shen (Mind/Spirit)",
    physiological: "Heart governs blood and houses the mind; circulates vitality and awareness.",
    neidanSpirit: "Shen (神) — the spirit; consciousness, joy, and connection.",
    wuXing: "Fire",
  },
  {
    branch: "Wei",
    branchCn: "未",
    startHour: 13,
    endHour: 15,
    organ: "Small Intestine",
    organHanzi: "小肠",
    organPinyin: "Xiǎocháng",
    spiritName: "Shen (Mind/Spirit)",
    physiological: "Small Intestine separates pure from turbid; discernment and absorption.",
    neidanSpirit: "Discernment — sorting what serves from what does not.",
    wuXing: "Fire",
  },
  {
    branch: "Shen",
    branchCn: "申",
    startHour: 15,
    endHour: 17,
    organ: "Bladder",
    organHanzi: "膀胱",
    organPinyin: "Pángguāng",
    spiritName: "Zhi (Willpower)",
    physiological: "Bladder stores and excretes urine; governs fluid metabolism.",
    neidanSpirit: "Water pathways; flow and release of what no longer serves.",
    wuXing: "Water",
  },
  {
    branch: "You",
    branchCn: "酉",
    startHour: 17,
    endHour: 19,
    organ: "Kidney",
    organHanzi: "肾",
    organPinyin: "Shèn",
    spiritName: "Zhi (Willpower)",
    physiological: "Kidney stores essence (Jing), governs water, and anchors Yuan Qi.",
    neidanSpirit: "Zhi (志) — willpower and perseverance; the root of life force.",
    wuXing: "Water",
  },
  {
    branch: "Xu",
    branchCn: "戌",
    startHour: 19,
    endHour: 21,
    organ: "Pericardium",
    organHanzi: "心包",
    organPinyin: "Xīnbāo",
    spiritName: "Shen (Mind/Spirit)",
    physiological: "Pericardium protects the Heart and governs blood circulation through the chest.",
    neidanSpirit: "The protector; boundaries and emotional shielding.",
    wuXing: "Fire",
  },
  {
    branch: "Hai",
    branchCn: "亥",
    startHour: 21,
    endHour: 23,
    organ: "San Jiao",
    organHanzi: "三焦",
    organPinyin: "Sānjiāo",
    spiritName: "Shen (Mind/Spirit)",
    physiological: "San Jiao (Triple Burner) regulates waterways and the three body cavities.",
    neidanSpirit: "Integration of upper, middle, lower; preparing for rest and renewal.",
    wuXing: "Fire",
  },
];

/**
 * Returns the active organ-hour entry for a given 24-hour clock hour (0–23).
 * Handles the Zi block (23–01) wrapping midnight.
 */
export function getCurrentOrganHour(hour24: number): OrganHourEntry {
  const defaultEntry = ORGAN_CLOCK[0]!;
  if (hour24 >= 23 || hour24 < 1) return defaultEntry; // Zi
  for (const e of ORGAN_CLOCK) {
    if (e.startHour === 23) continue; // Zi already handled
    if (hour24 >= e.startHour && hour24 < e.endHour) return e;
  }
  return defaultEntry;
}
