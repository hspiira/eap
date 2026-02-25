import { Calendar, Clock, MapPin, Pencil, ClipboardCopy, Check, TrendingUp } from "lucide-react"
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
    avatarColors: ["#b91c1c", "#fafafa", "#1d4ed8"],
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
        "rounded-lg border border-[#bfc4c9]/25 bg-white p-5",
        "shadow-[0_1px_4px_rgba(0,0,0,0.06)]"
      )}
    >
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div className="min-w-0 flex-1 space-y-2">
          <h3 className="text-lg font-bold text-[#5A626A]">{name}</h3>
          <div className="flex flex-wrap items-center gap-x-4 gap-y-1 text-sm text-[#5A626A]/70">
            <span className="flex items-center gap-1.5">
              <Calendar className="h-3.5 w-3.5 shrink-0" />
              {date}
            </span>
            <span className="flex items-center gap-1.5">
              <Clock className="h-3.5 w-3.5 shrink-0" />
              {time}
            </span>
          </div>
          <div className="flex items-center gap-1.5 text-sm text-[#5A626A]/70">
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
              <span className="text-sm text-[#5A626A]/70">{attendees}</span>
            </div>
          ) : status ? (
            <span className="inline-block rounded-md border border-[#bfc4c9]/40 bg-[#f5f5f5] px-2 py-0.5 text-xs font-medium text-[#5A626A]/80">
              {status}
            </span>
          ) : null}
        </div>
        <div className="flex flex-col items-end gap-1 text-right">
          <span
            className={cn(
              "text-xl font-bold tabular-nums",
              amountPositive ? "text-natural" : "text-[#5A626A]"
            )}
          >
            {amount}
          </span>
          <div className="flex items-center gap-1.5 text-sm text-[#5A626A]/70">
            <span>{dailyLabel}</span>
            {dailyChangePositive ? (
              <span className="inline-flex items-center gap-0.5 rounded border border-natural/40 bg-natural/10 px-1.5 py-0.5 text-xs font-medium text-natural">
                <TrendingUp className="h-3 w-3" />
                {dailyChange}
              </span>
            ) : (
              <span className="text-xs text-[#5A626A]/70">{dailyChange}</span>
            )}
          </div>
        </div>
      </div>
      <div className="mt-4 flex flex-wrap gap-2 border-t border-[#bfc4c9]/20 pt-4">
        <Button
          variant="secondary"
          size="sm"
          className="rounded-md border border-[#5A626A]/20 bg-[#f5f5f5] text-[#5A626A] hover:bg-[#ebebeb]"
        >
          <Pencil className="mr-1.5 h-3.5 w-3.5" />
          Edit Event
        </Button>
        <Button
          variant="secondary"
          size="sm"
          className="rounded-md border border-[#5A626A]/20 bg-[#f5f5f5] text-[#5A626A] hover:bg-[#ebebeb]"
        >
          <ClipboardCopy className="mr-1.5 h-3.5 w-3.5" />
          Copy Link
        </Button>
        {showPublish && (
          <Button
            size="sm"
            className="rounded-md bg-[#5A626A] text-white hover:bg-[#4a5568]"
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
