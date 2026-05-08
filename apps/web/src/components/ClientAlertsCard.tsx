import { useState } from "react"

import { AlertCircle, Bell, ChevronDown, ChevronUp } from "lucide-react"

import { cn } from "@/lib/utils"

export interface ClientAlert {
  id: string
  title: string
  description?: string | null
  severity?: "high" | "medium"
  link?: string
  linkLabel?: string
}

interface ClientAlertsCardProps {
  alerts: ClientAlert[]
  className?: string
}

export function ClientAlertsCard({ alerts, className }: ClientAlertsCardProps) {
  const [expandedId, setExpandedId] = useState<string | null>(null)

  if (alerts.length === 0) {
    return (
      <div
        className={cn(
          "flex flex-col border border-ink/30 rounded-none bg-neutral-50 overflow-hidden",
          className
        )}
      >
        <div className="flex items-center gap-2 border-b border-ink/20 px-4 py-3 bg-warm/20">
          <Bell className="h-4 w-4 text-ink" />
          <h3 className="text-sm font-semibold text-ink">Alerts</h3>
        </div>
        <div className="px-4 py-4 text-sm text-ink/80">No alerts for this client.</div>
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
      <div className="flex items-center gap-2 border-b border-ink/20 px-4 py-3 bg-warm/20">
        <div className="relative">
          <Bell className="h-4 w-4 text-ink" />
          <span className="absolute -right-0.5 -top-0.5 h-2 w-2 rounded-full bg-danger-soft" aria-hidden />
        </div>
        <h3 className="text-sm font-semibold text-ink">Alerts</h3>
        <span className="flex h-5 min-w-[20px] items-center justify-center bg-ink/15 px-1.5 text-xs font-medium text-ink rounded-none">
          {alerts.length}
        </span>
      </div>
      <div className="flex max-h-[280px] flex-col overflow-y-auto">
        {alerts.map((a) => {
          const isExpanded = expandedId === a.id
          return (
            <div
              key={a.id}
              className="border-b border-ink/15 px-4 py-3 last:border-b-0"
            >
              <div className="flex items-start gap-2">
                <AlertCircle className="mt-0.5 h-4 w-4 shrink-0 text-ink/70" />
                <div className="min-w-0 flex-1">
                  <div className="flex flex-wrap items-center justify-between gap-2">
                    <span className="text-sm font-medium text-ink">{a.title}</span>
                    <button
                      type="button"
                      className="p-1 text-ink/60 hover:bg-warm hover:text-ink rounded-none"
                      aria-label={isExpanded ? "Collapse" : "Expand"}
                      onClick={() => setExpandedId(isExpanded ? null : a.id)}
                    >
                      {isExpanded ? (
                        <ChevronUp className="h-3.5 w-3.5" />
                      ) : (
                        <ChevronDown className="h-3.5 w-3.5" />
                      )}
                    </button>
                  </div>
                  <span
                    className={cn(
                      "mt-1 inline-block px-2 py-0.5 text-xs font-medium rounded-none",
                      a.severity === "high" && "bg-danger-soft/30 text-ink",
                      a.severity !== "high" && "bg-warm/50 text-ink/90"
                    )}
                  >
                    {a.severity === "high" ? "High" : "Medium"}
                  </span>
                  {isExpanded && a.description && (
                    <p className="mt-2 text-xs leading-relaxed text-ink/90">{a.description}</p>
                  )}
                  {isExpanded && a.link && (
                    <a
                      href={a.link}
                      className="mt-2 inline-block text-xs font-medium text-natural hover:underline"
                    >
                      {a.linkLabel ?? "View"}
                    </a>
                  )}
                </div>
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}
