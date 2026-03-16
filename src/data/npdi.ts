/**
 * NPDI (18 Incompatibilities / Shi Ba Fan) - TCM herb contraindication pairs.
 * Herbs in the same incompatible pair should not be used together.
 *
 * Source: Shen Nong Ben Cao Jing, Wikibooks TCM Herb Interactions,
 * WHO Traditional Medicine strategy.
 */

/** Normalize pinyin for matching: lowercase, collapse spaces */
function norm(pinyin: string): string {
  return pinyin.trim().toLowerCase().replace(/\s+/g, " ");
}

/**
 * Map pinyin_name (and variants) to a canonical NPDI group key.
 * Herbs in the same group are treated as the same herb for NPDI purposes.
 */
const PINYIN_TO_CANONICAL: Record<string, string> = {
  // Gan Cao (Licorice) group
  "gan cao": "gan_cao",
  "zhi gan cao": "gan_cao",
  "sheng gan cao": "gan_cao",
  "gan cao gen": "gan_cao",
  // Purge / drainage herbs incompatible with Gan Cao
  "gan sui": "gan_sui",
  "da ji": "da_ji",
  "jing da ji": "da_ji",
  "hong da ji": "da_ji",
  "yuan hua": "yuan_hua",
  "hai zao": "hai_zao",
  "hai zhao": "hai_zao",
  // Wu Tou (Aconite) group
  "fu zi": "wu_tou",
  "chuan wu": "wu_tou",
  "cao wu": "wu_tou",
  "wu tou": "wu_tou",
  // Herbs incompatible with Wu Tou
  "ban xia": "ban_xia",
  "zhi ban xia": "ban_xia",
  "sheng ban xia": "ban_xia",
  "jiang ban xia": "ban_xia",
  "bai lian": "bai_lian",
  "bai ji": "bai_ji",
  "tian hua fen": "tian_hua_fen",
  "gua lou": "gua_lou",
  "gua lou pi": "gua_lou",
  "gua lou ren": "gua_lou",
  "gua lou shi": "gua_lou",
  "chuan bei mu": "chuan_bei_mu",
  "zhe bei mu": "zhe_bei_mu",
  // Li Lu and its incompatibles
  "li lu": "li_lu",
  "ren shen": "ren_shen",
  "bei sha shen": "bei_sha_shen",
  "nan sha shen": "nan_sha_shen",
  "ku shen": "ku_shen",
  "dan shen": "dan_shen",
  "xuan shen": "xuan_shen",
  "bai shao": "bai_shao",
  "chi shao": "chi_shao",
  "xi xin": "xi_xin",
  // 19 Antagonisms (Xiang Wu) - commonly checked alongside 18 Incompatibilities
  "rou gui": "rou_gui",
  "chi shi zhi": "chi_shi_zhi",
  "wu ling zhi": "wu_ling_zhi",
};

/** Incompatible pairs: [groupA, groupB] means herbs in groupA and groupB should not be combined */
const INCOMPATIBLE_PAIRS: [string, string][] = [
  // 18 Incompatibilities - Gan Cao group
  ["gan_cao", "gan_sui"],
  ["gan_cao", "da_ji"],
  ["gan_cao", "hai_zao"],
  ["gan_cao", "yuan_hua"],
  // 18 Incompatibilities - Wu Tou group
  ["wu_tou", "ban_xia"],
  ["wu_tou", "bai_lian"],
  ["wu_tou", "bai_ji"],
  ["wu_tou", "tian_hua_fen"],
  ["wu_tou", "gua_lou"],
  ["wu_tou", "chuan_bei_mu"],
  ["wu_tou", "zhe_bei_mu"],
  // 18 Incompatibilities - Li Lu group
  ["li_lu", "ren_shen"],
  ["li_lu", "bei_sha_shen"],
  ["li_lu", "nan_sha_shen"],
  ["li_lu", "ku_shen"],
  ["li_lu", "dan_shen"],
  ["li_lu", "xuan_shen"],
  ["li_lu", "bai_shao"],
  ["li_lu", "chi_shao"],
  ["li_lu", "xi_xin"],
  // 19 Antagonisms
  ["rou_gui", "chi_shi_zhi"],
  ["ren_shen", "wu_ling_zhi"],
];

function getCanonical(pinyin: string): string | null {
  const n = norm(pinyin);
  return PINYIN_TO_CANONICAL[n] ?? null;
}

/** Build a lookup: for each canonical key, which other keys are incompatible */
function buildIncompatibleMap(): Map<string, Set<string>> {
  const map = new Map<string, Set<string>>();
  for (const [a, b] of INCOMPATIBLE_PAIRS) {
    if (!map.has(a)) map.set(a, new Set());
    map.get(a)!.add(b);
    if (!map.has(b)) map.set(b, new Set());
    map.get(b)!.add(a);
  }
  return map;
}

const INCOMPATIBLE_MAP = buildIncompatibleMap();

export interface NPDIWarning {
  herbA: { id: string; pinyin_name: string; common_name: string };
  herbB: { id: string; pinyin_name: string; common_name: string };
  message: string;
}

/**
 * Check an array of herbs for 18 Incompatibilities (NPDI) / 19 Antagonisms.
 * Returns all pairs that violate the contraindication rules.
 */
export function checkNPDI(herbs: Array<{ id: string; pinyin_name: string; common_name: string }>): NPDIWarning[] {
  const warnings: NPDIWarning[] = [];
  const canonicalToHerbs = new Map<string, typeof herbs>();

  for (const herb of herbs) {
    const canon = getCanonical(herb.pinyin_name);
    if (canon) {
      if (!canonicalToHerbs.has(canon)) {
        canonicalToHerbs.set(canon, []);
      }
      canonicalToHerbs.get(canon)!.push(herb);
    }
  }

  const checked = new Set<string>();
  for (const [canonA, herbsA] of canonicalToHerbs) {
    const incompatibles = INCOMPATIBLE_MAP.get(canonA);
    if (!incompatibles) continue;

    for (const canonB of incompatibles) {
      const pairKey = [canonA, canonB].sort().join("|");
      if (checked.has(pairKey)) continue;
      checked.add(pairKey);

      const herbsB = canonicalToHerbs.get(canonB);
      if (!herbsB) continue;

      for (const a of herbsA) {
        for (const b of herbsB) {
          if (a.id === b.id) continue; // same herb, skip
          warnings.push({
            herbA: { id: a.id, pinyin_name: a.pinyin_name, common_name: a.common_name },
            herbB: { id: b.id, pinyin_name: b.pinyin_name, common_name: b.common_name },
            message: `${a.pinyin_name} (${a.common_name}) is incompatible with ${b.pinyin_name} (${b.common_name}) per 18 Incompatibilities (Shi Ba Fan) / 19 Antagonisms.`,
          });
        }
      }
    }
  }

  return warnings;
}
