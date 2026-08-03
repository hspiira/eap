import { useMemo } from "react"

import { useQuery } from "@tanstack/react-query"
import { Link } from "@tanstack/react-router"
import { CalendarClock, ChevronRight, Plus } from "lucide-react"

import { serviceSessionsApi } from "@/api/endpoints/service-sessions"
import { servicesApi } from "@/api/endpoints/services"
import { EmptyState } from "@/components/common/EmptyState"
import { StatusBadge } from "@/components/common/StatusBadge"
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"
import { entityListKey } from "@/lib/queries"
import type { Service } from "@/types/entities"

/**
 * Recent-session history for one person or one provider. Self-contained:
 * runs its own query and resolves service names, so detail pages embed it
 * as a single line. Service names render as names — never id fragments.
 */
export function SessionHistory({
  personId,
  providerId,
  limit = 10,
}: {
  personId?: string
  providerId?: string
  limit?: number
}) {
  const params = {
    ...(personId ? { person_id: personId } : {}),
    ...(providerId ? { provider_id: providerId } : {}),
    limit: 20,
  }
  const query = useQuery({
    queryKey: entityListKey("service-sessions", params),
    queryFn: () => serviceSessionsApi.list(params),
    enabled: Boolean(personId || providerId),
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
          personId
            ? "Sessions delivered to this person will show up here."
            : "Sessions delivered by this provider will show up here."
        }
        action={
          personId ? (
            <Link
              to="/service-sessions"
              search={{ new: true, person_id: personId }}
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
        <p className="text-xs text-fg/55">{sessions.length} recent sessions.</p>
        {personId ? (
          <Link
            to="/service-sessions"
            search={{ person_id: personId }}
            className="text-xs font-medium text-primary hover:underline"
          >
            View all
          </Link>
        ) : null}
      </div>
      <div className="overflow-hidden border border-fg/10 bg-surface">
        <Table className="w-full caption-bottom text-sm">
          <TableHeader className="border-b-0 bg-surface shadow-[inset_0_-1px_0_rgb(0_0_0/0.08)]">
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
                <TableCell className="text-sm text-fg">
                  {new Date(s.scheduled_at).toLocaleString()}
                </TableCell>
                <TableCell className="text-sm text-fg/75">
                  {servicesById.get(s.service_id)?.name ?? "—"}
                </TableCell>
                <TableCell>
                  <StatusBadge status={s.status} />
                </TableCell>
                <TableCell className="text-right">
                  <Link
                    to="/service-sessions/$sessionId"
                    params={{ sessionId: s.id }}
                    aria-label="Open session"
                    className="inline-flex text-fg/40 hover:text-primary"
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
