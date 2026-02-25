/**
 * Full serialization of Lunar + EightChar from lunar-typescript.
 * Dumps Shen Sha, 24 Solar Terms, Peng Zu, Day Officers, Na Yin, hidden stems, Tai Yi, Da Liu Ren.
 * For hidden AI context payload only — no UI display.
 */
import type { EightChar, JieQi, Lunar, LunarTime, Solar } from "lunar-typescript";
import { computeTaiYi } from "./taiyi";
import { computeDaLiuRen } from "./daliuren";

/** Safe getter that returns null instead of throwing. */
function safe<T>(fn: () => T): T | null {
  try {
    return fn();
  } catch {
    return null;
  }
}

/** Serialize a JieQi (24 Solar Terms) entry. */
function serializeJieQi(jq: JieQi): Record<string, unknown> | null {
  try {
    const solar = jq.getSolar?.();
    return {
      name: jq.getName?.(),
      is_jie: jq.isJie?.(),
      is_qi: jq.isQi?.(),
      solar_ymd: solar?.toYmd?.() ?? null,
    };
  } catch {
    return null;
  }
}

/** Serialize EightChar pillar data (year, month, day, time). */
function serializePillar(
  ec: EightChar,
  prefix: "Year" | "Month" | "Day" | "Time"
): Record<string, unknown> {
  const getGan = ec[`get${prefix}Gan`] as (() => string) | undefined;
  const getZhi = ec[`get${prefix}Zhi`] as (() => string) | undefined;
  const getHideGan = ec[`get${prefix}HideGan`] as (() => string[]) | undefined;
  const getWuXing = ec[`get${prefix}WuXing`] as (() => string) | undefined;
  const getNaYin = ec[`get${prefix}NaYin`] as (() => string) | undefined;
  const getShiShenGan = ec[`get${prefix}ShiShenGan`] as (() => string) | undefined;
  const getShiShenZhi = ec[`get${prefix}ShiShenZhi`] as (() => string[]) | undefined;
  const getDiShi = ec[`get${prefix}DiShi`] as (() => string) | undefined;
  const getXun = ec[`get${prefix}Xun`] as (() => string) | undefined;
  const getXunKong = ec[`get${prefix}XunKong`] as (() => string) | undefined;

  return {
    gan_zhi: `${getGan?.() ?? ""}${getZhi?.() ?? ""}`.trim() || null,
    gan: safe(() => getGan?.()),
    zhi: safe(() => getZhi?.()),
    hide_gan: safe(() => getHideGan?.()) ?? [],
    wu_xing: safe(() => getWuXing?.()),
    na_yin: safe(() => getNaYin?.()),
    shi_shen_gan: safe(() => getShiShenGan?.()),
    shi_shen_zhi: safe(() => getShiShenZhi?.()) ?? [],
    di_shi: safe(() => getDiShi?.()),
    xun: safe(() => getXun?.()),
    xun_kong: safe(() => getXunKong?.()),
  };
}

/**
 * Serialize the entire Lunar and EightChar objects into a clean advanced_astro JSON.
 * Includes: Shen Sha, 24 Solar Terms, Peng Zu taboos, Day Officers, Na Yin, hidden stems.
 */
