# Task 11.12 - Exploded Hexagram Bracket Alignment

## Scope

Align the left-flank SVG `[` brackets with the BaGua lines in the Exploded Hexagram UI. Bracket serifs should frame the top and bottom edges of each trigram group.

## Mathematical Alignment

### Line Coordinates

- Each line: `y = 106 - indexFromBottom * 16`, height = 8
- **Upper trigram** (lines 4–6): top edge = min(line.y), bottom edge = max(line.y) + 8
- **Lower trigram** (lines 1–3): top edge = min(line.y), bottom edge = max(line.y) + 8

### Transform When Exploded

- Upper group: `translate-y-[-16px]`
- Lower group: `translate-y-[16px]`

### Bracket Path Formula

Brackets live in an opacity-only group (fade in with labels). They use the **transformed** coordinates so they align with lines in their exploded positions:

- **Upper bracket**: `top' = top - 16`, `bottom' = bottom - 16`
- **Lower bracket**: `top' = top + 16`, `bottom' = bottom + 16`

Path d: `M BRACKET_X top v height M BRACKET_X top h SERIF M BRACKET_X bottom h SERIF`  
Constants: `BRACKET_X = 38`, `SERIF_WIDTH = 4`

## Implementation

- `upperBracketBounds` / `lowerBracketBounds`: computed from `upperTrigramLines` / `lowerTrigramLines` (min y → top, max y + 8 → bottom)
- `upperBracketPath` / `lowerBracketPath`: path d strings using transformed bounds
- Template: `<path :d="upperBracketPath" ... />` and `<path :d="lowerBracketPath" ... />`

## Animation Sync

Brackets and labels share `transition-opacity duration-500` with `isExploded`. The line groups use `transition-transform duration-500 ease-out`. All animations share the same duration, so brackets fade in smoothly as lines move into place.

## Files Modified

- `src/components/HexagramModal.vue`
