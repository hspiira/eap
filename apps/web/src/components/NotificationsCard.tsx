import { Bell, X, Eye, Trash2, ChevronDown, ChevronUp, Car } from "lucide-react"
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
        "flex flex-col rounded-lg border border-[#bfc4c9]/25 bg-white",
        "shadow-[0_1px_4px_rgba(0,0,0,0.06)]"
      )}
    >
      <div className="flex items-center justify-between border-b border-[#bfc4c9]/20 px-4 py-3">
        <div className="flex items-center gap-2">
          <div className="relative">
            <Bell className="h-4 w-4 text-[#5A626A]" />
            <span className="absolute -right-0.5 -top-0.5 h-2 w-2 rounded-full bg-[#b85c4a]" aria-hidden />
          </div>
          <h3 className="text-sm font-semibold text-[#5A626A]">Notifications</h3>
        </div>
        <button
          type="button"
          className="p-1 text-[#5A626A]/70 hover:bg-[#f0f0f0] hover:text-[#5A626A]"
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
              className="border-b border-[#bfc4c9]/15 px-4 py-3 last:border-b-0"
            >
              <div className="flex items-start gap-2">
                <Car className="mt-0.5 h-4 w-4 shrink-0 text-[#5A626A]/70" />
                <div className="min-w-0 flex-1">
                  <div className="flex flex-wrap items-center justify-between gap-2">
                    <div className="flex items-center gap-1.5">
                      <span className="text-sm font-medium text-[#5A626A]">{n.vehicle}</span>
                      {n.id === "1" && (
                        <span className="h-1.5 w-1.5 shrink-0 rounded-full bg-[#b85c4a]" aria-hidden />
                      )}
                    </div>
                    <div className="flex items-center gap-1">
                      <button type="button" className="p-1 text-[#5A626A]/60 hover:text-[#5A626A]" aria-label="Mark read">
                        <Eye className="h-3.5 w-3.5" />
                      </button>
                      <button type="button" className="p-1 text-[#5A626A]/60 hover:text-[#5A626A]" aria-label="Delete">
                        <Trash2 className="h-3.5 w-3.5" />
                      </button>
                      <button type="button" className="p-1 text-[#5A626A]/60 hover:text-[#5A626A]" aria-label="Expand">
                        {n.expanded ? <ChevronUp className="h-3.5 w-3.5" /> : <ChevronDown className="h-3.5 w-3.5" />}
                      </button>
                    </div>
                  </div>
                  <span
                    className={cn(
                      "mt-1 inline-block rounded px-2 py-0.5 text-xs font-medium",
                      n.tagVariant === "red" && "bg-[#b85c4a]/15 text-[#b85c4a]",
                      n.tagVariant === "orange" && "bg-[#D0B5B3]/30 text-[#8B6914]"
                    )}
                  >
                    {n.tag}
                  </span>
                  {n.expanded && n.description && (
                    <p className="mt-2 text-xs leading-relaxed text-[#5A626A]/90">
                      {n.description}
                    </p>
                  )}
                  {n.expanded && n.link && (
                    <button
                      type="button"
                      className="mt-2 text-xs font-medium text-[#8BA88B] hover:underline"
                    >
                      {n.link}
                    </button>
                  )}
                </div>
              </div>
            </div>
          ))}
        </div>
        <div className="grid grid-cols-2 gap-2 border-t border-[#bfc4c9]/20 p-3">
          <div className="flex justify-start bg-[#f5f5f5] px-3 py-2">
            <Button variant="ghost" size="sm" className="rounded-md text-xs text-[#5A626A]">
              Delete all
            </Button>
          </div>
          <div className="flex justify-start bg-[#f5f5f5] px-3 py-2">
            <Button variant="ghost" size="sm" className="rounded-md text-xs text-[#5A626A]">
              Delete read messages
            </Button>
          </div>
        </div>
      </div>
    </div>
  )
}
