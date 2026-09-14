/**
 * Counts above a table that are also its filters.
 *
 * People reach a big list looking for the exceptional rows, not to scan it.
 * A count that says "1 Suspended" and filters to that row on click turns the
 * summary into navigation. A cell without a filter value renders as plain
 * text, so a count with nothing to click never pretends otherwise.
 */

import { Button } from "@/components/ui/button"

interface SummaryCell {
  label: string
  value: number
  emphasis?: boolean
  /** Filter value this cell applies on click; undefined means not clickable. */
  filter?: string
}

export function SummaryStrip({
  cells,
  activeFilter,
  onFilter,
}: {
  cells: SummaryCell[]
  /** The currently applied filter value, so the active cell reads as pressed. */
  activeFilter?: string
  /** Called with the cell's filter value, or undefined for an emphasis cell (clear). */
  onFilter: (value: string | undefined) => void
}) {
  const shown = cells.filter((cell) => cell.emphasis || cell.value > 0)
  return (
    <div className="flex shrink-0 flex-wrap items-center gap-x-2 gap-y-1 border-b border-fg/10 bg-surface px-1.5 py-1">
      {shown.map((cell) => {
        const content = (
          <>
            <span
              className={`text-sm tabular-nums ${cell.emphasis ? "font-semibold text-fg" : "font-medium text-fg/80"}`}
            >
              {cell.value.toLocaleString()}
            </span>
            <span className="text-xs text-fg-muted">{cell.label}</span>
          </>
        )
        if (!cell.filter && !cell.emphasis) {
          return (
            <span key={cell.label} className="flex items-baseline gap-1.5 px-1.5 py-1">
              {content}
            </span>
          )
        }
        const active = cell.filter !== undefined && cell.filter === activeFilter
        return (
          <Button
            key={cell.label}
            type="button"
            variant="ghost"
            size="sm"
            aria-label={`${cell.value.toLocaleString()} ${cell.label}`}
            aria-pressed={active}
            onClick={() => onFilter(cell.filter)}
            className={`h-auto items-baseline gap-1.5 rounded-sm px-1.5 py-1 font-normal ${
              active ? "bg-fg/6" : ""
            }`}
          >
            {content}
          </Button>
        )
      })}
    </div>
  )
}
