import { useEffect, useState } from "react"

import { Activity, FileText, Mail, Phone, Users } from "lucide-react"

import { activitiesApi } from "@/api/endpoints/activities"
import { Badge } from "@/components/ui/badge"
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"
import { Skeleton } from "@/components/ui/skeleton"
import { cn } from "@/lib/utils"
import type { Activity as ActivityEntity } from "@/types/entities"

const ACTIVITY_ICONS: Record<string, React.ElementType> = {
  CALL: Phone,
  EMAIL: Mail,
  MEETING: Users,
  NOTE: FileText,
}

function formatActivityTime(iso: string): string {
  try {
    const d = new Date(iso)
    const now = new Date()
    const sameDay = d.toDateString() === now.toDateString()
    if (sameDay) {
      return `Today, ${d.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}`
    }
    const yesterday = new Date(now)
    yesterday.setDate(yesterday.getDate() - 1)
    if (d.toDateString() === yesterday.toDateString()) return "Yesterday"
    return d.toLocaleDateString([], {
      month: "short",
      day: "numeric",
      year: d.getFullYear() !== now.getFullYear() ? "numeric" : undefined,
    })
  } catch {
    return iso
  }
}

interface ClientActivityCardProps {
  clientId: string
  limit?: number
  className?: string
}

export function ClientActivityCard({
  clientId,
  limit = 10,
  className,
}: ClientActivityCardProps) {
  const [activities, setActivities] = useState<ActivityEntity[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    setLoading(true)
    activitiesApi
      .list({ limit: 20 } as Record<string, unknown>)
      .then((res) => {
        const items = (res.items ?? []).filter(
          (a: ActivityEntity) => a.client_id === clientId,
        )
        setActivities(items.slice(0, limit))
      })
      .catch(() => setActivities([]))
      .finally(() => setLoading(false))
  }, [clientId, limit])

  return (
    <Card className={cn("rounded-md", className)}>
      <CardHeader className="flex-row items-center justify-between gap-2 space-y-0 border-b border-border-subtle p-3">
        <CardTitle className="text-sm font-semibold text-fg">Activity</CardTitle>
        {!loading && activities.length > 0 ? (
          <Badge variant="secondary" size="sm" className="font-mono tabular-nums">
            {activities.length}
          </Badge>
        ) : null}
      </CardHeader>
      <CardContent className="p-0">
        {loading ? (
          <ul className="divide-y divide-border-subtle">
            {[1, 2, 3].map((i) => (
              <li key={i} className="flex gap-3 p-3">
                <Skeleton className="size-9 shrink-0 rounded-md" />
                <div className="min-w-0 flex-1 space-y-1.5">
                  <Skeleton className="h-3.5 w-2/3" />
                  <Skeleton className="h-3 w-full" />
                </div>
              </li>
            ))}
          </ul>
        ) : activities.length === 0 ? (
          <div className="px-3 py-6 text-center text-sm text-fg-muted">
            No recent activity.
          </div>
        ) : (
          <ul className="max-h-100 divide-y divide-border-subtle overflow-y-auto">
            {activities.map((a) => {
              const Icon = ACTIVITY_ICONS[a.activity_type] ?? Activity
              const title = a.title ?? a.activity_type
              return (
                <li key={a.id} className="flex gap-3 p-3">
                  <span
                    className="grid size-9 shrink-0 place-items-center rounded-md bg-muted text-fg-muted"
                    aria-hidden
                  >
                    <Icon className="size-4" />
                  </span>
                  <div className="min-w-0 flex-1">
                    <div className="flex flex-wrap items-baseline gap-2">
                      <span className="text-sm font-medium text-fg">
                        {title}
                      </span>
                      <span className="font-mono ml-auto shrink-0 text-xs tabular-nums text-fg-subtle">
                        {formatActivityTime(a.occurred_at)}
                      </span>
                    </div>
                    {a.description ? (
                      <p className="mt-0.5 text-sm text-fg-muted">
                        {a.description}
                      </p>
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
