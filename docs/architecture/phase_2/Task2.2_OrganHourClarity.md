# Task 2.2: Organ Hour Clarity (Wu Shen + Disambiguation)

**Phase:** 2 — Astrology Pillar (Temporal Diagnostics Polish)  
**Task:** 2.2 (Combined)

---

## 1. Files Modified

| Action | Path |
|--------|------|
| Modified | `src/data/organClock.ts` — added spiritName, organHanzi, organPinyin to all 12 entries |
| Modified | `src/components/astrology/OrganHourCard.vue` — micro-labels, linguistic display, dynamic Neidan header |
| Created | `docs/architecture/phase_2/Task2.2_OrganHourClarity.md` |

---

## 2. Schema Updates (organClock.ts)

**New fields on OrganHourEntry:**
- `spiritName` — Wu Shen label (e.g., "Hun (Ethereal Soul)", "Shen (Mind/Spirit)")
- `organHanzi` — Chinese characters (e.g., "胆", "心")
- `organPinyin` — Pinyin with tone marks (e.g., "Dǎn", "Xīn")

**Mappings:** Gallbladder→Dan/Hun, Liver→Hun, Lung→Po, Large Intestine→Letting go (Serves the Po), Stomach→Yi, Spleen→Yi, Heart→Shen, Small Intestine→Shen, Bladder→Zhi, Kidney→Zhi, Pericardium→Shen, San Jiao→Shen.

---

## 3. UI Updates (OrganHourCard.vue)

- **EARTHLY BRANCH (TIME):** Muted tracking label above branch (子 Zi) and time block
- **ACTIVE MERIDIAN:** Muted tracking label above organ; disambiguates time system from anatomy
- **Linguistic:** Organ name + organHanzi organPinyin (e.g., "Gallbladder 胆 Dǎn") with lighter font for Hanzi/Pinyin
- **Neidan header:** Dynamic — "NEIDAN / " + `spiritName.toUpperCase()` (e.g., "NEIDAN / SHEN (MIND/SPIRIT)")

---

## 4. One-Sentence Summary for AI CTO

OrganClock now maps the Five Spirits (Wu Shen) explicitly to each organ; OrganHourCard disambiguates Time System (Earthly Branch) from Anatomy System (Active Meridian) with micro-labels and displays organHanzi/organPinyin; the Neidan column header includes the current spirit name.
