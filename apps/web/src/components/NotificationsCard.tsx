import { Bell, Car, ChevronDown, ChevronUp, Eye, Trash2, X } from "lucide-react"

import { Button } from "@/components/ui/button"
import { cn } from "@/lib/utils"

const notifications = [
  {
    id: "1",
    vehicle: "Captiva 01 121 PHA",
    tag: "Speeding",
    tagVariant: "red",
    expanded: true,
    description:
      "Captiva 01 121 PHA violated the speed limit. On September 20, 2024, at 18:43:33, it was traveling at 76 km/h near 'E39, Samarkand, Samarkand Region, Uzbekistan'.",
    link: "Register an event",
  },
  {
    id: "2",
    vehicle: "Howo Авт 01 054 JKA",
    tag: "Exited the geofence",
    tagVariant: "orange",
    expanded: false,
    description: null,
    link: null,
  },
]

export function NotificationsCard() {
  return (
    <div
      data-notifications-card
      className={cn(
        "flex flex-col rounded-lg border border-border/25 bg-white",
        "shadow-[0_1px_4px_rgba(0,0,0,0.06)]"
      )}
    >
      <div className="flex items-center justify-between border-b border-border/20 px-4 py-3">
        <div className="flex items-center gap-2">
          <div className="relative">
            <Bell className="h-4 w-4 text-ink" />
            <span className="absolute -right-0.5 -top-0.5 h-2 w-2 rounded-full bg-stone" aria-hidden />
          </div>
          <h3 className="text-sm font-semibold text-ink">Notifications</h3>
        </div>
        <button
          type="button"
          className="p-1 text-ink/70 hover:bg-surface-tile hover:text-ink"
          aria-label="Close"
        >
          <X className="h-4 w-4" />
        </button>
      </div>
      <div className="flex max-h-[420px] flex-col overflow-hidden">
        <div className="flex-1 overflow-y-auto">
          {notifications.map((n) => (
            <div
              key={n.id}
              className="border-b border-border/15 px-4 py-3 last:border-b-0"
            >
              <div className="flex items-start gap-2">
                <Car className="mt-0.5 h-4 w-4 shrink-0 text-ink/70" />
                <div className="min-w-0 flex-1">
                  <div className="flex flex-wrap items-center justify-between gap-2">
                    <div className="flex items-center gap-1.5">
                      <span className="text-sm font-medium text-ink">{n.vehicle}</span>
                      {n.id === "1" && (
                        <span className="h-1.5 w-1.5 shrink-0 rounded-full bg-stone" aria-hidden />
                      )}
                    </div>
                    <div className="flex items-center gap-1">
                      <button type="button" className="p-1 text-ink/60 hover:text-ink" aria-label="Mark read">
                        <Eye className="h-3.5 w-3.5" />
                      </button>
                      <button type="button" className="p-1 text-ink/60 hover:text-ink" aria-label="Delete">
                        <Trash2 className="h-3.5 w-3.5" />
                      </button>
                      <button type="button" className="p-1 text-ink/60 hover:text-ink" aria-label="Expand">
                        {n.expanded ? <ChevronUp className="h-3.5 w-3.5" /> : <ChevronDown className="h-3.5 w-3.5" />}
                      </button>
                    </div>
                  </div>
                  <span
                    className={cn(
                      "mt-1 inline-block rounded px-2 py-0.5 text-xs font-medium",
                      n.tagVariant === "red" && "bg-stone/15 text-stone",
                      n.tagVariant === "orange" && "bg-danger-soft/30 text-accent-amber-ink"
                    )}
                  >
                    {n.tag}
                  </span>
                  {n.expanded && n.description && (
                    <p className="mt-2 text-xs leading-relaxed text-ink/90">
                      {n.description}
                    </p>
                  )}
                  {n.expanded && n.link && (
                    <button
                      type="button"
                      className="mt-2 text-xs font-medium text-natural hover:underline"
                    >
                      {n.link}
                    </button>
                  )}
                </div>
              </div>
            </div>
          ))}
        </div>
        <div className="grid grid-cols-2 gap-2 border-t border-border/20 p-3">
          <div className="flex justify-start bg-neutral-50 px-3 py-2">
            <Button variant="ghost" size="sm" className="rounded-md text-xs text-ink">
              Delete all
            </Button>
          </div>
          <div className="flex justify-start bg-neutral-50 px-3 py-2">
            <Button variant="ghost" size="sm" className="rounded-md text-xs text-ink">
              Delete read messages
            </Button>
          </div>
        </div>
      </div>
    </div>
  )
}
