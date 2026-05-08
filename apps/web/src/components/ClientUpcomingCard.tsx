import { Calendar, Clock, MapPin } from "lucide-react"

import { cn } from "@/lib/utils"

export interface ClientUpcomingItem {
  id: string
  title: string
  date: string
  time?: string | null
  context?: string | null
  link?: string
  linkLabel?: string
}

interface ClientUpcomingCardProps {
  items: ClientUpcomingItem[]
  className?: string
}

export function ClientUpcomingCard({ items, className }: ClientUpcomingCardProps) {
  if (items.length === 0) {
    return (
      <div
        className={cn(
          "flex flex-col border border-ink/30 rounded-none bg-neutral-50 overflow-hidden",
          className
        )}
      >
        <div className="border-b border-ink/20 px-4 py-3 bg-warm/20">
          <h3 className="text-sm font-semibold text-ink">Upcoming</h3>
        </div>
        <div className="px-4 py-4 text-sm text-ink/80">No upcoming events or deadlines.</div>
      </div>
    )
  }

  return (
    <div
      className={cn(
        "flex flex-col border border-ink/30 rounded-none bg-neutral-50 overflow-hidden",
        className
      )}
    >
      <div className="border-b border-ink/20 px-4 py-3 bg-warm/20">
        <h3 className="text-sm font-semibold text-ink">Upcoming</h3>
      </div>
      <div className="flex flex-col divide-y divide-ink/15 max-h-[280px] overflow-y-auto">
        {items.map((item) => (
          <div key={item.id} className="px-4 py-3">
            <div className="flex flex-wrap items-start justify-between gap-2">
              <div className="min-w-0 flex-1 space-y-1">
                <h4 className="text-sm font-medium text-ink">{item.title}</h4>
                <div className="flex flex-wrap items-center gap-x-3 gap-y-1 text-xs text-ink/70">
                  <span className="flex items-center gap-1">
                    <Calendar className="h-3 w-3 shrink-0" />
                    {item.date}
                  </span>
                  {item.time && (
                    <span className="flex items-center gap-1">
                      <Clock className="h-3 w-3 shrink-0" />
                      {item.time}
                    </span>
                  )}
                </div>
                {item.context && (
                  <div className="flex items-center gap-1 text-xs text-ink/70">
                    <MapPin className="h-3 w-3 shrink-0" />
                    <span>{item.context}</span>
                  </div>
                )}
              </div>
              {item.link && (
                <a
                  href={item.link}
                  className="shrink-0 text-xs font-medium text-natural hover:underline"
                >
                  {item.linkLabel ?? "View"}
                </a>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}
