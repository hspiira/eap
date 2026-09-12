/**
 * Sessions delivered over the selected window, one band per delivery type.
 *
 * Area rather than columns: the window control changes both the bucket count
 * and the density, and a filled band stays readable from seven daily points
 * up to twenty-six weekly ones, where columns would thin to slivers.
 *
 * The bands are overlaid, not stacked. Stacked, the upper band's line sits at
 * the running total while its thickness carries its own value, so a reader
 * following the Online line reads the total and disbelieves the tooltip. Each
 * line now meets the axis at its own value; the bucket total moves to the
 * tooltip label, which is the only place it was ever readable anyway.
 */

import { CalendarX2 } from "lucide-react"
import { Area, AreaChart, CartesianGrid, XAxis, YAxis } from "recharts"

import type { SeriesPoint } from "@/api/generated"
import { Card, CardContent } from "@/components/ui/card"
import {
  type ChartConfig,
  ChartContainer,
  ChartLegend,
  ChartLegendContent,
  ChartTooltip,
  ChartTooltipContent,
} from "@/components/ui/chart"
import { Skeleton } from "@/components/ui/skeleton"

import { CardBar, CardEmptyState, CardInsight, CardStat } from "./CardBar"

const CHART_CONFIG = {
  physical: { label: "Physical", color: "var(--color-chart-1)" },
  online: { label: "Online", color: "var(--color-chart-2)" },
  unknown: { label: "Not recorded", color: "var(--color-chart-muted)" },
} satisfies ChartConfig

const BANDS = [{ key: "physical" }, { key: "online" }, { key: "unknown" }] as const

interface AreaBodyProps {
  series: ReadonlyArray<SeriesPoint>
  loading?: boolean
  error?: boolean
  refreshing?: boolean
}

interface SessionsAreaCardProps extends AreaBodyProps {
  total: number
  delta?: React.ReactNode
  control?: React.ReactNode
  insight?: string | null
}

export function SessionsAreaCard({
  series,
  total,
  delta,
  loading,
  error,
  refreshing,
  control,
  insight,
}: SessionsAreaCardProps) {
  const split = totals(series)
  return (
    <Card className="flex h-full flex-col rounded-md">
      <CardBar title="Sessions delivered" control={control}>
        <CardStat value={total.toLocaleString()} label="delivered" />
        {delta}
        {split.online > 0 || split.physical > 0 ? (
          <CardStat
            value={`${Math.round((split.online / Math.max(split.online + split.physical, 1)) * 100)}%`}
            label="online"
          />
        ) : null}
      </CardBar>
      <CardContent className="flex flex-1 flex-col justify-center p-3 pt-4">
        <AreaBody series={series} loading={loading} error={error} refreshing={refreshing} />
      </CardContent>
      {loading || error ? null : <CardInsight text={insight ?? null} />}
    </Card>
  )
}

function totals(series: ReadonlyArray<SeriesPoint>) {
  return series.reduce(
    (acc, p) => ({ physical: acc.physical + p.physical, online: acc.online + p.online }),
    { physical: 0, online: 0 },
  )
}

function AreaBody({ series, loading, error, refreshing }: AreaBodyProps) {
  if (loading) return <Skeleton className="h-[220px] w-full" />
  if (error) {
    return <Message text="Sessions could not be loaded." />
  }
  if (series.every((p) => p.total === 0)) {
    return (
      <div className="flex h-[220px] items-center justify-center">
        <CardEmptyState
          icon={CalendarX2}
          title="No completed sessions"
          description="Sessions delivered in this window will chart here once logged."
        />
      </div>
    )
  }
  // A band with nothing in it still draws its stroke along the top of the
  // stack, which reads as a flat series rather than an absent one.
  const bands = BANDS.filter((band) => series.some((point) => point[band.key] > 0))
  return (
    <ChartContainer
      config={CHART_CONFIG}
      className="h-[220px] w-full transition-opacity"
      style={{ opacity: refreshing ? 0.6 : 1 }}
    >
      <AreaChart data={series as SeriesPoint[]} margin={{ left: 4, right: 8, top: 4 }}>
        <defs>
          {bands.map((band) => (
            <SeriesGradient
              key={band.key}
              id={`fill-${band.key}`}
              color={`var(--color-${band.key})`}
            />
          ))}
        </defs>
        <CartesianGrid vertical={false} stroke="var(--color-border-default)" />
        <XAxis
          dataKey="label"
          tickLine={false}
          axisLine={false}
          tickMargin={8}
          minTickGap={24}
          className="text-[10px]"
        />
        <YAxis
          tickLine={false}
          axisLine={false}
          width={28}
          allowDecimals={false}
          className="text-[10px]"
        />
        <ChartTooltip
          content={
            <ChartTooltipContent
              indicator="line"
              labelFormatter={(label, items) => (
                <span className="flex items-baseline gap-2">
                  {label}
                  <span className="text-fg-muted">{bucketTotal(items)} total</span>
                </span>
              )}
            />
          }
        />
        <ChartLegend
          verticalAlign="top"
          align="right"
          content={<ChartLegendContent className="flex-nowrap justify-end pt-0 pb-2" />}
        />
        {bands.map((band) => (
          <Area
            key={band.key}
            dataKey={band.key}
            type="monotone"
            stroke={`var(--color-${band.key})`}
            strokeWidth={2}
            fill={`url(#fill-${band.key})`}
          />
        ))}
      </AreaChart>
    </ChartContainer>
  )
}

/** Overlaid bands, so the wash stays light enough to read one through another. */
function SeriesGradient({ id, color }: { id: string; color: string }) {
  return (
    <linearGradient id={id} x1="0" y1="0" x2="0" y2="1">
      <stop offset="5%" stopColor={color} stopOpacity={0.18} />
      <stop offset="95%" stopColor={color} stopOpacity={0.02} />
    </linearGradient>
  )
}

function bucketTotal(items: ReadonlyArray<{ value?: unknown }> = []): number {
  return items.reduce((sum, item) => sum + (Number(item.value) || 0), 0)
}

function Message({ text }: { text: string }) {
  return (
    <div className="flex h-[220px] items-center justify-center">
      <p className="text-sm text-fg-muted">{text}</p>
    </div>
  )
}
