/**
 * One-line card header: title, then the figures that would otherwise be a
 * subtitle, then an optional control. Charts carry their own context inline
 * rather than repeating it in prose above them.
 */

import { cn } from "@/lib/utils"

export function CardBar({
  title,
  control,
  children,
}: {
  title: string
  control?: React.ReactNode
  children?: React.ReactNode
}) {
  return (
    <div className="flex flex-wrap items-center gap-x-3 gap-y-1 border-b border-border p-3">
      <h2 className="text-sm font-semibold text-fg">{title}</h2>
      <div className="flex flex-1 flex-wrap items-center gap-x-3 gap-y-1">{children}</div>
      {control}
    </div>
  )
}

/** A figure with its unit, sized to sit inside a header line. */
export function CardStat({
  value,
  label,
  className,
}: {
  value: string
  label: string
  className?: string
}) {
  return (
    <span className={cn("flex items-baseline gap-1", className)}>
      <span className="text-sm font-semibold tabular-nums text-fg">{value}</span>
      <span className="text-xs text-fg-muted">{label}</span>
    </span>
  )
}

export function CardDelta({
  label,
  direction,
  tone,
}: {
  label: string
  direction: "up" | "down"
  tone: "success" | "danger"
}) {
  return (
    <span
      className={cn(
        "inline-flex items-center gap-0.5 rounded-sm px-1.5 text-xs font-medium tabular-nums ring-1",
        tone === "success"
          ? "bg-success-soft text-success-fg ring-success/20"
          : "bg-danger-soft text-danger-fg ring-danger/20",
      )}
    >
      {direction === "up" ? "↑" : "↓"} {label}
    </span>
  )
}
