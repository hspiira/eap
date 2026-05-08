import { Calendar, Check, ClipboardCopy, Clock, MapPin, Pencil, TrendingUp } from "lucide-react"

import { Button } from "@/components/ui/button"
import { cn } from "@/lib/utils"

const events = [
  {
    id: "1",
    name: "Poolside Party",
    date: "April 27",
    time: "5:00 PM",
    location: "Los Angeles, CA",
    attendees: "+45 more are down",
    avatarColors: ["var(--palette-accent-red-deep)", "var(--palette-neutral-50)", "var(--palette-accent-blue)"],
    amount: "$5,790.00",
    amountPositive: true,
    dailyLabel: "Today",
    dailyChange: "6.5%",
    dailyChangePositive: true,
    status: null,
    showPublish: false,
  },
  {
    id: "2",
    name: "Rave",
    date: "June 4",
    time: "7:00 PM",
    location: "Miami, FL",
    attendees: null,
    avatarColors: [],
    amount: "$0.00",
    amountPositive: false,
    dailyLabel: "Today",
    dailyChange: "0.0%",
    dailyChangePositive: false,
    status: "Draft",
    showPublish: true,
  },
]

function EventCard({
  name,
  date,
  time,
  location,
  attendees,
  avatarColors,
  amount,
  amountPositive,
  dailyLabel,
  dailyChange,
  dailyChangePositive,
  status,
  showPublish,
}: (typeof events)[0]) {
  return (
    <article
      className={cn(
        "rounded-lg border border-border/25 bg-white p-5",
        "shadow-[0_1px_4px_rgba(0,0,0,0.06)]"
      )}
    >
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div className="min-w-0 flex-1 space-y-2">
          <h3 className="text-lg font-bold text-fg">{name}</h3>
          <div className="flex flex-wrap items-center gap-x-4 gap-y-1 text-sm text-fg/70">
            <span className="flex items-center gap-1.5">
              <Calendar className="h-3.5 w-3.5 shrink-0" />
              {date}
            </span>
            <span className="flex items-center gap-1.5">
              <Clock className="h-3.5 w-3.5 shrink-0" />
              {time}
            </span>
          </div>
          <div className="flex items-center gap-1.5 text-sm text-fg/70">
            <MapPin className="h-3.5 w-3.5 shrink-0" />
            <span>& {location}</span>
          </div>
          {attendees ? (
            <div className="flex items-center gap-2 pt-0.5">
              <div className="flex -space-x-2">
                {avatarColors.map((color, i) => (
                  <div
                    key={i}
                    className="h-6 w-6 shrink-0 rounded-full border-2 border-white"
                    style={{ backgroundColor: color }}
                  />
                ))}
              </div>
              <span className="text-sm text-fg/70">{attendees}</span>
            </div>
          ) : status ? (
            <span className="inline-block rounded-md border border-border/40 bg-neutral-50 px-2 py-0.5 text-xs font-medium text-fg/80">
              {status}
            </span>
          ) : null}
        </div>
        <div className="flex flex-col items-end gap-1 text-right">
          <span
            className={cn(
              "text-xl font-bold tabular-nums",
              amountPositive ? "text-primary" : "text-fg"
            )}
          >
            {amount}
          </span>
          <div className="flex items-center gap-1.5 text-sm text-fg/70">
            <span>{dailyLabel}</span>
            {dailyChangePositive ? (
              <span className="inline-flex items-center gap-0.5 rounded border border-primary/40 bg-primary/10 px-1.5 py-0.5 text-xs font-medium text-primary">
                <TrendingUp className="h-3 w-3" />
                {dailyChange}
              </span>
            ) : (
              <span className="text-xs text-fg/70">{dailyChange}</span>
            )}
          </div>
        </div>
      </div>
      <div className="mt-4 flex flex-wrap gap-2 border-t border-border/20 pt-4">
        <Button
          variant="secondary"
          size="sm"
          className="rounded-md border border-fg/20 bg-neutral-50 text-fg hover:bg-neutral-100"
        >
          <Pencil className="mr-1.5 h-3.5 w-3.5" />
          Edit Event
        </Button>
        <Button
          variant="secondary"
          size="sm"
          className="rounded-md border border-fg/20 bg-neutral-50 text-fg hover:bg-neutral-100"
        >
          <ClipboardCopy className="mr-1.5 h-3.5 w-3.5" />
          Copy Link
        </Button>
        {showPublish && (
          <Button
            size="sm"
            className="rounded-md bg-fg text-white hover:bg-surface-slate"
          >
            <Check className="mr-1.5 h-3.5 w-3.5" />
            Publish
          </Button>
        )}
      </div>
    </article>
  )
}

export function EventCards() {
  return (
    <div className="space-y-4">
      {events.map((event) => (
        <EventCard key={event.id} {...event} />
      ))}
    </div>
  )
}
