import { Calendar, Clock, MapPin } from "lucide-react"

import { Panel, PanelEmpty, PanelList } from "@/components/common/Panel"

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
    <Panel
      icon={Calendar}
      title="Upcoming"
      count={items.length || null}
      className={className}
      bodyClassName="p-0"
    >
      {items.length === 0 ? (
        <PanelEmpty>No upcoming events or deadlines.</PanelEmpty>
      ) : (
        <PanelList className="max-h-72 overflow-y-auto">
          {items.map((item) => (
            <li key={item.id} className="px-3 py-2.5">
              <div className="flex flex-wrap items-start justify-between gap-2">
                <div className="grid min-w-0 flex-1 gap-1">
                  <h4 className="text-sm font-medium text-fg">{item.title}</h4>
                  <div className="flex flex-wrap items-center gap-x-3 gap-y-1 text-xs text-fg/60">
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
                    <div className="flex items-center gap-1 text-xs text-fg/55">
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
        </PanelList>
      )}
    </Panel>
  )
}
