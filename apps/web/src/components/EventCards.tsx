import {
  Calendar,
  Check,
  ClipboardCopy,
  Clock,
  MapPin,
  Pencil,
  TrendingUp,
} from "lucide-react"

import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import {
  Card,
  CardContent,
} from "@/components/ui/card"
import { cn } from "@/lib/utils"

export interface ScheduledEvent {
  id: string
  name: string
  date: string
  time: string
  location: string
  attendees?: number | null
  avatarTones?: ReadonlyArray<"info" | "success" | "warning" | "danger">
  amount?: string
  amountTone?: "primary" | "neutral"
  dailyLabel?: string
  dailyChange?: string
  dailyChangePositive?: boolean
  status?: string | null
  showPublish?: boolean
}

const DEFAULT_EVENTS: ReadonlyArray<ScheduledEvent> = [
  {
    id: "evt-1",
    name: "Q2 wellness town hall",
    date: "April 27",
    time: "5:00 PM",
    location: "Acme Holdings, Kampala",
    attendees: 45,
    avatarTones: ["info", "success", "warning"],
    amount: "$5,790.00",
    amountTone: "primary",
    dailyLabel: "RSVPs",
    dailyChange: "6.5%",
    dailyChangePositive: true,
  },
  {
    id: "evt-2",
    name: "Manager training cohort",
    date: "June 4",
    time: "7:00 PM",
    location: "Beta Industries, Mombasa",
    amount: "$0.00",
    amountTone: "neutral",
    dailyLabel: "RSVPs",
    dailyChange: "0.0%",
    status: "Draft",
    showPublish: true,
  },
]

const TONE_BG: Record<NonNullable<ScheduledEvent["avatarTones"]>[number], string> = {
  info: "bg-info",
  success: "bg-success",
  warning: "bg-warning",
  danger: "bg-danger",
}

interface EventCardsProps {
  events?: ReadonlyArray<ScheduledEvent>
}

export function EventCards({ events = DEFAULT_EVENTS }: EventCardsProps = {}) {
  return (
    <div className="grid gap-4">
      {events.map((event) => (
        <EventCard key={event.id} event={event} />
      ))}
    </div>
  )
}

function EventCard({ event }: { event: ScheduledEvent }) {
  return (
    <Card className="rounded-md">
      <CardContent className="p-4">
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div className="min-w-0 flex-1 grid gap-2">
            <h3 className="text-base font-semibold text-fg">{event.name}</h3>
            <div className="flex flex-wrap items-center gap-x-4 gap-y-1 text-sm text-fg-muted">
              <span className="flex items-center gap-1.5">
                <Calendar className="size-3.5 shrink-0" aria-hidden />
                <span className="font-mono tabular-nums">{event.date}</span>
              </span>
              <span className="flex items-center gap-1.5">
                <Clock className="size-3.5 shrink-0" aria-hidden />
                <span className="font-mono tabular-nums">{event.time}</span>
              </span>
            </div>
            <div className="flex items-center gap-1.5 text-sm text-fg-muted">
              <MapPin className="size-3.5 shrink-0" aria-hidden />
              <span>{event.location}</span>
            </div>
            {event.attendees ? (
              <div className="flex items-center gap-2 pt-0.5">
                <div className="flex -space-x-1.5">
                  {(event.avatarTones ?? []).map((tone, i) => (
                    <span
                      key={i}
                      className={cn(
                        "size-5 shrink-0 rounded-full border-2 border-bg",
                        TONE_BG[tone],
                      )}
                      aria-hidden
                    />
                  ))}
                </div>
                <span className="font-mono text-sm tabular-nums text-fg-muted">
                  +{event.attendees} attendees
                </span>
              </div>
            ) : event.status ? (
              <Badge variant="outline" size="sm" className="w-fit">
                {event.status}
              </Badge>
            ) : null}
          </div>

          <div className="flex flex-col items-end gap-1 text-right">
            {event.amount ? (
              <span
                className={cn(
                  "font-mono text-lg font-semibold tabular-nums",
                  event.amountTone === "primary" ? "text-primary" : "text-fg",
                )}
              >
                {event.amount}
              </span>
            ) : null}
            {event.dailyChange ? (
              <div className="flex items-center gap-1.5 text-sm text-fg-muted">
                {event.dailyLabel ? <span>{event.dailyLabel}</span> : null}
                {event.dailyChangePositive ? (
                  <Badge
                    variant="secondary"
                    size="sm"
                    className="font-mono tabular-nums text-success"
                  >
                    <TrendingUp className="size-3" />
                    {event.dailyChange}
                  </Badge>
                ) : (
                  <span className="font-mono text-xs tabular-nums text-fg-muted">
                    {event.dailyChange}
                  </span>
                )}
              </div>
            ) : null}
          </div>
        </div>

        <div className="mt-4 flex flex-wrap gap-2 border-t border-border-subtle pt-3">
          <Button variant="outline" size="sm">
            <Pencil className="size-3.5" />
            Edit
          </Button>
          <Button variant="outline" size="sm">
            <ClipboardCopy className="size-3.5" />
            Copy link
          </Button>
          {event.showPublish ? (
            <Button size="sm">
              <Check className="size-3.5" />
              Publish
            </Button>
          ) : null}
        </div>
      </CardContent>
    </Card>
  )
}
