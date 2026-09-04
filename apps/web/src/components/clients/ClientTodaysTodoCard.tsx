import { CalendarCheck } from "lucide-react"

import { Panel } from "@/components/common/Panel"

export interface ClientTodaysTodoItem {
  id: string
  title: string
  time?: string | null
  link?: string
  linkLabel?: string
}

interface ClientTodaysTodoCardProps {
  items: ClientTodaysTodoItem[]
  className?: string
}

function formatTodayLabel() {
  const d = new Date()
  const y = d.getFullYear()
  const m = String(d.getMonth() + 1).padStart(2, "0")
  const day = String(d.getDate()).padStart(2, "0")
  const days = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]
  return `${y}-${m}-${day} · ${days[d.getDay()]}`
}

export function ClientTodaysTodoCard({ items, className }: ClientTodaysTodoCardProps) {
  return (
    <Panel
      icon={CalendarCheck}
      title="Today's to-do"
      count={items.length || null}
      className={className}
    >
      <div className="grid gap-3">
        <div className="flex h-7 items-center justify-center rounded-sm border border-fg/10 bg-bg">
          <span className="text-xs tabular-nums text-fg/65">{formatTodayLabel()}</span>
        </div>
        {items.length === 0 ? (
          <p className="text-sm text-fg/60">Nothing scheduled for today.</p>
        ) : (
          <ul className="grid gap-2">
            {items.map((item) => (
              <li key={item.id} className="flex items-baseline gap-3 text-sm text-fg">
                {item.time ? (
                  <span className="shrink-0 tabular-nums text-fg-subtle">{item.time}</span>
                ) : (
                  <span className="mt-1.5 size-1.5 shrink-0 rounded-full bg-fg/40" aria-hidden />
                )}
                <span className="min-w-0 flex-1">
                  {item.link ? (
                    <a href={item.link} className="hover:text-primary hover:underline">
                      {item.title}
                    </a>
                  ) : (
                    item.title
                  )}
                </span>
                {item.link && item.linkLabel ? (
                  <a href={item.link} className="shrink-0 text-xs text-fg-muted hover:text-primary">
                    {item.linkLabel}
                  </a>
                ) : null}
              </li>
            ))}
          </ul>
        )}
      </div>
    </Panel>
  )
}
