# Task 11.5 - Yi Jing Lens Icons

## Scope

Added iconography and animated lens toggles for the six Yi Jing interpretation systems in the modal.

## New Component

- `src/components/astrology/PhilosophyIcon.vue`

`PhilosophyIcon` accepts:

- `system: 'daoism' | 'confucianism' | 'buddhism' | 'psychology' | 'humandesign' | 'genekeys'`

## SVG Set

Each icon is pure inline SVG (`viewBox="0 0 24 24"`):

- **Daoism**: Tabler `yin-yang` icon (MIT).
- **Confucianism**: KanjiVG stroke-path for `水` (CC BY-SA).
- **Buddhism**: Font Awesome Free `dharmachakra` (CC BY 4.0).
- **Psychology**: Wikimedia Greek Psi symbol SVG.
- **Human Design**: Lucide `network` icon (ISC).
- **Gene Keys**: Lucide `dna` icon (ISC).

All six icons are centered within the `24x24` coordinate grid for consistent visual weight in the toggle bar.

## Source References

- Daoism: <https://raw.githubusercontent.com/tabler/tabler-icons/master/icons/outline/yin-yang.svg>
- Confucianism (`水`): <https://raw.githubusercontent.com/KanjiVG/kanjivg/master/kanji/06c34.svg>
- Buddhism: <https://raw.githubusercontent.com/FortAwesome/Font-Awesome/6.x/svgs/solid/dharmachakra.svg>
- Psychology: <https://upload.wikimedia.org/wikipedia/commons/6/62/Greek_letter_psi.svg>
- Human Design: <https://raw.githubusercontent.com/lucide-icons/lucide/main/icons/network.svg>
- Gene Keys: <https://raw.githubusercontent.com/lucide-icons/lucide/main/icons/dna.svg>

## Modal Integration

- Updated `src/components/HexagramModal.vue` (active Yi Jing modal in this repository):
  - Replaced stacked six-section rendering with a six-option lens toggle row.
  - Each toggle now includes `PhilosophyIcon` + lens label.
  - Added active-lens state rendering so only one perspective body is shown at a time.

## Interaction / Motion

- Toggle buttons use transition classes for visual feedback:
  - `transition-all duration-300`
  - active state includes subtle scale boost (`scale-110`) and glow-style highlight.
- Active icon glyph receives an additional subtle SVG glow (`drop-shadow`) to improve tab-state recognition.
- Inactive options keep a subdued style and receive mild hover scaling for responsiveness.
