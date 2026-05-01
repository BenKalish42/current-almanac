# Math Fixture Sources

Fixtures used by `tests/math/*.spec.ts` for the Cosmic Engine. Every value
was computed against the existing `lunar-typescript` library on master
(commit `8cc472e`) and locked in. They serve two purposes:

1. **Regression**: any change to `core/ganzhi.ts`, `core/hexagramsXKDG.ts`,
   `lib/personal/baziNineStar.ts`, or `utils/solarTime.ts` that would
   alter pillar / hexagram / Nine-Star output is caught.
2. **Sign-convention**: cusps around 立春 (Lichun, ~Feb 4) are explicitly
   tested so that any future edit to year-pillar boundary detection is
   verified against the published Chinese calendar.

## BaZi / Nine Star fixtures

| # | Label | Input (local) | Year pillar | Month pillar | Day pillar | Hour pillar | Year ☆ | Month ☆ |
|--:|-------|---------------|------------|--------------|-----------|-------------|--------|---------|
| 1 | Mao Zedong (Shaoshan) | 1893-12-26 07:30 | 癸巳 | 甲子 | 丁酉 | 甲辰 | 八 | 一 |
| 2 | Albert Einstein (Ulm) | 1879-03-14 11:30 | 己卯 | 丁卯 | 丙申 | 甲午 | 四 | 七 |
| 3 | Anchor 2000-01-01 00:00 | 2000-01-01 00:00 | 己卯 | 丙子 | 戊午 | 壬子 | 一 | 七 |
| 4 | Anchor 2024-06-15 12:00 | 2024-06-15 12:00 | 甲辰 | 庚午 | 庚戌 | 壬午 | 三 | 一 |
| 5 | Anchor 1990-01-01 12:00 | 1990-01-01 12:00 | 己巳 | 丙子 | 丙寅 | 甲午 | 二 | 一 |
| 6 | Cusp Lichun-1 | 2000-02-04 02:00 | 己卯 | 丁丑 | 壬辰 | 辛丑 | 九 | 五 |
| 7 | Cusp Lichun+1d | 2000-02-05 02:00 | 庚辰 | 戊寅 | 癸巳 | 癸丑 | 九 | 五 |

The cusp pair (#6 / #7) verifies the year-pillar transition at 立春
(Lichun, ~Feb 4). The year branch flips from 卯 (Rabbit) to 辰 (Dragon)
the moment Lichun ticks; #6 is one day before, #7 is one day after.

## True Solar Time

`utils/solarTime.ts` is verified against NOAA's published Equation of Time
table for J2000 epoch:

| Date (UTC) | Day-of-year | Expected EoT (min) | Tolerance |
|------------|-------------|--------------------|-----------|
| 2024-01-15 | 15  | -9.2  | ±0.5 |
| 2024-02-15 | 46  | -14.0 | ±0.5 |
| 2024-04-15 | 106 |  -0.1 | ±0.5 |
| 2024-06-15 | 167 |  -0.4 | ±0.5 |
| 2024-09-15 | 259 |  +4.6 | ±0.5 |
| 2024-11-03 | 308 | +16.5 | ±0.5 |

Source: NOAA Solar Position Calculator (https://gml.noaa.gov/grad/solcalc/),
sampled and rounded to one decimal.

## Provenance

The pillar values for #1, #2 cross-check against published BaZi sources
(en.wikipedia BaZi entries for these figures). #3–#7 are anchor cases
chosen for stability across timezones and calendar boundaries.
