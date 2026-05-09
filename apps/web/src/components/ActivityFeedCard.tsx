import { useQuery } from "@tanstack/react-query"
import {
  AlertTriangle,
  CalendarClock,
  CheckCircle2,
  FileSignature,
  MessageSquare,
  Settings,
} from "lucide-react"

import { auditApi } from "@/api/endpoints/audit"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"
import { Skeleton } from "@/components/ui/skeleton"
import { formatRelativeTime } from "@/lib/dashboard"
import { entityListKey } from "@/lib/queries"
import { cn } from "@/lib/utils"
import type { AuditLog } from "@/types/entities"

type ActivityTone = "info" | "success" | "warning" | "danger"

export interface Activity {
  id: string
  icon: React.ElementType
  tone: ActivityTone
  title: string
  description: string
  time: string
  badge?: { label: string; variant?: "default" | "secondary" | "destructive" | "outline" }
  actions?: React.ReactNode
}

interface ActivityFeedCardProps {
  /** Override the live feed with explicit activities (for the gallery, demos). */
  activities?: ReadonlyArray<Activity>
  /** Number of audit-log entries to fetch when activities are not provided. */
  limit?: number
}

const TABS = ["All", "Sessions", "Cases", "Contracts"] as const

const TONE_RING: Record<ActivityTone, string> = {
  info: "bg-info-soft text-info ring-info/20",
  success: "bg-success-soft text-success ring-success/20",
  warning: "bg-warning-soft text-warning ring-warning/20",
  danger: "bg-danger-soft text-danger ring-danger/20",
}

export function ActivityFeedCard({
  activities,
  limit = 6,
}: ActivityFeedCardProps = {}) {
  const params = { page: 1, limit }
  const { data, isLoading, isError } = useQuery({
    queryKey: entityListKey("audit", params),
    queryFn: () => auditApi.list(params),
    staleTime: 30_000,
    enabled: activities === undefined,
  })

  const live = data?.items ? data.items.map(auditLogToActivity) : []
  const items = activities ?? live

  return (
    <Card className="rounded-md">
      <CardHeader className="flex-row items-center justify-between gap-2 space-y-0 border-b border-border p-3">
        <div className="flex items-center gap-2">
          <CardTitle className="text-sm font-semibold text-fg">
            Activity feed
          </CardTitle>
          <Badge variant="secondary" size="sm" className="font-mono tabular-nums">
            {activities === undefined && isLoading ? "…" : items.length}
          </Badge>
        </div>
        <Button
          variant="ghost"
          size="icon"
          aria-label="Activity feed settings"
          className="size-8"
        >
          <Settings className="size-4" />
        </Button>
      </CardHeader>

      <div
        role="tablist"
        aria-label="Activity filters"
        className="flex border-b border-border"
      >
        {TABS.map((tab, i) => {
          const active = i === 0
          return (
            <button
              key={tab}
              type="button"
              role="tab"
              aria-selected={active}
              className={cn(
                "border-b-2 px-3 py-2 text-sm font-medium transition-colors",
                active
                  ? "border-primary text-fg"
                  : "border-transparent text-fg-muted hover:text-fg",
              )}
            >
              {tab}
            </button>
          )
        })}
      </div>

      <CardContent className="p-0">
        {activities === undefined && isLoading ? (
          <ActivitySkeletonList count={3} />
        ) : activities === undefined && isError ? (
          <ActivityErrorState />
        ) : items.length === 0 ? (
          <ActivityEmptyState />
        ) : (
          <ol className="divide-y divide-border">
            {items.map((a) => (
              <ActivityRow key={a.id} activity={a} />
            ))}
          </ol>
        )}
      </CardContent>
    </Card>
  )
}

function ActivityRow({ activity: a }: { activity: Activity }) {
  return (
    <li className="flex gap-3 p-3">
      <span
        className={cn(
          "flex size-9 shrink-0 items-center justify-center rounded-md ring-1",
          TONE_RING[a.tone],
        )}
        aria-hidden
      >
        <a.icon className="size-4" />
      </span>
      <div className="min-w-0 flex-1">
        <div className="flex flex-wrap items-center gap-2">
          <span className="text-sm font-medium text-fg">{a.title}</span>
          {a.badge ? (
            <Badge variant={a.badge.variant ?? "secondary"} size="sm">
              {a.badge.label}
            </Badge>
          ) : null}
          <span className="ml-auto shrink-0 font-mono text-xs tabular-nums text-fg-subtle">
            {a.time}
          </span>
        </div>
        <p className="mt-0.5 text-sm text-fg-muted">{a.description}</p>
        {a.actions ? <div className="mt-2 flex gap-2">{a.actions}</div> : null}
      </div>
    </li>
  )
}

function ActivitySkeletonList({ count }: { count: number }) {
  return (
    <ol className="divide-y divide-border">
      {Array.from({ length: count }).map((_, i) => (
        <li key={i} className="flex gap-3 p-3">
          <Skeleton className="size-9 shrink-0 rounded-md" />
          <div className="min-w-0 flex-1 space-y-1.5">
            <Skeleton className="h-3.5 w-2/3" />
            <Skeleton className="h-3 w-full" />
          </div>
        </li>
      ))}
    </ol>
  )
}

function ActivityErrorState() {
  return (
    <div className="px-3 py-6 text-center text-sm text-fg-muted">
      Couldn't load activity. Try again later.
    </div>
  )
}

function ActivityEmptyState() {
  return (
    <div className="px-3 py-6 text-center text-sm text-fg-muted">
      No activity yet.
    </div>
  )
}

const ACTION_TONE: Record<string, ActivityTone> = {
  create: "success",
  created: "success",
  update: "info",
  updated: "info",
  delete: "danger",
  deleted: "danger",
  archive: "warning",
  archived: "warning",
  restore: "success",
  restored: "success",
  login: "info",
  logout: "info",
}

const ACTION_ICON: Record<string, React.ElementType> = {
  create: CheckCircle2,
  created: CheckCircle2,
  update: FileSignature,
  updated: FileSignature,
  delete: AlertTriangle,
  deleted: AlertTriangle,
  archive: AlertTriangle,
  archived: AlertTriangle,
  restore: CheckCircle2,
  restored: CheckCircle2,
  login: MessageSquare,
  logout: MessageSquare,
}

function humanise(s: string): string {
  return s
    .replace(/[_-]+/g, " ")
    .replace(/^./, (c) => c.toUpperCase())
}

export function auditLogToActivity(log: AuditLog): Activity {
  const action = (log.action_type ?? "").toLowerCase()
  const tone = ACTION_TONE[action] ?? "info"
  const icon = ACTION_ICON[action] ?? CalendarClock

  const resource = humanise(log.resource_type ?? "record")
  const title = `${humanise(action || "Activity")} ${resource.toLowerCase()}`

  return {
    id: log.id,
    icon,
    tone,
    title,
    description: log.resource_id ? `#${log.resource_id.slice(0, 8)}` : "",
    time: formatRelativeTime(log.created_at),
  }
}
