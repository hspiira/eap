import { Calendar } from "lucide-react"

import { Panel, PanelEmpty, PanelList } from "@/components/common/Panel"
import { formatDay } from "@/lib/format"

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
            <UpcomingRow key={item.id} item={item} />
          ))}
        </PanelList>
      )}
    </Panel>
  )
}

function UpcomingRow({ item }: { item: ClientUpcomingItem }) {
  const meta = [formatDay(item.date), item.time, item.context].filter(Boolean).join(" · ")
  return (
    <li className="flex items-center gap-2.5 px-3 py-2.5">
      <Calendar className="size-4 shrink-0 text-fg-subtle" aria-hidden />
      <span className="flex min-w-0 flex-1 flex-wrap items-baseline gap-x-2">
        <span className="truncate text-sm font-medium text-fg">{item.title}</span>
        <span className="shrink-0 text-xs tabular-nums text-fg-muted">{meta}</span>
      </span>
      {item.link ? (
        <a href={item.link} className="shrink-0 text-xs font-medium text-primary hover:underline">
          {item.linkLabel ?? "View"}
        </a>
      ) : null}
    </li>
  )
}
