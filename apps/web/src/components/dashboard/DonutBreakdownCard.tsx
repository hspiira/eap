/**
 * A share-of-total donut with its legend, hover-to-lift, and centre readout.
 *
 * One implementation for every "N sessions, grouped by X" card: the caller
 * names the slices and may pin a slice's colour, which is how "Not recorded"
 * stays muted instead of borrowing an identity hue.
 */

import { useState } from "react"

import { PieChart as PieChartIcon } from "lucide-react"
import { Cell, Label, Pie, PieChart, Sector } from "recharts"
import type { PieSectorDataItem } from "recharts/types/polar/Pie"

import { Card, CardContent } from "@/components/ui/card"
import { type ChartConfig, ChartContainer, ChartTooltip } from "@/components/ui/chart"
import { Skeleton } from "@/components/ui/skeleton"

import { CardBar, CardEmptyState, CardErrorState, CardInsight } from "./CardBar"

const SLOTS = [
  "var(--color-chart-1)",
  "var(--color-chart-2)",
  "var(--color-chart-3)",
  "var(--color-chart-4)",
]

export interface DonutSlice {
  key: string
  label: string
  total: number
  /** Pinned colour; slices without one take the next identity slot in order. */
  color?: string
}

interface DonutBreakdownCardProps {
  title: string
  slices: ReadonlyArray<DonutSlice>
  /** The noun under the centre figure, e.g. "sessions". */
  centreNoun: string
  emptyTitle: string
  emptyDescription: string
  insight?: string | null
  loading?: boolean
  error?: boolean
  onRetry?: () => void
}

/** Slot colours skip slices with a pinned colour, so identities stay stable. */
function withColors(slices: ReadonlyArray<DonutSlice>): Array<DonutSlice & { color: string }> {
  let slot = 0
  return slices.map((slice) => ({
    ...slice,
    color: slice.color ?? SLOTS[slot++ % SLOTS.length],
  }))
}

export function DonutBreakdownCard({
  title,
  slices,
  centreNoun,
  emptyTitle,
  emptyDescription,
  insight,
  loading,
  error,
  onRetry,
}: DonutBreakdownCardProps) {
  const [active, setActive] = useState<number | null>(null)
  const colored = withColors(slices)
  const total = colored.reduce((sum, slice) => sum + slice.total, 0)
  const config = Object.fromEntries(
    colored.map((slice) => [slice.key, { label: slice.label, color: slice.color }]),
  ) satisfies ChartConfig

  return (
    <Card className="flex h-full flex-col rounded-md">
      <CardBar title={title} />
      <CardContent className="grid flex-1 content-center gap-3 p-3 sm:grid-cols-[9rem_1fr] sm:items-center">
        {loading ? (
          <Skeleton className="h-36 w-full sm:col-span-2" />
        ) : error ? (
          <CardErrorState
            title={`${title} unavailable`}
            onRetry={onRetry}
            className="sm:col-span-2"
          />
        ) : total === 0 ? (
          <CardEmptyState
            icon={PieChartIcon}
            title={emptyTitle}
            description={emptyDescription}
            className="sm:col-span-2"
          />
        ) : (
          <>
            <Donut
              slices={colored}
              config={config}
              total={total}
              centreNoun={centreNoun}
              active={active}
              onActive={setActive}
            />
            <SliceLegend slices={colored} total={total} active={active} onActive={setActive} />
          </>
        )}
      </CardContent>
      {loading || error || total === 0 ? null : <CardInsight text={insight ?? null} />}
    </Card>
  )
}

interface DonutProps {
  slices: ReadonlyArray<DonutSlice & { color: string }>
  config: ChartConfig
  total: number
  centreNoun: string
  active: number | null
  onActive: (index: number | null) => void
}

function Donut({ slices, config, total, centreNoun, active, onActive }: DonutProps) {
  const shown = active ?? -1
  const centreValue = active === null ? total : slices[active].total
  const centreLabel = active === null ? centreNoun : slices[active].label

  return (
    <ChartContainer config={config} className="mx-auto aspect-square h-36 w-36">
      <PieChart>
        <ChartTooltip content={() => null} />
        <Pie
          data={slices as Array<DonutSlice & { color: string }>}
          dataKey="total"
          nameKey="key"
          innerRadius={44}
          outerRadius={64}
          paddingAngle={2}
          stroke="var(--color-surface)"
          strokeWidth={2}
          activeIndex={shown}
          activeShape={({ outerRadius = 0, ...props }: PieSectorDataItem) => (
            <Sector {...props} outerRadius={outerRadius + 6} />
          )}
          onMouseEnter={(_, index) => onActive(index)}
          onMouseLeave={() => onActive(null)}
        >
          {slices.map((slice) => (
            <Cell key={slice.key} fill={slice.color} />
          ))}
          <Label
            content={({ viewBox }) => {
              if (!viewBox || !("cx" in viewBox)) return null
              return (
                <text x={viewBox.cx} y={viewBox.cy} textAnchor="middle">
                  <tspan x={viewBox.cx} y={viewBox.cy} className="fill-fg text-xl font-semibold">
                    {centreValue.toLocaleString()}
                  </tspan>
                  <tspan
                    x={viewBox.cx}
                    y={(viewBox.cy ?? 0) + 18}
                    className="fill-fg-muted text-xs"
                  >
                    {centreLabel}
                  </tspan>
                </text>
              )
            }}
          />
        </Pie>
      </PieChart>
    </ChartContainer>
  )
}

function SliceLegend({
  slices,
  total,
  active,
  onActive,
}: {
  slices: ReadonlyArray<DonutSlice & { color: string }>
  total: number
  active: number | null
  onActive: (index: number | null) => void
}) {
  return (
    <ul className="grid gap-1.5">
      {slices.map((slice, i) => (
        <li
          key={slice.key}
          className="flex items-center gap-2"
          onMouseEnter={() => onActive(i)}
          onMouseLeave={() => onActive(null)}
        >
          <span
            className="size-2.5 shrink-0 rounded-[2px]"
            style={{ background: slice.color }}
            aria-hidden
          />
          <span
            className={
              "min-w-0 flex-1 truncate text-sm " +
              (active === i ? "font-medium text-fg" : "text-fg-muted")
            }
          >
            {slice.label}
          </span>
          <span className="text-sm font-medium tabular-nums text-fg">
            {slice.total.toLocaleString()}
          </span>
          <span className="w-9 text-right text-xs tabular-nums text-fg-subtle">
            {Math.round((slice.total / total) * 100)}%
          </span>
        </li>
      ))}
    </ul>
  )
}
