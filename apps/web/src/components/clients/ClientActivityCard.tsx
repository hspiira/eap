import { useQuery } from "@tanstack/react-query"
import { Activity, FileText, Mail, Phone, Users } from "lucide-react"

import { activitiesApi } from "@/api/endpoints/activities"
import { Panel, PanelEmpty, PanelList } from "@/components/common/Panel"
import { Button } from "@/components/ui/button"
import { Skeleton } from "@/components/ui/skeleton"

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
  } catch (_err) {
    return iso
  }
}

interface ClientActivityCardProps {
  clientId: string
  limit?: number
  className?: string
}

export function ClientActivityCard({ clientId, limit = 10, className }: ClientActivityCardProps) {
  const activitiesQuery = useQuery({
    queryKey: ["activities", "client", clientId, limit],
    queryFn: () => activitiesApi.list({ limit, client_id: clientId }),
  })
  const loading = activitiesQuery.isPending
  const activities = activitiesQuery.data?.items ?? []

  return (
    <Panel
      icon={Activity}
      title="Activity"
      count={
        !loading && !activitiesQuery.isError && (activitiesQuery.data?.total ?? 0) > 0
          ? activitiesQuery.data?.total
          : null
      }
      className={className}
      bodyClassName="p-0"
    >
      {loading ? (
        <PanelList>
          {[1, 2, 3].map((i) => (
            <li key={i} className="flex gap-3 px-3 py-2.5">
              <Skeleton className="size-8 shrink-0 rounded-sm" />
              <div className="min-w-0 flex-1 space-y-1.5">
                <Skeleton className="h-3.5 w-2/3" />
                <Skeleton className="h-3 w-full" />
              </div>
            </li>
          ))}
        </PanelList>
      ) : activitiesQuery.isError ? (
        <PanelEmpty>
          <span className="block">Activity could not be loaded.</span>
          <Button
            variant="outline"
            size="sm"
            className="mt-2"
            onClick={() => void activitiesQuery.refetch()}
          >
            Retry
          </Button>
        </PanelEmpty>
      ) : activities.length === 0 ? (
        <PanelEmpty>No recent activity.</PanelEmpty>
      ) : (
        <PanelList className="max-h-104 overflow-y-auto">
          {activities.map((a) => {
            const Icon = ACTIVITY_ICONS[a.activity_type] ?? Activity
            const title = a.title ?? a.activity_type
            return (
              <li key={a.id} className="flex gap-3 px-3 py-2.5">
                <span
                  className="grid size-8 shrink-0 place-items-center rounded-sm bg-fg/8 text-fg/60"
                  aria-hidden
                >
                  <Icon className="size-4" />
                </span>
                <div className="min-w-0 flex-1">
                  <div className="flex flex-wrap items-baseline gap-2">
                    <span className="text-sm font-medium text-fg">{title}</span>
                    <span className="ml-auto shrink-0 text-xs tabular-nums text-fg-subtle">
                      {formatActivityTime(a.occurred_at)}
                    </span>
                  </div>
                  {a.description ? (
                    <p className="mt-0.5 text-sm text-fg/65">{a.description}</p>
                  ) : null}
                </div>
              </li>
            )
          })}
        </PanelList>
      )}
    </Panel>
  )
}
