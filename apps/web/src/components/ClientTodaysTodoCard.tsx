import { ChevronLeft, ChevronRight } from "lucide-react"

import { Button } from "@/components/ui/button"
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"
import { cn } from "@/lib/utils"

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
    <Card className={cn("rounded-md", className)}>
      <CardHeader className="flex-row items-center justify-between gap-2 space-y-0 border-b border-border-subtle p-3">
        <CardTitle className="text-sm font-semibold text-fg">
          Today's to-do
        </CardTitle>
        <Button
          variant="ghost"
          size="sm"
          className="-mr-2 h-7 px-2 text-xs text-fg-muted"
        >
          View all
        </Button>
      </CardHeader>
      <CardContent className="grid gap-3 p-3">
        <div className="flex items-center justify-between rounded-sm border border-border-subtle bg-surface px-2 py-1">
          <Button variant="ghost" size="icon" className="size-6" aria-label="Previous day">
            <ChevronLeft className="size-3.5" />
          </Button>
          <span className="font-mono text-xs tabular-nums text-fg-muted">
            {formatTodayLabel()}
          </span>
          <Button variant="ghost" size="icon" className="size-6" aria-label="Next day">
            <ChevronRight className="size-3.5" />
          </Button>
        </div>
        {items.length === 0 ? (
          <p className="text-sm text-fg-muted">Nothing scheduled for today.</p>
        ) : (
          <ul className="grid gap-2">
            {items.map((item) => (
              <li
                key={item.id}
                className="flex items-baseline gap-3 text-sm text-fg"
              >
                {item.time ? (
                  <span className="font-mono shrink-0 tabular-nums text-fg-subtle">
                    {item.time}
                  </span>
                ) : (
                  <span
                    className="mt-1 size-1.5 shrink-0 rounded-full bg-fg-muted"
                    aria-hidden
                  />
                )}
                <span className="min-w-0 flex-1">
                  {item.link ? (
                    <a
                      href={item.link}
                      className="hover:text-primary hover:underline"
                    >
                      {item.title}
                    </a>
                  ) : (
                    item.title
                  )}
                </span>
                {item.link && item.linkLabel ? (
                  <a
                    href={item.link}
                    className="shrink-0 text-xs text-fg-muted hover:text-primary"
                  >
                    {item.linkLabel}
                  </a>
                ) : null}
              </li>
            ))}
          </ul>
        )}
      </CardContent>
    </Card>
  )
}
