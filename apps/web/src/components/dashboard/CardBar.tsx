/**
 * One-line card header: title, then the figures that would otherwise be a
 * subtitle, then an optional control. Charts carry their own context inline
 * rather than repeating it in prose above them.
 */

import type { ElementType, ReactNode } from "react"

import { CircleAlert } from "lucide-react"

import { Button } from "@/components/ui/button"
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

/** A dashed-box placeholder for a card with nothing to show yet. */
export function CardEmptyState({
  icon: Icon,
  title,
  description,
  action,
  className,
}: {
  icon?: ElementType
  title: string
  description?: string
  action?: ReactNode
  className?: string
}) {
  return (
    <div
      className={cn(
        "flex flex-col items-center justify-center gap-1 border border-dashed border-fg/15 p-6 text-center",
        className,
      )}
    >
      {Icon ? (
        <span className="mb-1 grid size-9 place-items-center rounded-full bg-fg/5 text-fg-subtle">
          <Icon className="size-4" />
        </span>
      ) : null}
      <p className="text-sm font-medium text-fg">{title}</p>
      {description ? <p className="max-w-[28ch] text-xs text-fg-muted">{description}</p> : null}
      {action ? <div className="mt-1">{action}</div> : null}
    </div>
  )
}

/** A dashed-box placeholder for a card whose data failed to load. */
export function CardErrorState({
  title = "Could not load",
  description,
  onRetry,
  className,
}: {
  title?: string
  description?: string
  onRetry?: () => void
  className?: string
}) {
  return (
    <div
      className={cn(
        "flex flex-col items-center justify-center gap-1 border border-dashed border-danger/30 p-6 text-center",
        className,
      )}
    >
      <span className="mb-1 grid size-9 place-items-center rounded-full bg-danger-soft text-danger-fg">
        <CircleAlert className="size-4" />
      </span>
      <p className="text-sm font-medium text-fg">{title}</p>
      {description ? <p className="max-w-[28ch] text-xs text-fg-muted">{description}</p> : null}
      {onRetry ? (
        <Button variant="outline" size="sm" onClick={onRetry} className="mt-2">
          Retry
        </Button>
      ) : null}
    </div>
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

/** The sentence under a chart: computed from the same data, never filler. */
export function CardInsight({ text }: { text: string | null }) {
  if (!text) return null
  return <p className="border-t border-border px-3 py-2 text-xs text-fg-muted">{text}</p>
}
