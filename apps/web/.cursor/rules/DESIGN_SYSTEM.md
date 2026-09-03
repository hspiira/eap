# Design System Rules

## Theme system

Colors live in **`src/theme/`**: palette → tokens → themes. See `src/theme/README.md` for switching themes and adding new ones. Tailwind utilities come from there (`bg-safe`, `text-natural`, `bg-page`, `bg-surface`, etc.).

**Default project theme:** White and black. Page and surface backgrounds are white; primary text is black. Use green (`natural`) for selection and primary actions.

## Color Palette

Use ONLY these colors from the approved palette:

- **SAFE** (`#4f5860`) - Dark gray
  - Use for: Borders, secondary text, dark backgrounds
  - Tailwind class: `safe` or `text-safe`, `bg-safe`, `border-safe`

- **NATURAL** (`#103a10`) - Green (primary)
  - Lighter: `#3fe844` (`natural-light`)
  - Use for: Primary actions, success states, selection highlight, accents
  - Tailwind class: `natural` or `text-natural`, `bg-natural`, `border-natural`. Selection: `bg-selection` (green tint)

- **NURTURING** (`#a06858`) - Warm clay/amber
  - Use for: Secondary actions, highlights, pending states
  - Tailwind class: `nurturing` or `text-nurturing`, `bg-nurturing`, `border-nurturing`

- **DANGER** (`#b84848`) - Red
  - Use for: Errors, failed states, validation, destructive actions
  - Tailwind class: `danger` or `text-danger`, `bg-danger`, `border-danger`

- **Page/Surface:** White (`#ffffff`) for page and card backgrounds. Use `bg-page`, `bg-surface`, or `bg-white`. Text: black (`#000000`) via `--token-text` / `text-black`.

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
- Use white for backgrounds (`bg-white` / `bg-surface`)
- Use `safe` for borders
- Flat design, no shadows

### Inputs/Forms
- Sharp corners (`rounded-none`)
- Use `safe` for borders
- Use white for input backgrounds
- Flat design

### Navigation
- Use `safe` or black for text
- Use white for backgrounds
- Sharp corners on all elements

### Selection
- Use green tint for selected rows/items: `bg-selection` (token) or `bg-natural/15`

## Implementation

All components must follow these rules. When creating or updating components:
1. Use the defined color palette
2. Set `rounded-none` on all elements
3. Remove any gradients or shadows
4. Maintain flat, minimal design
5. Remove any blue/cyan/teal colors
6. **Do not add comments unnecessarily** – avoid decorative or redundant comments in code
