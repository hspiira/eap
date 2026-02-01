# Theme system

Plug-and-play color management: **palette** → **tokens** → **themes**.

## Layout

- **`palette.css`** – Raw hex values (`--palette-*`). Single source of truth for brand and neutrals.
- **`tokens.css`** – Semantic tokens (`--token-*`) that reference the palette (e.g. `--token-page`, `--token-surface`, `--token-primary`).
- **`themes/`** – Theme overrides. Each file can override `--palette-*` or `--token-*` for a given theme.

Tailwind `@theme` in `styles.css` maps both palette and tokens to utilities (`bg-safe`, `text-natural`, `bg-page`, `bg-surface`, etc.).

## Switching themes

1. **Default (Evexía)**  
   `theme/index.css` imports `themes/evexia.css`. No change needed.

2. **Dark**  
   - Add `@import "./themes/evexia-dark.css";` to `theme/index.css` (or conditionally load it).
   - Use `data-theme="dark"` on `<html>` when dark mode is active.  
   `evexia-dark.css` overrides `--palette-*` (and optionally `--token-*`) for `[data-theme="dark"]`.

3. **New theme (e.g. Acme)**  
   - Add `themes/acme.css` that sets `--palette-*` (and optionally `--token-*`) for `:root` or `[data-theme="acme"]`.
   - Import it from `theme/index.css` or load it when Acme theme is selected.
   - Optionally switch via `data-theme="acme"` on `<html>`.

## Adding a theme

1. Create `themes/<name>.css`.
2. Override `:root` or `[data-theme="<name>"]` with `--palette-*` and/or `--token-*`.
3. Import the file in `theme/index.css` (or load it when the theme is active).
4. If using a selector, set `data-theme="<name>"` on `<html>` when the theme is active.

## Tokens

| Token | Use |
|-------|-----|
| `page` | Page background |
| `surface` | Cards, inputs, modals |
| `surface-hover` | Hover state for surfaces |
| `surface-muted` | Muted surfaces (e.g. empty state) |
| `border` | Default border |
| `border-focus` | Focus ring |
| `text` | Primary text |
| `text-muted` | Secondary text |
| `primary` / `primary-hover` | Primary actions |
| `secondary` / `secondary-hover` | Secondary actions |
| `neutral` / `neutral-light` / `neutral-dark` | Neutral UI (badges, etc.) |
| `danger` / `danger-light` / `danger-dark` | Errors, destructive actions, validation |

Use `bg-page`, `bg-surface`, `text-text`, `border-border`, etc. for token-based styling. Existing `bg-safe`, `text-natural`, `bg-danger`, etc. still work via the palette.
