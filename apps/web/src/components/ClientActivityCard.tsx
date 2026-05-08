import { useEffect, useState } from "react"

import { Activity, FileText, Mail, Phone, Users } from "lucide-react"

import { activitiesApi } from "@/api/endpoints/activities"
import { Skeleton } from "@/components/ui/skeleton"
import { cn } from "@/lib/utils"
import type { Activity as ActivityEntity } from "@/types/entities"

const skeletonClass = "rounded-none bg-ink/15"

const ACTIVITY_ICONS: Record<string, typeof Phone> = {
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
    if (sameDay) return `Today, ${d.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}`
    const yesterday = new Date(now)
    yesterday.setDate(yesterday.getDate() - 1)
    if (d.toDateString() === yesterday.toDateString()) return "Yesterday"
    return d.toLocaleDateString([], { month: "short", day: "numeric", year: d.getFullYear() !== now.getFullYear() ? "numeric" : undefined })
  } catch {
    return iso
  }
}

interface ClientActivityCardProps {
  clientId: string
  limit?: number
  className?: string
}

export function ClientActivityCard({ clientId, limit = 10, className }: ClientActivityCardProps) {
  const [activities, setActivities] = useState<ActivityEntity[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    setLoading(true)
    activitiesApi
      .list({ limit: 20 } as Record<string, unknown>)
      .then((res) => {
        const items = (res.items ?? []).filter((a: ActivityEntity) => a.client_id === clientId)
        setActivities(items.slice(0, limit))
      })
      .catch(() => setActivities([]))
      .finally(() => setLoading(false))
  }, [clientId, limit])

  if (loading) {
    return (
      <div
        className={cn(
          "flex flex-col border border-ink/30 rounded-none bg-neutral-50 overflow-hidden",
          className
        )}
      >
        <div className="border-b border-ink/20 px-4 py-3 bg-warm/20">
          <h3 className="text-sm font-semibold text-ink">Activity</h3>
        </div>
        <div className="divide-y divide-ink/15 px-4">
          {[1, 2, 3, 4].map((i) => (
            <div key={i} className="flex gap-3 py-3">
              <Skeleton className={cn(skeletonClass, "h-9 w-9 shrink-0")} />
              <div className="min-w-0 flex-1 space-y-1">
                <Skeleton className={cn(skeletonClass, "h-4 w-32")} />
                <Skeleton className={cn(skeletonClass, "h-3 w-full max-w-[200px]")} />
                <Skeleton className={cn(skeletonClass, "h-3 w-16")} />
              </div>
            </div>
          ))}
        </div>
      </div>
    )
  }

  if (activities.length === 0) {
    return (
      <div
        className={cn(
          "flex flex-col border border-ink/30 rounded-none bg-neutral-50 overflow-hidden",
          className
        )}
      >
        <div className="border-b border-ink/20 px-4 py-3 bg-warm/20">
          <h3 className="text-sm font-semibold text-ink">Activity</h3>
        </div>
        <div className="px-4 py-4 text-sm text-ink/80">No recent activity.</div>
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
      <div className="flex items-center justify-between border-b border-ink/20 px-4 py-3 bg-warm/20">
        <h3 className="text-sm font-semibold text-ink">Activity</h3>
        <span className="flex h-5 min-w-[20px] items-center justify-center bg-ink/15 px-1.5 text-xs font-medium text-ink rounded-none">
          {activities.length}
        </span>
      </div>
      <div className="divide-y divide-ink/15 max-h-[400px] overflow-y-auto">
        {activities.map((a) => {
          const Icon = ACTIVITY_ICONS[a.activity_type] ?? Activity
          const title = a.title ?? a.activity_type
          return (
            <div key={a.id} className="flex gap-3 px-4 py-3">
              <div className="flex h-9 w-9 shrink-0 items-center justify-center border border-ink/20 bg-warm/50 text-ink rounded-none">
                <Icon className="h-4 w-4" />
              </div>
              <div className="min-w-0 flex-1">
                <div className="flex flex-wrap items-center gap-2">
                  <span className="text-sm font-medium text-ink">{title}</span>
                  <span className="shrink-0 text-xs text-ink/70">
                    {formatActivityTime(a.occurred_at)}
                  </span>
                </div>
                {a.description && (
                  <p className="mt-0.5 text-sm text-ink/90">{a.description}</p>
                )}
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}
