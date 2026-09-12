/**
 * The booking pipeline for the week ahead: one thin column per day.
 *
 * Deliberately not part of the sessions series. Delivery and demand are
 * different facts, and folding bookings into the delivered chart was the
 * mistake the schema decision guards against; this card gives the pipeline
 * its own name instead.
 */

import { Link } from "@tanstack/react-router"
import { ArrowUpRight, CalendarPlus } from "lucide-react"
import { Bar, BarChart, CartesianGrid, XAxis, YAxis } from "recharts"

import type { UpcomingBookings } from "@/api/generated"
import { Card, CardContent } from "@/components/ui/card"
import {
  type ChartConfig,
  ChartContainer,
  ChartTooltip,
  ChartTooltipContent,
} from "@/components/ui/chart"
import { Skeleton } from "@/components/ui/skeleton"

import { CardBar, CardEmptyState, CardInsight, CardStat } from "./CardBar"

const CHART_CONFIG = {
  total: { label: "Bookings", color: "var(--color-chart-1)" },
} satisfies ChartConfig

interface UpcomingBookingsCardProps {
  upcoming: UpcomingBookings | null
  insight?: string | null
  loading?: boolean
}

export function UpcomingBookingsCard({ upcoming, insight, loading }: UpcomingBookingsCardProps) {
  return (
    <Card className="flex flex-col rounded-md">
      <CardBar
        title="Next 7 days"
        control={
          <Link
            to="/service-sessions"
            className="inline-flex items-center gap-1 text-xs text-fg-muted hover:text-primary"
          >
            Sessions
            <ArrowUpRight className="size-3" aria-hidden />
          </Link>
        }
      >
        {upcoming ? <CardStat value={upcoming.total.toLocaleString()} label="booked" /> : null}
      </CardBar>
      <CardContent className="flex-1 p-3">
        {loading || !upcoming ? (
          <Skeleton className="h-28 w-full" />
        ) : upcoming.total === 0 ? (
          <CardEmptyState
            icon={CalendarPlus}
            title="Nothing booked yet"
            description="Bookings for the coming week will chart here as they land."
          />
        ) : (
          <ChartContainer config={CHART_CONFIG} className="h-28 w-full">
            <BarChart data={[...upcoming.days]} margin={{ top: 4, right: 4, bottom: 0, left: 4 }}>
              <CartesianGrid vertical={false} strokeOpacity={0.35} />
              <XAxis dataKey="label" tickLine={false} axisLine={false} fontSize={10} />
              <YAxis hide allowDecimals={false} />
              <ChartTooltip content={<ChartTooltipContent />} />
              <Bar
                dataKey="total"
                fill="var(--color-total)"
                radius={[4, 4, 0, 0]}
                maxBarSize={22}
              />
            </BarChart>
          </ChartContainer>
        )}
      </CardContent>
      {loading || !upcoming || upcoming.total === 0 ? null : <CardInsight text={insight ?? null} />}
    </Card>
  )
}
