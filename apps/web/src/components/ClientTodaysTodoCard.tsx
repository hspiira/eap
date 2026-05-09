import { CalendarCheck, ChevronLeft, ChevronRight } from "lucide-react"

import { Panel } from "@/components/common/Panel"
import { Button } from "@/components/ui/button"

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

export function ClientTodaysTodoCard({
  items,
  className,
}: ClientTodaysTodoCardProps) {
  return (
    <Panel
      icon={CalendarCheck}
      title="Today's to-do"
      count={items.length || null}
      action={
        <Button variant="ghost" size="sm" className="-mr-1 h-7 px-2 text-xs text-fg/60">
          View all
        </Button>
      }
      className={className}
    >
      <div className="grid gap-3">
        <div className="flex h-7 items-center justify-between rounded-sm border border-fg/10 bg-bg px-1">
          <button
            type="button"
            aria-label="Previous day"
            className="grid size-5 place-items-center rounded-sm text-fg/55 transition-colors hover:bg-surface-hover hover:text-fg"
          >
            <ChevronLeft className="size-3.5" />
          </button>
          <span className="font-mono text-xs tabular-nums text-fg/65">
            {formatTodayLabel()}
          </span>
          <button
            type="button"
            aria-label="Next day"
            className="grid size-5 place-items-center rounded-sm text-fg/55 transition-colors hover:bg-surface-hover hover:text-fg"
          >
            <ChevronRight className="size-3.5" />
          </button>
        </div>
        {items.length === 0 ? (
          <p className="text-sm text-fg/60">Nothing scheduled for today.</p>
        ) : (
          <ul className="grid gap-2">
            {items.map((item) => (
              <li key={item.id} className="flex items-baseline gap-3 text-sm text-fg">
                {item.time ? (
                  <span className="shrink-0 font-mono tabular-nums text-fg/45">
                    {item.time}
                  </span>
                ) : (
                  <span
                    className="mt-1.5 size-1.5 shrink-0 rounded-full bg-fg/40"
                    aria-hidden
                  />
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
                  <a
                    href={item.link}
                    className="shrink-0 text-xs text-fg/55 hover:text-primary"
                  >
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
