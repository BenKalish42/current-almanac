# Task 11.8 - Yi Jing UX Polish

## Scope

Unified the philosophy lens state, fixed SVG clipping, removed redundant Line Analysis tabs, and redesigned the Line Analysis block for a cleaner UX.

## Changes

### 1. SVG ViewBox Fix (Clipped Text)

- **Before**: `viewBox="0 0 240 140"` — left-flank BaGua text (trigram name + element) was clipped when text extended past x=0.
- **After**: `viewBox="-50 0 290 140"` — expanded visible area by 50 units to the left and 50 to the right so trigram labels render fully.

### 2. Unified Philosophy State

- **Before**: Two separate states:
  - `activeLens` (LensKey) for the main hexagram description
  - `activeLinePhilosophy` (LinePhilosophy) for the Line Analysis section
- **After**: Single `activePhilosophy` (PhilosophyKey) drives both:
  - Main hexagram description (perspective text)
  - Line Analysis placeholder content
- **Mapping**: `PHILOSOPHY_TO_SUMMARY_KEY` maps philosophy keys (daoism, confucianism, etc.) to summary keys (daoist, confucian, etc.) for `HexagramSummary`.

### 3. Removed Double Picker

- Deleted the redundant row of 6 `PhilosophyIcon` tabs that appeared inside the Line Analysis section.
- The modal now has one global philosophy picker (lens toggle) that controls both the hexagram body and the line analysis lens.

### 4. Redesigned Line Analysis Block

- **Conditional**: Renders only when `activeLine` is set (`v-if="activeLine"`).
- **Header**: `Line {{ activeLine }} • {{ activePhilosophyDisplay }} Analysis` — philosophy name capitalized via `PHILOSOPHY_DISPLAY`.
- **Styling**:
  - Left border colored by Wu Xing (based on which trigram the line belongs to: upper 4–6 vs lower 1–3).
  - Slightly lighter/darker background with subtle glow.
- **Placeholder**: "Line X Philosophy analysis is coming soon."

### 5. Wu Xing Border for Line Block

- `lineBlockBorderClass` computed: uses `trigramBreakdown.upper` for lines 4–6, `trigramBreakdown.lower` for lines 1–3.
- Maps trigram to Tailwind border color: Li→red, Sun/Zhen→emerald, Kan→blue, Kun/Gen→amber, Qian/Dui→slate.

## Files Modified

- `src/components/HexagramModal.vue`
