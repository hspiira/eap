import { useState } from "react"

import { AlertCircle, Bell, ChevronDown, ChevronUp } from "lucide-react"

import { Panel, PanelEmpty, PanelList } from "@/components/common/Panel"
import { cn } from "@/lib/utils"

export type ClientAlertSeverity = "low" | "medium" | "high" | "critical"

export interface ClientAlert {
  id: string
  title: string
  description?: string | null
  severity?: ClientAlertSeverity
  link?: string
  linkLabel?: string
}

interface ClientAlertsCardProps {
  alerts: ClientAlert[]
  className?: string
}

const SEVERITY_LABEL: Record<ClientAlertSeverity, string> = {
  low: "Low",
  medium: "Medium",
  high: "High",
  critical: "Critical",
}

const SEVERITY_TONE: Record<
  ClientAlertSeverity,
  { icon: string; pill: string }
> = {
  low: {
    icon: "text-fg/45",
    pill: "border border-fg/15 text-fg/70",
  },
  medium: {
    icon: "text-warning",
    pill: "border border-warning/30 bg-warning-soft text-warning-fg",
  },
  high: {
    icon: "text-danger",
    pill: "border border-danger/30 bg-danger-soft text-danger-fg",
  },
  critical: {
    icon: "text-danger",
    pill: "border border-danger/40 bg-danger-soft text-danger-fg",
  },
}

export function ClientAlertsCard({ alerts, className }: ClientAlertsCardProps) {
  const [expandedId, setExpandedId] = useState<string | null>(null)
  const hasAlerts = alerts.length > 0
  const hasUnacked = alerts.some(
    (a) => a.severity === "high" || a.severity === "critical",
  )

  return (
    <Panel
      icon={Bell}
      title="Alerts"
      count={hasAlerts ? alerts.length : null}
      badge={
        hasUnacked ? (
          <span
            aria-hidden
            className="size-1.5 rounded-full bg-danger"
            title="Unread high-priority alerts"
          />
        ) : null
      }
      className={className}
      bodyClassName="p-0"
    >
      {!hasAlerts ? (
        <PanelEmpty>No alerts for this client.</PanelEmpty>
      ) : (
        <PanelList className="max-h-72 overflow-y-auto">
          {alerts.map((a) => {
            const severity = a.severity ?? "medium"
            const isExpanded = expandedId === a.id
            const expandable = Boolean(a.description || a.link)
            const tone = SEVERITY_TONE[severity]
            return (
              <li key={a.id} className="px-3 py-2.5">
                <div className="flex items-start gap-2">
                  <AlertCircle
                    className={cn("mt-0.5 size-4 shrink-0", tone.icon)}
                    aria-hidden
                  />
                  <div className="min-w-0 flex-1">
                    <div className="flex flex-wrap items-start justify-between gap-2">
                      <span className="text-sm font-medium text-fg">
                        {a.title}
                      </span>
                      {expandable ? (
                        <button
                          type="button"
                          aria-label={isExpanded ? "Collapse alert" : "Expand alert"}
                          aria-expanded={isExpanded}
                          onClick={() =>
                            setExpandedId(isExpanded ? null : a.id)
                          }
                          className="grid size-6 place-items-center rounded-sm text-fg/55 transition-colors hover:bg-surface-hover hover:text-fg"
                        >
                          {isExpanded ? (
                            <ChevronUp className="size-3.5" />
                          ) : (
                            <ChevronDown className="size-3.5" />
                          )}
                        </button>
                      ) : null}
                    </div>
                    <span
                      className={cn(
                        "mt-1 inline-flex items-center rounded-sm px-1.5 py-0.5 text-[11px] font-medium",
                        tone.pill,
                      )}
                    >
                      {SEVERITY_LABEL[severity]}
                    </span>
                    {isExpanded && a.description ? (
                      <p className="mt-2 text-xs leading-relaxed text-fg/65">
                        {a.description}
                      </p>
                    ) : null}
                    {isExpanded && a.link ? (
                      <a
                        href={a.link}
                        className="mt-2 inline-block text-xs font-medium text-primary hover:underline"
                      >
                        {a.linkLabel ?? "View"}
                      </a>
                    ) : null}
                  </div>
                </div>
              </li>
            )
          })}
        </PanelList>
      )}
    </Panel>
  )
}
