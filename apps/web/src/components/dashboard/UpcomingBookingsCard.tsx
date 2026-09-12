/**
 * The week ahead as the sessions themselves: when, what, with whom.
 *
 * Day counts said "3 bookings" and left the operator to go find out which.
 * The rows come from the sessions list endpoint rather than the dashboard
 * aggregate, which carries counts only; record-level data stays on the
 * endpoint that already serves it, with the same authorization.
 *
 * Deliberately not part of the sessions series. Delivery and demand are
 * different facts, and folding bookings into the delivered chart was the
 * mistake the schema decision guards against.
 */

import { useState } from "react"

import { useQuery } from "@tanstack/react-query"
import { Link } from "@tanstack/react-router"
import { ArrowUpRight, CalendarPlus, ChevronRight } from "lucide-react"

import { serviceSessionsApi } from "@/api/endpoints/service-sessions"
import type { UpcomingBookings } from "@/api/generated"
import { Card, CardContent } from "@/components/ui/card"
import { Skeleton } from "@/components/ui/skeleton"
import { entityListKey } from "@/lib/queries"
import type { ServiceSession } from "@/types/entities"
import { SessionStatus } from "@/types/enums"

import { CardBar, CardEmptyState, CardStat } from "./CardBar"

const SHOWN = 6
const WINDOW_DAYS = 7
const OPEN_BOOKING_STATUSES: ReadonlyArray<string> = [
  SessionStatus.SCHEDULED,
  SessionStatus.RESCHEDULED,
]

/** "Tue 02, 14:00" — enough to act on, short enough for one row. */
function formatSlot(iso: string): string {
  const d = new Date(iso)
  if (Number.isNaN(d.getTime())) return ""
  const day = d.toLocaleDateString(undefined, { weekday: "short", day: "2-digit" })
  const time = d.toLocaleTimeString(undefined, {
    hour: "2-digit",
    minute: "2-digit",
    hour12: false,
  })
  return `${day}, ${time}`
}

/** Client with the member when named, then the counsellor, one muted run. */
function participants(session: ServiceSession): string {
  const who = [session.client_name, session.member_display_label].filter(Boolean).join(" / ")
  return [who, session.provider_display_name].filter(Boolean).join(" · ")
}

function useWeekAhead(enabled: boolean) {
  // Anchored per mount: an inline `new Date()` would mint a fresh query key
  // on every render and refetch forever, the trap the sessions list page
  // documents on its own range params.
  const [from] = useState(() => new Date())
  const to = new Date(from.getTime() + WINDOW_DAYS * 24 * 60 * 60 * 1000)
  const params = {
    limit: 20,
    scheduled_from: from.toISOString(),
    scheduled_to: to.toISOString(),
    sort_by: "scheduled_at",
    sort_desc: false,
  }
  return useQuery({
    queryKey: entityListKey("service-sessions", { ...params, card: "week-ahead" }),
    queryFn: () => serviceSessionsApi.list(params),
    staleTime: 60_000,
    enabled,
    select: (page) =>
      page.items.filter((s) => OPEN_BOOKING_STATUSES.includes(s.status)).slice(0, SHOWN),
  })
}

interface UpcomingBookingsCardProps {
  /** The aggregate's count, which stays authoritative for the header figure. */
  upcoming: UpcomingBookings | null
  loading?: boolean
}

export function UpcomingBookingsCard({ upcoming, loading }: UpcomingBookingsCardProps) {
  const total = upcoming?.total ?? 0
  const rows = useWeekAhead(total > 0)
  const sessions = rows.data ?? []
  const overflow = total - sessions.length

  return (
    <Card className="flex flex-col rounded-md">
      <CardBar
        title="Upcoming sessions"
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
        {upcoming ? <CardStat value={total.toLocaleString()} label="booked" /> : null}
      </CardBar>
      <CardContent className="flex-1 p-3">
        {loading || !upcoming || (total > 0 && rows.isPending) ? (
          <Skeleton className="h-16 w-full" />
        ) : total === 0 ? (
          <CardEmptyState
            icon={CalendarPlus}
            title="Nothing booked yet"
            description="Bookings for the coming week will list here as they land."
          />
        ) : (
          <>
            <ul className="divide-y divide-fg/5">
              {sessions.map((session) => (
                <li key={session.id}>
                  <Link
                    to="/service-sessions/$sessionId"
                    params={{ sessionId: session.id }}
                    className="group flex items-center gap-1.5 py-1.5"
                  >
                    <span className="w-24 shrink-0 text-xs tabular-nums text-fg-muted">
                      {formatSlot(session.scheduled_at)}
                    </span>
                    <span className="min-w-0 truncate text-sm font-medium text-fg group-hover:text-primary">
                      {session.service_name ?? "Session"}
                    </span>
                    <span className="min-w-0 truncate text-xs text-fg-muted">
                      {participants(session)}
                    </span>
                    <ChevronRight
                      aria-hidden
                      className="ml-auto size-3.5 shrink-0 text-fg-subtle transition-transform group-hover:translate-x-0.5 group-hover:text-primary"
                    />
                  </Link>
                </li>
              ))}
            </ul>
            {overflow > 0 ? (
              <Link
                to="/service-sessions"
                className="mt-1.5 inline-flex items-center gap-1 text-xs text-fg-muted hover:text-primary"
              >
                and {overflow} more this week
                <ArrowUpRight className="size-3" aria-hidden />
              </Link>
            ) : null}
          </>
        )}
      </CardContent>
    </Card>
  )
}
