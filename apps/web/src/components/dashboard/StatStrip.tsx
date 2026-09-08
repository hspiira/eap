/**
 * KPI strip: one card, up to four stat tiles separated by hairlines.
 * A tile shows a headline value with an optional delta against the prior
 * period, a one-line hint, and an optional 12-point sparkline.
 */

import { Card, CardContent } from "@/components/ui/card"
import { Skeleton } from "@/components/ui/skeleton"
import { cn } from "@/lib/utils"

export type StatTone = "info" | "danger" | "success" | "warning"

export interface StatDelta {
  label: string
  direction: "up" | "down"
  tone: "success" | "danger"
}

export interface StatSpec {
  id: string
  label: string
  value: string
  icon: React.ElementType
  tone: StatTone
  hint?: string
  delta?: StatDelta
  spark?: number[]
  loading?: boolean
  error?: boolean
}

const TONE_BADGE: Record<StatTone, string> = {
  info: "bg-info-soft text-info-fg ring-info/20",
  danger: "bg-danger-soft text-danger-fg ring-danger/20",
  success: "bg-success-soft text-success-fg ring-success/20",
  warning: "bg-warning-soft text-warning-fg ring-warning/20",
}

export function StatStrip({ stats }: { stats: ReadonlyArray<StatSpec> }) {
  return (
    <Card className="rounded-md">
      <CardContent className="flex flex-col p-0 md:flex-row">
        {stats.map((stat, i) => (
          <StatCell key={stat.id} stat={stat} withDivider={i > 0} />
        ))}
      </CardContent>
    </Card>
  )
}

function StatCell({ stat, withDivider }: { stat: StatSpec; withDivider: boolean }) {
  return (
    <div
      className={cn(
        "flex flex-1 flex-col gap-1 px-4 py-3",
        withDivider && "border-t border-border-subtle md:border-l md:border-t-0",
      )}
    >
      <div className="flex items-center gap-2">
        <span
          className={cn(
            "flex size-6 shrink-0 items-center justify-center rounded-md ring-1",
            TONE_BADGE[stat.tone],
          )}
          aria-hidden
        >
          <stat.icon className="size-3.5" />
        </span>
        <span className="min-w-0 flex-1 truncate text-sm font-medium text-fg">{stat.label}</span>
        {stat.delta ? <DeltaBadge delta={stat.delta} /> : null}
      </div>
      <div className="flex items-end justify-between gap-2">
        {stat.loading ? (
          <Skeleton className="h-7 w-12" />
        ) : (
          <span
            className={cn("text-2xl font-semibold", stat.error ? "text-fg-subtle" : "text-fg")}
            title={stat.error ? "Failed to load" : undefined}
          >
            {stat.error ? "-" : stat.value}
          </span>
        )}
        {stat.spark && !stat.loading && !stat.error ? <Sparkline points={stat.spark} /> : null}
      </div>
      {stat.hint ? <p className="truncate text-xs text-fg-muted">{stat.hint}</p> : null}
    </div>
  )
}

function DeltaBadge({ delta }: { delta: StatDelta }) {
  return (
    <span
      className={cn(
        "inline-flex items-center gap-0.5 rounded-sm px-1.5 text-xs font-medium tabular-nums ring-1",
        delta.tone === "success"
          ? "bg-success-soft text-success-fg ring-success/20"
          : "bg-danger-soft text-danger-fg ring-danger/20",
      )}
    >
      {delta.direction === "up" ? "↑" : "↓"} {delta.label}
    </span>
  )
}

/** Decorative trend; the chart below carries the readable version. */
function Sparkline({ points }: { points: number[] }) {
  const max = Math.max(...points, 1)
  return (
    <div className="flex h-7 items-end gap-0.5" aria-hidden>
      {points.map((value, i) => (
        <div
          key={i}
          className={cn(
            "w-1 rounded-t-[1px]",
            i === points.length - 1 ? "bg-primary" : "bg-fg-subtle/30",
          )}
          style={{ height: `${Math.max((value / max) * 100, 4)}%` }}
        />
      ))}
    </div>
  )
}