export function serializeAdvancedAstro(
  lunar: Lunar,
  eightChar: EightChar,
  sect: number = 2
): Record<string, unknown> {
  const solar = safe(() => lunar.getSolar?.());
  const jieQiTable = safe(() => lunar.getJieQiTable?.()) ?? {};
  const jieQiList = safe(() => lunar.getJieQiList?.()) ?? [];

  const jieQiEntries = Object.entries(jieQiTable).map(([name, s]) => ({
    name,
    solar_ymd: (s as Solar)?.toYmd?.() ?? null,
  }));

  const nextJieQi = safe(() => lunar.getNextJieQi?.());
  const prevJieQi = safe(() => lunar.getPrevJieQi?.());
  const currentJieQi = safe(() => lunar.getCurrentJieQi?.());

  const timeObj = safe(() => lunar.getTime?.()) as LunarTime | null;

  return {
    lunar_basic: {
      year: safe(() => lunar.getYear?.()),
      month: safe(() => lunar.getMonth?.()),
      day: safe(() => lunar.getDay?.()),
      year_gan_zhi: safe(() => lunar.getYearInGanZhi?.()),
      month_gan_zhi: safe(() => lunar.getMonthInGanZhi?.()),
      day_gan_zhi: safe(() => lunar.getDayInGanZhi?.()),
      time_gan_zhi: safe(() => lunar.getTimeInGanZhi?.()),
      bazi: safe(() => lunar.getBaZi?.()) ?? [],
      bazi_wu_xing: safe(() => lunar.getBaZiWuXing?.()) ?? [],
      bazi_na_yin: safe(() => lunar.getBaZiNaYin?.()) ?? [],
      bazi_shi_shen_gan: safe(() => lunar.getBaZiShiShenGan?.()) ?? [],
      bazi_shi_shen_zhi: safe(() => lunar.getBaZiShiShenZhi?.()) ?? [],
    },

    jie_qi_24: {
      list: jieQiList,
      table: jieQiEntries,
      current: currentJieQi ? serializeJieQi(currentJieQi) : null,
      next: nextJieQi ? serializeJieQi(nextJieQi) : null,
      prev: prevJieQi ? serializeJieQi(prevJieQi) : null,
    },

    peng_zu: {
      gan: safe(() => lunar.getPengZuGan?.()),
      zhi: safe(() => lunar.getPengZuZhi?.()),
    },

    day_officers: {
      yi: (safe(() => lunar.getDayYi?.(sect)) ?? []) as string[],
      ji: (safe(() => lunar.getDayJi?.(sect)) ?? []) as string[],
      ji_shen: (safe(() => lunar.getDayJiShen?.()) ?? []) as string[],
      xiong_sha: (safe(() => lunar.getDayXiongSha?.()) ?? []) as string[],
      time_yi: (safe(() => lunar.getTimeYi?.()) ?? []) as string[],
      time_ji: (safe(() => lunar.getTimeJi?.()) ?? []) as string[],
    },

    shen_sha: {
      chong: safe(() => lunar.getChong?.()),
      chong_gan: safe(() => lunar.getChongGan?.()),
      chong_sheng_xiao: safe(() => lunar.getChongShengXiao?.()),
      chong_desc: safe(() => lunar.getChongDesc?.()),
      sha: safe(() => lunar.getSha?.()),
      day_chong: safe(() => lunar.getDayChong?.()),
      day_sha: safe(() => lunar.getDaySha?.()),
      time_chong: safe(() => lunar.getTimeChong?.()),
      time_sha: safe(() => lunar.getTimeSha?.()),
      day_tian_shen: safe(() => lunar.getDayTianShen?.()),
      time_tian_shen: safe(() => lunar.getTimeTianShen?.()),
      day_tian_shen_type: safe(() => lunar.getDayTianShenType?.()),
      time_tian_shen_type: safe(() => lunar.getTimeTianShenType?.()),
      day_tian_shen_luck: safe(() => lunar.getDayTianShenLuck?.()),
      time_tian_shen_luck: safe(() => lunar.getTimeTianShenLuck?.()),
      zhi_xing: safe(() => lunar.getZhiXing?.()),
    },

    day_officer_positions: {
      xi: safe(() => lunar.getPositionXi?.()),
      xi_desc: safe(() => lunar.getPositionXiDesc?.()),
      yang_gui: safe(() => lunar.getPositionYangGui?.()),
      yang_gui_desc: safe(() => lunar.getPositionYangGuiDesc?.()),
      yin_gui: safe(() => lunar.getPositionYinGui?.()),
      yin_gui_desc: safe(() => lunar.getPositionYinGuiDesc?.()),
      fu: safe(() => lunar.getDayPositionFu?.(sect)),
      fu_desc: safe(() => lunar.getDayPositionFuDesc?.(sect)),
      cai: safe(() => lunar.getPositionCai?.()),
      cai_desc: safe(() => lunar.getPositionCaiDesc?.()),
      day_position_tai_sui: safe(() => lunar.getDayPositionTaiSui?.(sect)),
    },

    xiu_su: {
      xiu: safe(() => lunar.getXiu?.()),
      xiu_luck: safe(() => lunar.getXiuLuck?.()),
      xiu_song: safe(() => lunar.getXiuSong?.()),
      zheng: safe(() => lunar.getZheng?.()),
      animal: safe(() => lunar.getAnimal?.()),
      gong: safe(() => lunar.getGong?.()),
      shou: safe(() => lunar.getShou?.()),
    },

    eight_char_full: {
      sect,
      year: serializePillar(eightChar, "Year"),
      month: serializePillar(eightChar, "Month"),
      day: serializePillar(eightChar, "Day"),
      time: serializePillar(eightChar, "Time"),
      tai_yuan: safe(() => eightChar.getTaiYuan?.()),
      tai_yuan_na_yin: safe(() => eightChar.getTaiYuanNaYin?.()),
      tai_xi: safe(() => eightChar.getTaiXi?.()),
      tai_xi_na_yin: safe(() => eightChar.getTaiXiNaYin?.()),
      ming_gong: safe(() => eightChar.getMingGong?.()),
      ming_gong_na_yin: safe(() => eightChar.getMingGongNaYin?.()),
      shen_gong: safe(() => eightChar.getShenGong?.()),
      shen_gong_na_yin: safe(() => eightChar.getShenGongNaYin?.()),
    },

    time_detail: timeObj
      ? {
          gan_zhi: safe(() => timeObj.getGanZhi?.()),
          na_yin: safe(() => timeObj.getNaYin?.()),
          tian_shen: safe(() => timeObj.getTianShen?.()),
          tian_shen_type: safe(() => timeObj.getTianShenType?.()),
          tian_shen_luck: safe(() => timeObj.getTianShenLuck?.()),
          chong: safe(() => timeObj.getChong?.()),
          sha: safe(() => timeObj.getSha?.()),
        }
      : null,

    solar_ymd: solar?.toYmd?.() ?? null,

    taiyi: safe(() => {
      if (!solar) return null;
      const d = new Date(
        solar.getYear(),
        solar.getMonth() - 1,
        solar.getDay(),
        solar.getHour(),
        solar.getMinute(),
        solar.getSecond()
      );
      return computeTaiYi(d);
    }),

    daliuren: safe(() => {
      if (!solar) return null;
      const d = new Date(
        solar.getYear(),
        solar.getMonth() - 1,
        solar.getDay(),
        solar.getHour(),
        solar.getMinute(),
        solar.getSecond()
      );
      return computeDaLiuRen(d);
    }),
  };
}
