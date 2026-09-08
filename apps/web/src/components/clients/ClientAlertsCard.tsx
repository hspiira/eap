import { useState } from "react"

import { AlertCircle, Bell, ChevronDown, ChevronUp } from "lucide-react"

import { Panel, PanelEmpty, PanelList } from "@/components/common/Panel"
import { Button } from "@/components/ui/button"
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

const SEVERITY_TONE: Record<ClientAlertSeverity, { icon: string; pill: string }> = {
  low: {
    icon: "text-fg-subtle",
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
  const hasUnacked = alerts.some((a) => a.severity === "high" || a.severity === "critical")

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
          {alerts.map((a) => (
            <AlertRow
              key={a.id}
              alert={a}
              isExpanded={expandedId === a.id}
              onToggle={() => setExpandedId(expandedId === a.id ? null : a.id)}
            />
          ))}
        </PanelList>
      )}
    </Panel>
  )
}

function AlertRow({
  alert,
  isExpanded,
  onToggle,
}: {
  alert: ClientAlert
  isExpanded: boolean
  onToggle: () => void
}) {
  const severity = alert.severity ?? "medium"
  const tone = SEVERITY_TONE[severity]
  const expandable = Boolean(alert.description || alert.link)

  return (
    <li>
      {expandable ? (
        <Button
          type="button"
          variant="ghost"
          onClick={onToggle}
          aria-expanded={isExpanded}
          aria-label={isExpanded ? `Collapse ${alert.title}` : `Expand ${alert.title}`}
          className="h-auto w-full justify-start gap-2.5 rounded-none px-3 py-2.5 text-left font-normal hover:bg-surface-hover"
        >
          <AlertRowHeader alert={alert} tone={tone} severity={severity} />
          {isExpanded ? (
            <ChevronUp className="size-3.5 shrink-0 text-fg-muted" aria-hidden />
          ) : (
            <ChevronDown className="size-3.5 shrink-0 text-fg-muted" aria-hidden />
          )}
        </Button>
      ) : (
        <div className="flex items-center gap-2.5 px-3 py-2.5">
          <AlertRowHeader alert={alert} tone={tone} severity={severity} />
        </div>
      )}
      {isExpanded && expandable ? (
        <div className="space-y-1.5 py-2.5 pl-[2.375rem] pr-3">
          {alert.description ? (
            <p className="text-xs leading-relaxed text-fg/65">{alert.description}</p>
          ) : null}
          {alert.link ? (
            <a
              href={alert.link}
              className="inline-block text-xs font-medium text-primary hover:underline"
            >
              {alert.linkLabel ?? "View"}
            </a>
          ) : null}
        </div>
      ) : null}
    </li>
  )
}

function AlertRowHeader({
  alert,
  tone,
  severity,
}: {
  alert: ClientAlert
  tone: { icon: string; pill: string }
  severity: ClientAlertSeverity
}) {
  return (
    <>
      <AlertCircle className={cn("size-4 shrink-0", tone.icon)} aria-hidden />
      <span className="min-w-0 flex-1 truncate text-sm font-medium text-fg">{alert.title}</span>
      <span className={cn("shrink-0 rounded-sm px-1.5 py-0.5 text-[11px] font-medium", tone.pill)}>
        {SEVERITY_LABEL[severity]}
      </span>
    </>
  )
}
