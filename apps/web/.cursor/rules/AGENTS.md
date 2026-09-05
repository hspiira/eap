# Evexía - Agent Rules

## Design System Rules (CRITICAL - Always Follow)

### Color Palette
- **Default theme:** White (`#ffffff`) for page and surface backgrounds; black for primary text.
- **ONLY** use these colors:
  - SAFE: `#5A626A` (dark gray) - for borders, secondary text
  - NATURAL: `#103a10` (primary green), lighter: `#3fe844` - for primary actions, **selection highlight** (`bg-selection`), success states
  - NURTURING: `#D0B5B3` (dusty rose) - for secondary actions, highlights
  - Use **white** for backgrounds; avoid cream/beige unless explicitly requested

### NO Rounded Corners
- **CRITICAL**: All buttons, cards, inputs, and components MUST have sharp, square corners
- Always use `rounded-none` in Tailwind
- Only add rounded corners if the user explicitly requests it

### Flat Design Only
- **NO gradients** - Use solid colors only
- **NO shadows** - Unless absolutely necessary for accessibility
- **NO blueish AI colors** - Remove any cyan, blue, or teal colors
- Maintain flat, minimal aesthetic

### Consistency
- Use the same color palette throughout
- Maintain consistent spacing
- Follow the same design patterns

## When Creating Components

1. Use `rounded-none` on all elements
2. Use only the approved color palette
3. Remove any gradients or shadows
4. Remove any blue/cyan/teal colors
5. Maintain flat, minimal design
6. Do not add comments unnecessarily

## Reference Files
- Design system: `.cursor/rules/DESIGN_SYSTEM.md`
- Full documentation: `docs/DESIGN_SYSTEM.md`
