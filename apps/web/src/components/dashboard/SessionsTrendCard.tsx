/**
 * Twelve months of completed sessions as a single-hue column chart.
 * Each month band is its own hover and focus target; the latest month with
 * data carries a direct label, gridline ticks carry the rest.
 */

import { useState } from "react"

import type { MonthlySessions } from "@/api/generated"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Skeleton } from "@/components/ui/skeleton"
import { monthLabel, monthLabelLong, niceTicks } from "@/lib/dashboard"
import { cn } from "@/lib/utils"

interface SessionsTrendCardProps {
  monthly: ReadonlyArray<MonthlySessions>
  loading?: boolean
  error?: boolean
}

export function SessionsTrendCard({ monthly, loading, error }: SessionsTrendCardProps) {
  return (
    <Card className="rounded-md">
      <CardHeader className="border-b border-border p-3">
        <CardTitle className="text-sm font-semibold text-fg">Sessions delivered</CardTitle>
        <p className="text-xs text-fg-muted">Completed sessions per month, last 12 months</p>
      </CardHeader>
      <CardContent className="p-4">
        <TrendBody monthly={monthly} loading={loading} error={error} />
      </CardContent>
    </Card>
  )
}

function TrendBody({ monthly, loading, error }: SessionsTrendCardProps) {
  if (loading) return <Skeleton className="h-52 w-full" />
  if (error) return <ChartMessage text="Sessions could not be loaded." />
  if (monthly.every((m) => m.total === 0)) {
    return <ChartMessage text="No completed sessions in the last 12 months." />
  }
  return <TrendChart monthly={monthly} />
}

function ChartMessage({ text }: { text: string }) {
  return (
    <div className="flex h-52 items-center justify-center">
      <p className="text-sm text-fg-muted">{text}</p>
    </div>
  )
}

function TrendChart({ monthly }: { monthly: ReadonlyArray<MonthlySessions> }) {
  const [active, setActive] = useState<number | null>(null)
  const ticks = niceTicks(Math.max(...monthly.map((m) => m.total)))
  const top = ticks[ticks.length - 1]
  const labelled = monthly.reduce((last, m, i) => (m.total > 0 ? i : last), -1)

  return (
    <div className="relative" onMouseLeave={() => setActive(null)}>
      <div className="relative ml-8 h-44">
        {ticks.map((tick) => (
          <GridLine key={tick} tick={tick} top={top} />
        ))}
        <div className="absolute inset-0 flex items-end gap-0.5">
          {monthly.map((m, i) => (
            <MonthBand
              key={m.month}
              month={m}
              heightPct={(m.total / top) * 100}
              active={active === i}
              showLabel={i === labelled && active === null}
              onEnter={() => setActive(i)}
              onLeave={() => setActive((current) => (current === i ? null : current))}
            />
          ))}
        </div>
        {active !== null ? <TrendTooltip monthly={monthly} index={active} /> : null}
      </div>
      <div className="ml-8 flex gap-0.5 pt-1">
        {monthly.map((m, i) => (
          <span
            key={m.month}
            className={cn(
              "flex-1 text-center text-[10px] text-fg-subtle",
              i % 2 === 1 && "max-md:invisible",
            )}
          >
            {monthLabel(m.month)}
          </span>
        ))}
      </div>
    </div>
  )
}

function GridLine({ tick, top }: { tick: number; top: number }) {
  return (
    <div
      className="absolute inset-x-0 border-t border-border-default"
      style={{ bottom: `${(tick / top) * 100}%` }}
      aria-hidden
    >
      <span className="absolute -left-8 w-7 -translate-y-1/2 pr-1 text-right text-[10px] tabular-nums text-fg-subtle">
        {tick.toLocaleString()}
      </span>
    </div>
  )
}

interface MonthBandProps {
  month: MonthlySessions
  heightPct: number
  active: boolean
  showLabel: boolean
  onEnter: () => void
  onLeave: () => void
}

function MonthBand({ month, heightPct, active, showLabel, onEnter, onLeave }: MonthBandProps) {
  return (
    <Button
      type="button"
      variant="ghost"
      className="group relative h-full flex-1 items-end justify-center rounded-sm p-0 hover:bg-transparent"
      onMouseEnter={onEnter}
      onFocus={onEnter}
      onBlur={onLeave}
      aria-label={`${monthLabelLong(month.month)}: ${month.total} sessions`}
    >
      <div
        className={cn(
          "relative w-full max-w-6 rounded-t bg-primary transition-opacity",
          active && "opacity-75",
        )}
        style={{ height: `${heightPct}%` }}
      >
        {showLabel && month.total > 0 ? (
          <span className="absolute -top-4 left-1/2 -translate-x-1/2 text-[10px] font-medium tabular-nums text-fg-muted">
            {month.total}
          </span>
        ) : null}
      </div>
    </Button>
  )
}

function TrendTooltip({
  monthly,
  index,
}: {
  monthly: ReadonlyArray<MonthlySessions>
  index: number
}) {
  const month = monthly[index]
  const centerPct = ((index + 0.5) / monthly.length) * 100
  return (
    <div
      className="pointer-events-none absolute -top-2 z-10 -translate-x-1/2 rounded-md border border-border bg-surface-elevated px-2 py-1 shadow-md"
      style={{ left: `${centerPct}%` }}
      role="status"
    >
      <p className="whitespace-nowrap text-sm font-semibold tabular-nums text-fg">
        {month.total} {month.total === 1 ? "session" : "sessions"}
      </p>
      <p className="whitespace-nowrap text-xs text-fg-muted">{monthLabelLong(month.month)}</p>
    </div>
  )
}
