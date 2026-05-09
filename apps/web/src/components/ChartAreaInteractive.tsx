"use client"

import * as React from "react"

import { Area, AreaChart, CartesianGrid, XAxis } from "recharts"

import { Button } from "@/components/ui/button"
import {
  type ChartConfig,
  ChartContainer,
  ChartLegend,
  ChartLegendContent,
  ChartTooltip,
  ChartTooltipContent,
} from "@/components/ui/chart"
import { cn } from "@/lib/utils"

export interface ChartSeries {
  key: string
  label: string
}

export type ChartTimeRange = "7d" | "30d" | "90d"

export interface ChartDataPoint {
  date: string
  [seriesKey: string]: number | string
}

interface ChartAreaInteractiveProps {
  data?: ReadonlyArray<ChartDataPoint>
  series?: ReadonlyArray<ChartSeries>
  timeRange?: ChartTimeRange
  className?: string
  height?: number
}

const DEFAULT_SERIES: ReadonlyArray<ChartSeries> = [
  { key: "sessions", label: "Sessions" },
  { key: "intakes", label: "Intakes" },
]

function generateDefaultData(): ReadonlyArray<ChartDataPoint> {
  const start = new Date()
  start.setDate(start.getDate() - 90)
  const out: ChartDataPoint[] = []
  for (let i = 0; i < 91; i++) {
    const d = new Date(start)
    d.setDate(start.getDate() + i)
    const iso = d.toISOString().slice(0, 10)
    const phase = i / 14
    out.push({
      date: iso,
      sessions: Math.round(180 + Math.sin(phase) * 60 + Math.random() * 60),
      intakes: Math.round(80 + Math.cos(phase * 0.8) * 30 + Math.random() * 30),
    })
  }
  return out
}

const DEFAULT_DATA = generateDefaultData()

export function ChartAreaInteractive({
  data = DEFAULT_DATA,
  series = DEFAULT_SERIES,
  timeRange: initialRange = "30d",
  className,
  height = 220,
}: ChartAreaInteractiveProps = {}) {
  const [timeRange, setTimeRange] = React.useState<ChartTimeRange>(initialRange)

  const filtered = React.useMemo(() => {
    const lookbackDays = timeRange === "7d" ? 7 : timeRange === "30d" ? 30 : 90
    const referenceDate = data.length > 0
      ? new Date(data[data.length - 1].date)
      : new Date()
    const start = new Date(referenceDate)
    start.setDate(referenceDate.getDate() - lookbackDays)
    return data.filter((d) => new Date(d.date) >= start)
  }, [data, timeRange])

  const chartConfig: ChartConfig = React.useMemo(() => {
    const out: ChartConfig = {}
    series.forEach((s, i) => {
      out[s.key] = {
        label: s.label,
        color: i === 0 ? "var(--color-primary)" : "var(--color-fg-muted)",
      }
    })
    return out
  }, [series])

  return (
    <div className={className}>
      <div className="mb-3 flex items-center justify-between">
        <div className="text-xs font-medium tracking-wide text-fg-muted">
          Trend
        </div>
        <RangeToggle value={timeRange} onChange={setTimeRange} />
      </div>
      <ChartContainer config={chartConfig} style={{ height }}>
        <AreaChart data={[...filtered]}>
          <defs>
            {series.map((s) => (
              <linearGradient
                key={s.key}
                id={`fill-${s.key}`}
                x1="0"
                y1="0"
                x2="0"
                y2="1"
              >
                <stop
                  offset="5%"
                  stopColor={`var(--color-${s.key})`}
                  stopOpacity={0.6}
                />
                <stop
                  offset="95%"
                  stopColor={`var(--color-${s.key})`}
                  stopOpacity={0.05}
                />
              </linearGradient>
            ))}
          </defs>
          <CartesianGrid vertical={false} stroke="var(--border-subtle)" />
          <XAxis
            dataKey="date"
            tickLine={false}
            axisLine={false}
            tickMargin={8}
            minTickGap={32}
            tick={{ fill: "var(--fg-subtle)", fontSize: 11 }}
            tickFormatter={(value) =>
              new Date(value as string).toLocaleDateString(undefined, {
                month: "short",
                day: "numeric",
              })
            }
          />
          <ChartTooltip
            cursor={false}
            content={
              <ChartTooltipContent
                labelFormatter={(value) =>
                  new Date(value as string).toLocaleDateString(undefined, {
                    month: "short",
                    day: "numeric",
                    year: "numeric",
                  })
                }
                indicator="dot"
              />
            }
          />
          {series.map((s) => (
            <Area
              key={s.key}
              dataKey={s.key}
              type="monotone"
              fill={`url(#fill-${s.key})`}
              stroke={`var(--color-${s.key})`}
              strokeWidth={1.5}
              stackId={undefined}
            />
          ))}
          <ChartLegend content={<ChartLegendContent />} />
        </AreaChart>
      </ChartContainer>
    </div>
  )
}

const RANGE_OPTIONS: ReadonlyArray<{ value: ChartTimeRange; label: string }> = [
  { value: "7d", label: "7d" },
  { value: "30d", label: "30d" },
  { value: "90d", label: "90d" },
]

function RangeToggle({
  value,
  onChange,
}: {
  value: ChartTimeRange
  onChange: (next: ChartTimeRange) => void
}) {
  return (
    <div
      role="radiogroup"
      aria-label="Time range"
      className="inline-flex rounded-sm border border-border-subtle bg-surface p-0.5"
    >
      {RANGE_OPTIONS.map((opt) => {
        const selected = opt.value === value
        return (
          <Button
            key={opt.value}
            type="button"
            variant="ghost"
            size="sm"
            role="radio"
            aria-checked={selected}
            onClick={() => onChange(opt.value)}
            className={cn(
              "h-auto rounded-sm px-2 py-0.5 font-mono text-xs tabular-nums",
              selected
                ? "bg-primary text-primary-foreground hover:bg-primary hover:text-primary-foreground"
                : "text-fg-muted hover:bg-transparent hover:text-fg",
            )}
          >
            {opt.label}
          </Button>
        )
      })}
    </div>
  )
}
