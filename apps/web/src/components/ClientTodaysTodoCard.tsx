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
  const day = d.getDate()
  const days = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]
  const weekDay = days[d.getDay()]
  return `${y}/${m} ${day} ${weekDay}`
}

export function ClientTodaysTodoCard({ items, className }: ClientTodaysTodoCardProps) {
  return (
    <div
      className={cn(
        "flex flex-col border border-ink/20 bg-white p-4 rounded-none",
        className
      )}
    >
      <div className="mb-3 flex items-center justify-between">
        <h3 className="text-sm font-semibold text-ink">Today's to-do</h3>
        <span className="text-xs text-ink/70">View all</span>
      </div>
      <div className="mb-3 flex items-center justify-between rounded-none border border-ink/30 bg-neutral-50 px-2 py-1">
        <button type="button" className="p-1 text-ink/70 hover:bg-ink/10" aria-label="Previous day">
          ←
        </button>
        <span className="text-xs text-ink">{formatTodayLabel()}</span>
        <button type="button" className="p-1 text-ink/70 hover:bg-ink/10" aria-label="Next day">
          →
        </button>
      </div>
      {items.length === 0 ? (
        <p className="text-sm text-ink/80">Nothing scheduled for today.</p>
      ) : (
        <ul className="space-y-2">
          {items.map((item) => (
            <li key={item.id} className="flex gap-2 text-sm text-ink">
              <span className="mt-1.5 h-1.5 w-1.5 shrink-0 rounded-none bg-ink" />
              <span className="min-w-0 flex-1">
                {item.link ? (
                  <a
                    href={item.link}
                    className="hover:text-natural hover:underline"
                  >
                    {(item.time ? `${item.time} ` : "") + item.title}
                  </a>
                ) : (
                  <span>{(item.time ? `${item.time} ` : "") + item.title}</span>
                )}
              </span>
              {item.link && item.linkLabel && (
                <a
                  href={item.link}
                  className="shrink-0 text-xs text-ink/70 hover:text-natural"
                >
                  {item.linkLabel}
                </a>
              )}
            </li>
          ))}
        </ul>
      )}
    </div>
  )
}
