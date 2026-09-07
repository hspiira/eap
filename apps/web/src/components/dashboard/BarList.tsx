/**
 * Ranked horizontal bars: label, value, and a single-hue fill on a lighter
 * track of the same ramp. Rows that carry a destination render as links.
 */

import { Link } from "@tanstack/react-router"

import { cn } from "@/lib/utils"

export interface BarListItem {
  key: string
  label: string
  value: number
  to?: string
  params?: Record<string, string>
  hint?: string
}

interface BarListProps {
  items: ReadonlyArray<BarListItem>
  tone?: "brand" | "warning"
}

const FILL: Record<NonNullable<BarListProps["tone"]>, string> = {
  brand: "bg-primary",
  warning: "bg-warning",
}

const TRACK: Record<NonNullable<BarListProps["tone"]>, string> = {
  brand: "bg-primary/10",
  warning: "bg-warning/10",
}

export function BarList({ items, tone = "brand" }: BarListProps) {
  const max = Math.max(...items.map((item) => item.value), 1)
  return (
    <ul className="grid gap-1">
      {items.map((item) => (
        <li key={item.key}>
          <BarRow item={item} max={max} tone={tone} />
        </li>
      ))}
    </ul>
  )
}

function BarRow({
  item,
  max,
  tone,
}: {
  item: BarListItem
  max: number
  tone: NonNullable<BarListProps["tone"]>
}) {
  const body = (
    <>
      <div className="flex items-baseline justify-between gap-3">
        <span className="min-w-0 truncate text-sm text-fg">{item.label}</span>
        <span className="text-sm font-medium tabular-nums text-fg">
          {item.value.toLocaleString()}
        </span>
      </div>
      <div className={cn("h-1.5 overflow-hidden rounded-full", TRACK[tone])}>
        <div
          className={cn("h-full rounded-full", FILL[tone])}
          style={{ width: `${Math.max((item.value / max) * 100, 1.5)}%` }}
        />
      </div>
      {item.hint ? <p className="truncate text-xs text-fg-muted">{item.hint}</p> : null}
    </>
  )
  const rowClass = "grid gap-1 rounded-md px-2 py-1.5 -mx-2"
  if (!item.to) return <div className={rowClass}>{body}</div>
  return (
    <Link
      to={item.to}
      params={item.params}
      className={cn(
        rowClass,
        "transition-colors hover:bg-surface-hover focus-visible:bg-surface-hover focus-visible:outline-none",
      )}
      aria-label={`${item.label}: ${item.value.toLocaleString()}`}
    >
      {body}
    </Link>
  )
}
