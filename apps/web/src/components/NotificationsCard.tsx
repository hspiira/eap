import { useState } from "react"

import { Bell, ChevronDown, ChevronUp, Eye, Trash2 } from "lucide-react"

import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"
import { cn } from "@/lib/utils"

type NotificationTone = "info" | "success" | "warning" | "danger"

export interface NotificationItem {
  id: string
  title: string
  tag?: { label: string; tone: NotificationTone } | null
  description?: string
  link?: { label: string; href: string }
}

interface NotificationsCardProps {
  notifications?: ReadonlyArray<NotificationItem>
  className?: string
}

const TAG_VARIANT: Record<NotificationTone, "default" | "secondary" | "destructive" | "outline"> = {
  info: "secondary",
  success: "secondary",
  warning: "secondary",
  danger: "destructive",
}

const TAG_TONE: Record<NotificationTone, string> = {
  info: "text-info",
  success: "text-success",
  warning: "text-warning",
  danger: "",
}

const DEFAULT_NOTIFICATIONS: ReadonlyArray<NotificationItem> = [
  {
    id: "n1",
    title: "Acme Holdings — contract renewal due",
    tag: { label: "Action needed", tone: "warning" },
    description:
      "Master service agreement expires in 14 days. Initiate renewal to avoid service interruption.",
    link: { label: "Open contract", href: "/contracts" },
  },
  {
    id: "n2",
    title: "Critical incident logged",
    tag: { label: "Critical", tone: "danger" },
    description:
      "Severity High incident reported 2026-05-08. Awaiting case-manager assignment.",
    link: { label: "Open incident", href: "/incidents" },
  },
  {
    id: "n3",
    title: "Survey response rate above target",
    tag: { label: "Healthy", tone: "success" },
  },
]

export function NotificationsCard({
  notifications = DEFAULT_NOTIFICATIONS,
  className,
}: NotificationsCardProps = {}) {
  const [expandedId, setExpandedId] = useState<string | null>(
    notifications[0]?.id ?? null,
  )

  return (
    <Card className={cn("rounded-md", className)} data-notifications-card>
      <CardHeader className="flex-row items-center justify-between gap-2 space-y-0 border-b border-border-subtle p-3">
        <div className="flex items-center gap-2">
          <Bell className="size-4 text-fg-muted" aria-hidden />
          <CardTitle className="text-sm font-semibold text-fg">
            Notifications
          </CardTitle>
          <Badge variant="secondary" size="sm" className="font-mono tabular-nums">
            {notifications.length}
          </Badge>
        </div>
        <Button variant="ghost" size="sm" className="-mr-2 h-7 px-2 text-xs text-fg-muted">
          Mark all read
        </Button>
      </CardHeader>
      <CardContent className="p-0">
        {notifications.length === 0 ? (
          <div className="px-3 py-6 text-center text-sm text-fg-muted">
            No notifications.
          </div>
        ) : (
          <ul className="max-h-100 divide-y divide-border-subtle overflow-y-auto">
            {notifications.map((n) => {
              const expanded = n.id === expandedId
              const expandable = Boolean(n.description || n.link)
              return (
                <li key={n.id} className="p-3">
                  <div className="flex items-start gap-2">
                    <div className="min-w-0 flex-1 grid gap-1">
                      <div className="flex flex-wrap items-center gap-2">
                        <span className="text-sm font-medium text-fg">
                          {n.title}
                        </span>
                        {n.tag ? (
                          <Badge
                            variant={TAG_VARIANT[n.tag.tone]}
                            size="sm"
                            className={cn(TAG_TONE[n.tag.tone])}
                          >
                            {n.tag.label}
                          </Badge>
                        ) : null}
                      </div>
                      {expanded && n.description ? (
                        <p className="text-xs leading-relaxed text-fg-muted">
                          {n.description}
                        </p>
                      ) : null}
                      {expanded && n.link ? (
                        <div className="flex items-center gap-2 pt-1">
                          <Button
                            asChild
                            variant="outline"
                            size="sm"
                            className="h-7 gap-1.5"
                          >
                            <a href={n.link.href}>
                              <Eye className="size-3" />
                              {n.link.label}
                            </a>
                          </Button>
                          <Button
                            variant="ghost"
                            size="sm"
                            className="h-7 gap-1.5 text-fg-muted"
                          >
                            <Trash2 className="size-3" />
                            Dismiss
                          </Button>
                        </div>
                      ) : null}
                    </div>
                    {expandable ? (
                      <Button
                        variant="ghost"
                        size="icon"
                        className="size-6"
                        aria-label={expanded ? "Collapse" : "Expand"}
                        aria-expanded={expanded}
                        onClick={() =>
                          setExpandedId(expanded ? null : n.id)
                        }
                      >
                        {expanded ? (
                          <ChevronUp className="size-3.5" />
                        ) : (
                          <ChevronDown className="size-3.5" />
                        )}
                      </Button>
                    ) : null}
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
