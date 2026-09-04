/** Border colour for list-table rows. */
export const ROW_BORDER = "border-fg/8"

/**
 * Header separation for a table inside a panel. The border sits on the th
 * cells because Tailwind collapses table borders, which drops a border set on
 * a sticky thead.
 */
export const TABLE_HEAD = "border-b-0 bg-surface [&_th]:border-b [&_th]:border-fg/15"

/** Header for a full-page list table, pinned while the rows scroll under it. */
export const STICKY_TABLE_HEAD = `sticky top-0 z-10 ${TABLE_HEAD}`
