import { Calendar, Clock, MapPin } from "lucide-react"

import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"
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

export function ClientUpcomingCard({
  items,
  className,
}: ClientUpcomingCardProps) {
  return (
    <Card className={cn("rounded-md", className)}>
      <CardHeader className="border-b border-border-subtle p-3">
        <CardTitle className="text-sm font-semibold text-fg">Upcoming</CardTitle>
      </CardHeader>
      <CardContent className="p-0">
        {items.length === 0 ? (
          <div className="px-3 py-6 text-center text-sm text-fg-muted">
            No upcoming events or deadlines.
          </div>
        ) : (
          <ul className="max-h-70 divide-y divide-border-subtle overflow-y-auto">
            {items.map((item) => (
              <li key={item.id} className="p-3">
                <div className="flex flex-wrap items-start justify-between gap-2">
                  <div className="min-w-0 flex-1 grid gap-1">
                    <h4 className="text-sm font-medium text-fg">{item.title}</h4>
                    <div className="flex flex-wrap items-center gap-x-3 gap-y-1 text-xs text-fg-muted">
                      <span className="flex items-center gap-1">
                        <Calendar className="size-3 shrink-0" aria-hidden />
                        <span className="font-mono tabular-nums">
                          {item.date}
                        </span>
                      </span>
                      {item.time ? (
                        <span className="flex items-center gap-1">
                          <Clock className="size-3 shrink-0" aria-hidden />
                          <span className="font-mono tabular-nums">
                            {item.time}
                          </span>
                        </span>
                      ) : null}
                    </div>
                    {item.context ? (
                      <div className="flex items-center gap-1 text-xs text-fg-muted">
                        <MapPin className="size-3 shrink-0" aria-hidden />
                        <span>{item.context}</span>
                      </div>
                    ) : null}
                  </div>
                  {item.link ? (
                    <a
                      href={item.link}
                      className="shrink-0 text-xs font-medium text-primary hover:underline"
                    >
                      {item.linkLabel ?? "View"}
                    </a>
                  ) : null}
                </div>
              </li>
            ))}
          </ul>
        )}
      </CardContent>
    </Card>
  )
}
