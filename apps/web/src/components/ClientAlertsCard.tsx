import { useState } from "react"

import { AlertCircle, Bell, ChevronDown, ChevronUp } from "lucide-react"

import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"
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

const SEVERITY_VARIANT: Record<
  ClientAlertSeverity,
  "default" | "secondary" | "destructive" | "outline"
> = {
  low: "outline",
  medium: "secondary",
  high: "destructive",
  critical: "destructive",
}

const SEVERITY_ICON_TONE: Record<ClientAlertSeverity, string> = {
  low: "text-fg-subtle",
  medium: "text-warning",
  high: "text-danger",
  critical: "text-danger",
}

export function ClientAlertsCard({ alerts, className }: ClientAlertsCardProps) {
  const [expandedId, setExpandedId] = useState<string | null>(null)
  const hasAlerts = alerts.length > 0
  const hasUnacked = alerts.some(
    (a) => a.severity === "high" || a.severity === "critical",
  )

  return (
    <Card className={cn("rounded-md", className)}>
      <CardHeader className="flex-row items-center gap-2 space-y-0 border-b border-border p-3">
        <span className="relative" aria-hidden>
          <Bell className="size-4 text-fg-muted" />
          {hasUnacked ? (
            <span className="absolute right-0 top-0 size-1.5 -translate-y-0.5 translate-x-0.5 rounded-full bg-danger" />
          ) : null}
        </span>
        <CardTitle className="text-sm font-semibold text-fg">Alerts</CardTitle>
        {hasAlerts ? (
          <Badge variant="secondary" size="sm" className="font-mono tabular-nums">
            {alerts.length}
          </Badge>
        ) : null}
      </CardHeader>

      <CardContent className="p-0">
        {!hasAlerts ? (
          <div className="px-3 py-6 text-center text-sm text-fg-muted">
            No alerts for this client.
          </div>
        ) : (
          <ul className="max-h-70 divide-y divide-border overflow-y-auto">
            {alerts.map((a) => {
              const severity = a.severity ?? "medium"
              const isExpanded = expandedId === a.id
              const expandable = Boolean(a.description || a.link)
              return (
                <li key={a.id} className="p-3">
                  <div className="flex items-start gap-2">
                    <AlertCircle
                      className={cn(
                        "mt-0.5 size-4 shrink-0",
                        SEVERITY_ICON_TONE[severity],
                      )}
                      aria-hidden
                    />
                    <div className="min-w-0 flex-1">
                      <div className="flex flex-wrap items-start justify-between gap-2">
                        <span className="text-sm font-medium text-fg">
                          {a.title}
                        </span>
                        {expandable ? (
                          <Button
                            variant="ghost"
                            size="icon"
                            className="size-6"
                            aria-label={isExpanded ? "Collapse alert" : "Expand alert"}
                            aria-expanded={isExpanded}
                            onClick={() =>
                              setExpandedId(isExpanded ? null : a.id)
                            }
                          >
                            {isExpanded ? (
                              <ChevronUp className="size-3.5" />
                            ) : (
                              <ChevronDown className="size-3.5" />
                            )}
                          </Button>
                        ) : null}
                      </div>
                      <Badge
                        variant={SEVERITY_VARIANT[severity]}
                        size="sm"
                        className="mt-1"
                      >
                        {SEVERITY_LABEL[severity]}
                      </Badge>
                      {isExpanded && a.description ? (
                        <p className="mt-2 text-xs leading-relaxed text-fg-muted">
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
          </ul>
        )}
      </CardContent>
    </Card>
  )
}
