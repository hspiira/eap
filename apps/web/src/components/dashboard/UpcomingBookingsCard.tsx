/**
 * The booking pipeline for the week ahead, as a plain list of days.
 *
 * A list rather than a chart: a handful of bookings across seven days is a
 * work list, not a trend, and rows read at a glance where thin bars only
 * decorate. Days with nothing booked stay out of the list.
 *
 * Deliberately not part of the sessions series. Delivery and demand are
 * different facts, and folding bookings into the delivered chart was the
 * mistake the schema decision guards against; this card gives the pipeline
 * its own name instead.
 */

import { Link } from "@tanstack/react-router"
import { ArrowUpRight, CalendarPlus } from "lucide-react"

import type { UpcomingBookings } from "@/api/generated"
import { Card, CardContent } from "@/components/ui/card"
import { Skeleton } from "@/components/ui/skeleton"

import { CardBar, CardEmptyState, CardStat } from "./CardBar"

interface UpcomingBookingsCardProps {
  upcoming: UpcomingBookings | null
  loading?: boolean
}

export function UpcomingBookingsCard({ upcoming, loading }: UpcomingBookingsCardProps) {
  const booked = upcoming?.days.filter((day) => day.total > 0) ?? []
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
          <Skeleton className="h-16 w-full" />
        ) : booked.length === 0 ? (
          <CardEmptyState
            icon={CalendarPlus}
            title="Nothing booked yet"
            description="Bookings for the coming week will list here as they land."
          />
        ) : (
          <ul className="divide-y divide-fg/5">
            {booked.map((day) => (
              <li
                key={day.bucket}
                className="flex items-baseline gap-1.5 py-1.5 first:pt-0 last:pb-0"
              >
                <span className="w-16 shrink-0 text-xs text-fg-muted">{day.label}</span>
                <span className="text-sm font-medium tabular-nums text-fg">{day.total}</span>
                <span className="text-xs text-fg-muted">booking{day.total === 1 ? "" : "s"}</span>
              </li>
            ))}
          </ul>
        )}
      </CardContent>
    </Card>
  )
}
