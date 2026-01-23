# Design System Rules

## Color Palette

Use ONLY these colors from the approved palette:

- **SAFE** (`#5A626A`) - Dark grayish-blue
  - Use for: Primary text, borders, dark backgrounds
  - Tailwind class: `safe` or `text-safe`, `bg-safe`, `border-safe`

- **NATURAL** (`#8BA88B`) - Sage green
  - Use for: Primary actions, success states, accents
  - Tailwind class: `natural` or `text-natural`, `bg-natural`, `border-natural`

- **NURTURING** (`#D0B5B3`) - Dusty rose/pink
  - Use for: Secondary actions, highlights, warm accents
  - Tailwind class: `nurturing` or `text-nurturing`, `bg-nurturing`, `border-nurturing`

- **CALM** (`#E6E0D7`) - Warm beige/cream
  - Use for: Backgrounds, light surfaces, subtle highlights
  - Tailwind class: `calm` or `text-calm`, `bg-calm`, `border-calm`

## Design Principles

### NO Rounded Corners
- **CRITICAL**: All buttons, cards, inputs, and components must have sharp, square corners
- Use `rounded-none` in Tailwind (or no border-radius)
- Only add rounded corners if explicitly requested by the user

### Flat Colors Only
- **NO gradients** - Use solid colors only
- **NO shadows** unless absolutely necessary for accessibility
- **NO blueish AI colors** - Remove any cyan, blue, or teal colors
- Maintain flat, minimal aesthetic

### Consistency
- Use the same color palette throughout the entire application
- Maintain consistent spacing and typography
- Follow the same design patterns across all components

## Component Guidelines

### Buttons
- Sharp corners (`rounded-none`)
- Flat colors (no gradients)
- Use `natural` for primary, `nurturing` for secondary
- No shadows unless needed for accessibility

### Cards/Containers
- Sharp corners (`rounded-none`)
- Use `calm` for backgrounds
- Use `safe` for borders
- Flat design, no shadows

### Inputs/Forms
- Sharp corners (`rounded-none`)
- Use `safe` for borders
- Use `calm` for backgrounds
- Flat design

### Navigation
- Use `safe` for text
- Use `calm` for backgrounds
- Sharp corners on all elements

## Implementation

All components must follow these rules. When creating or updating components:
1. Use the defined color palette
2. Set `rounded-none` on all elements
3. Remove any gradients or shadows
4. Maintain flat, minimal design
5. Remove any blue/cyan/teal colors
