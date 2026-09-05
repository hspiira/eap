import { useMemo } from "react"

import { useQuery } from "@tanstack/react-query"
import { Link } from "@tanstack/react-router"
import { CalendarClock, ChevronRight, Plus } from "lucide-react"

import { serviceSessionsApi } from "@/api/endpoints/service-sessions"
import { servicesApi } from "@/api/endpoints/services"
import { EmptyState } from "@/components/common/EmptyState"
import { StatusBadge } from "@/components/common/StatusBadge"
import { TABLE_HEAD } from "@/components/common/tableStyles"
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"
import { formatDateTime } from "@/lib/format"
import { entityListKey } from "@/lib/queries"
import type { Service } from "@/types/entities"

/**
 * Recent-session history for one member or one provider. Self-contained:
 * runs its own query and resolves service names, so detail pages embed it
 * as a single line. Service names render as names, never id fragments.
 */
export function SessionHistory({
  memberId,
  providerId,
  limit = 10,
}: {
  memberId?: string
  providerId?: string
  limit?: number
}) {
  const params = {
    ...(memberId ? { member_id: memberId } : {}),
    ...(providerId ? { provider_id: providerId } : {}),
    limit: 20,
  }
  const query = useQuery({
    queryKey: entityListKey("service-sessions", params),
    queryFn: () => serviceSessionsApi.list(params),
    enabled: Boolean(memberId || providerId),
    staleTime: 30_000,
  })
  const sessions = query.data?.items ?? []

  const { data: servicesData } = useQuery({
    queryKey: ["services", "lookup"],
    queryFn: () => servicesApi.list({ limit: 200 }),
    staleTime: 5 * 60_000,
  })
  const servicesById = useMemo(() => {
    const m = new Map<string, Service>()
    for (const s of servicesData?.items ?? []) m.set(s.id, s)
    return m
  }, [servicesData])

  if (query.isPending) return <p className="text-sm text-fg/65">Loading sessions…</p>
  if (sessions.length === 0) {
    return (
      <EmptyState
        icon={CalendarClock}
        title="No sessions yet"
        description={
          memberId
            ? "Sessions delivered to this member will show up here."
            : "Sessions delivered by this provider will show up here."
        }
        action={
          memberId ? (
            <Link
              to="/service-sessions"
              search={{ new: true, member_id: memberId }}
              className="inline-flex h-9 items-center gap-1.5 rounded-sm border border-fg/15 bg-surface px-3 text-sm font-medium text-fg hover:bg-surface-hover"
            >
              <Plus className="size-4" />
              Schedule session
            </Link>
          ) : undefined
        }
      />
    )
  }

  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between">
        <p className="text-xs text-fg-muted">{sessions.length} recent sessions.</p>
        {memberId ? (
          <Link
            to="/service-sessions"
            search={{ member_id: memberId }}
            className="text-xs font-medium text-primary hover:underline"
          >
            View all
          </Link>
        ) : null}
      </div>
      <div className="overflow-hidden border border-fg/10 bg-surface">
        <Table className="w-full caption-bottom text-sm">
          <TableHeader className={TABLE_HEAD}>
            <TableRow className="border-fg/8 hover:bg-transparent">
              <TableHead>Scheduled</TableHead>
              <TableHead>Service</TableHead>
              <TableHead>Status</TableHead>
              <TableHead className="w-10 text-right text-fg/65">
                <span className="sr-only">Open</span>
              </TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {sessions.slice(0, limit).map((s) => (
              <TableRow key={s.id} className="group border-fg/8">
                <TableCell className="text-sm text-fg">{formatDateTime(s.scheduled_at)}</TableCell>
                <TableCell className="text-sm text-fg/75">
                  {servicesById.get(s.service_id)?.name ?? "-"}
                </TableCell>
                <TableCell>
                  <StatusBadge status={s.status} />
                </TableCell>
                <TableCell className="text-right">
                  <Link
                    to="/service-sessions/$sessionId"
                    params={{ sessionId: s.id }}
                    aria-label="Open session"
                    className="inline-flex text-fg-subtle hover:text-primary"
                  >
                    <ChevronRight className="size-4" />
                  </Link>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </div>
    </div>
  )
}
