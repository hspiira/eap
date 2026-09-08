/**
 * Sessions by category as an active donut: hovering or focusing a slice
 * lifts it and writes its label and share into the middle of the ring.
 * The legend carries the counts, so identity never rests on colour alone.
 */

import { useState } from "react"

import { PieChart as PieChartIcon } from "lucide-react"
import { Cell, Label, Pie, PieChart, Sector } from "recharts"
import type { PieSectorDataItem } from "recharts/types/polar/Pie"

import type { CategoryCount } from "@/api/generated"
import { Card, CardContent } from "@/components/ui/card"
import { type ChartConfig, ChartContainer, ChartTooltip } from "@/components/ui/chart"
import { Skeleton } from "@/components/ui/skeleton"

import { CardBar, CardEmptyState } from "./CardBar"

const SLOTS = [
  "var(--color-chart-1)",
  "var(--color-chart-2)",
  "var(--color-chart-3)",
  "var(--color-chart-4)",
]

interface CategoryDonutCardProps {
  categories: ReadonlyArray<CategoryCount>
  loading?: boolean
}

export function CategoryDonutCard({ categories, loading }: CategoryDonutCardProps) {
  const [active, setActive] = useState<number | null>(null)
  const total = categories.reduce((sum, c) => sum + c.total, 0)
  const config = Object.fromEntries(
    categories.map((c, i) => [c.category, { label: c.category, color: SLOTS[i % SLOTS.length] }]),
  ) satisfies ChartConfig

  return (
    <Card className="flex h-full flex-col rounded-md">
      <CardBar title="By category" />
      <CardContent className="grid flex-1 content-center gap-3 p-3 sm:grid-cols-[9rem_1fr] sm:items-center">
        {loading ? (
          <Skeleton className="h-36 w-full sm:col-span-2" />
        ) : total === 0 ? (
          <CardEmptyState
            icon={PieChartIcon}
            title="No categorised sessions"
            description="A breakdown will appear here once sessions are logged in this window."
            className="sm:col-span-2"
          />
        ) : (
          <>
            <Donut
              categories={categories}
              config={config}
              total={total}
              active={active}
              onActive={setActive}
            />
            <CategoryLegend
              categories={categories}
              total={total}
              active={active}
              onActive={setActive}
            />
          </>
        )}
      </CardContent>
    </Card>
  )
}

interface DonutProps {
  categories: ReadonlyArray<CategoryCount>
  config: ChartConfig
  total: number
  active: number | null
  onActive: (index: number | null) => void
}

function Donut({ categories, config, total, active, onActive }: DonutProps) {
  const shown = active ?? -1
  const centreValue = active === null ? total : categories[active].total
  const centreLabel = active === null ? "sessions" : categories[active].category

  return (
    <ChartContainer config={config} className="mx-auto aspect-square h-36 w-36">
      <PieChart>
        <ChartTooltip content={() => null} />
        <Pie
          data={categories as CategoryCount[]}
          dataKey="total"
          nameKey="category"
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
          {categories.map((category, i) => (
            <Cell key={category.category} fill={SLOTS[i % SLOTS.length]} />
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

function CategoryLegend({
  categories,
  total,
  active,
  onActive,
}: {
  categories: ReadonlyArray<CategoryCount>
  total: number
  active: number | null
  onActive: (index: number | null) => void
}) {
  return (
    <ul className="grid gap-1.5">
      {categories.map((category, i) => (
        <li
          key={category.category}
          className="flex items-center gap-2"
          onMouseEnter={() => onActive(i)}
          onMouseLeave={() => onActive(null)}
        >
          <span
            className="size-2.5 shrink-0 rounded-[2px]"
            style={{ background: SLOTS[i % SLOTS.length] }}
            aria-hidden
          />
          <span
            className={
              "min-w-0 flex-1 truncate text-sm " +
              (active === i ? "font-medium text-fg" : "text-fg-muted")
            }
          >
            {category.category}
          </span>
          <span className="text-sm font-medium tabular-nums text-fg">
            {category.total.toLocaleString()}
          </span>
          <span className="w-9 text-right text-xs tabular-nums text-fg-subtle">
            {Math.round((category.total / total) * 100)}%
          </span>
        </li>
      ))}
    </ul>
  )
}
