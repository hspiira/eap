# Evexía - Agent Rules

## Design System Rules (CRITICAL - Always Follow)

### Color Palette
- **ONLY** use these colors:
  - SAFE: `#5A626A` (dark grayish-blue) - for text, borders, dark backgrounds
  - NATURAL: `#8BA88B` (sage green) - for primary actions, success states
  - NURTURING: `#D0B5B3` (dusty rose) - for secondary actions, highlights
  - CALM: `#E6E0D7` (warm beige) - for backgrounds, light surfaces

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

## Reference Files
- Design system: `.cursor/rules/DESIGN_SYSTEM.md`
- Full documentation: `docs/DESIGN_SYSTEM.md`
