# Task 11.0 - Formula Graph Schema (Phase 1.5 Alchemy Pillar)

## Objective

Expand from a static herb list into a relational formula graph that links:

- **Classical formulas** (canonical historical blueprint nodes)
- **Market variants** (real products sold by modern brands)
- **Ingredient edges** (role and dosage relationships to herbs)

This supports deviation tracking, safety checks, and brand-to-blueprint traceability.

## Graph Model

### Node: `ClassicalFormula`

Represents the original formula design from source texts.

Key fields:

- `id`
- `name_hanzi`
- `name_pinyin`
- `linguistics` (`cantonese`, `taiwanese`)
- `source_text` (for example, `Shanghan Lun`)
- `description`

### Node: `MarketVariant`

Represents a concrete product from a specific brand.

Key fields:

- `id`
- `brand_name`
- `formula_id` (foreign key to `ClassicalFormula.id`)
- `actual_ingredients` (array with `herb_id`, `exact_dosage_grams`)
- `has_shadow_nodes` (legal/safety red flag)

## Edge: `FormulaIngredient`

Represents canonical ingredient relationships for each classical formula.

Key fields:

- `formula_id`
- `herb_id`
- `role` (`Jun`, `Chen`, `Zuo`, `Shi`)
- `classical_dosage_ratio`

Interpretation:

- This edge defines the **classical blueprint composition**.
- `MarketVariant.actual_ingredients` then records **real-world product composition**.
- Comparison between the two surfaces ingredient substitutions and dosage drifts.

## Shadow Node Safety Protocol

`has_shadow_nodes` is set to `true` when a market product references one or more `herb_id`s that are intentionally abstracted (for legal, regulatory, or safety reasons).

### Why shadow nodes exist

- Some ingredients may be legally sensitive, restricted, region-specific, or need legal review before explicit publication.
- A shadow node allows graph continuity while preventing unsafe or non-compliant direct disclosure.

### Operational rules

- Shadow ingredient IDs should be prefixed, e.g. `shadow_herb_*`.
- Any market variant containing a shadow-prefixed ingredient must set `has_shadow_nodes: true`.
- Downstream UI or reporting layers should:
  - show a caution badge,
  - suppress explicit ingredient details where required,
  - route the record to compliance review workflows.

## Seed Payload Coverage

Task 11 ships with two classical formulas:

- `Liu Wei Di Huang Wan`
- `Bao He Wan`

And three market variants:

- `Plum Flower` (Liu Wei Di Huang Wan)
- `Solstice` (Liu Wei Di Huang Wan)
- `Solstice` (Bao He Wan)

This demonstrates many-to-one mapping from market products to a single classical blueprint and includes seeded shadow-node examples for safety workflow testing.
