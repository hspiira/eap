import { useState } from "react"
import { Bell, ChevronDown, ChevronUp, AlertCircle } from "lucide-react"
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
          "flex flex-col border border-[#5A626A]/30 rounded-none bg-[#fafafa] overflow-hidden",
          className
        )}
      >
        <div className="flex items-center gap-2 border-b border-[#5A626A]/20 px-4 py-3 bg-[#E6E0D7]/20">
          <Bell className="h-4 w-4 text-[#5A626A]" />
          <h3 className="text-sm font-semibold text-[#5A626A]">Alerts</h3>
        </div>
        <div className="px-4 py-4 text-sm text-[#5A626A]/80">No alerts for this client.</div>
      </div>
    )
  }

  return (
    <div
      className={cn(
        "flex flex-col border border-[#5A626A]/30 rounded-none bg-[#fafafa] overflow-hidden",
        className
      )}
    >
      <div className="flex items-center gap-2 border-b border-[#5A626A]/20 px-4 py-3 bg-[#E6E0D7]/20">
        <div className="relative">
          <Bell className="h-4 w-4 text-[#5A626A]" />
          <span className="absolute -right-0.5 -top-0.5 h-2 w-2 rounded-full bg-[#D0B5B3]" aria-hidden />
        </div>
        <h3 className="text-sm font-semibold text-[#5A626A]">Alerts</h3>
        <span className="flex h-5 min-w-[20px] items-center justify-center bg-[#5A626A]/15 px-1.5 text-xs font-medium text-[#5A626A] rounded-none">
          {alerts.length}
        </span>
      </div>
      <div className="flex max-h-[280px] flex-col overflow-y-auto">
        {alerts.map((a) => {
          const isExpanded = expandedId === a.id
          return (
            <div
              key={a.id}
              className="border-b border-[#5A626A]/15 px-4 py-3 last:border-b-0"
            >
              <div className="flex items-start gap-2">
                <AlertCircle className="mt-0.5 h-4 w-4 shrink-0 text-[#5A626A]/70" />
                <div className="min-w-0 flex-1">
                  <div className="flex flex-wrap items-center justify-between gap-2">
                    <span className="text-sm font-medium text-[#5A626A]">{a.title}</span>
                    <button
                      type="button"
                      className="p-1 text-[#5A626A]/60 hover:bg-[#E6E0D7] hover:text-[#5A626A] rounded-none"
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
                      a.severity === "high" && "bg-[#D0B5B3]/30 text-[#5A626A]",
                      a.severity !== "high" && "bg-[#E6E0D7]/50 text-[#5A626A]/90"
                    )}
                  >
                    {a.severity === "high" ? "High" : "Medium"}
                  </span>
                  {isExpanded && a.description && (
                    <p className="mt-2 text-xs leading-relaxed text-[#5A626A]/90">{a.description}</p>
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
