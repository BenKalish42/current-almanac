# Task 12.7: Nine Palaces Matrix Component (Layered)

## Context
Building a unified `NinePalacesMatrix.vue` component to serve as a 3x3 grid displaying the Flying Stars. This component acts as the foundational view for supporting multiple instances (e.g., Natal, Current Flow). The UI supports viewing information from multiple traditions (Lo Shu, Tibetan Mewa, Japanese Nine Star Ki) simultaneously via layered toggles. Clicking on a specific palace triggers a popover/modal revealing an offline synthesis of that number across all activated traditions.

## Implementation Details

### Data Dictionary & Math
Path: `src/data/ninePalacesDictionary.ts`

**Mathematical Flight Path:**
Calculates the positions of the 8 surrounding palaces given a `centerStar` according to the standard Luo Shu flight path:
- Center -> NW -> W -> NE -> S -> N -> SW -> E -> SE
- Each subsequent direction increments the star number by 1, wrapping around from 9 back to 1.

**Traditions Supported (Multi-Layer):**
Each number 1-9 is mapped in the dictionary to:
- `loshuLabel`: Daoist Elements (Water, Earth, Wood, Metal, Fire)
- `mewaLabel`: Tibetan Colors (White, Black, Indigo, Green, Yellow, Red)
- `nineStarLabel`: Japanese Nine Star Ki names
- `mewaBgClass`: Optional Tailwind coloring (applied if Mewa is the *only* active tradition to avoid clashing when layering).
- `synthesisText`: A structured object containing paragraphs interpreting the number through the lens of all three traditions.

### Component View
Path: `src/components/astrology/NinePalacesMatrix.vue`

**Daoist Directional Grid Map:**
Follows standard traditional mapping where:
- South is Top
- North is Bottom
- East is Left
- West is Right

Represented cleanly in a responsive Tailwind 3x3 CSS Grid, mapping to the array sequence:
- Row 1: SE, S, SW
- Row 2: E, Center, W
- Row 3: NE, N, NW

**Layer Toggles (Checkboxes):**
Interactive toggle buttons provided directly above the grid:
- `[ ☯️ Chinese Lo Shu ]`
- `[ 🏔️ Tibetan Mewa ]`
- `[ 🌸 Japanese 9-Star ]`
Bound to `activeTraditions: string[]`. By default, `['loshu']` is active.
Inside each grid cell, the selected traditions are rendered beneath the large star number in clean, subtle typography.

**Click Synthesis Modal:**
Clicking on a specific palace cell opens an overlaid modal displaying the number. Inside the modal, the user can read the `synthesisText` segmented by tradition, offering a unified, offline understanding of the selected flying star.

## Integration
The component is exported securely, taking `centerStar` as a required numerical prop. It manages its own interactive state for `activeTraditions` and the modal, allowing Jun to instantiate it easily in BaZi, Current Flow, or other dashboard views without wiring up complex external state.