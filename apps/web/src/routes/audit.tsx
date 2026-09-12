import { useMemo, useState } from "react"

import { useQueries, useQuery } from "@tanstack/react-query"
import { createFileRoute } from "@tanstack/react-router"
import { ClipboardCheck, X } from "lucide-react"

import { auditApi } from "@/api/endpoints/audit"
import { usersApi } from "@/api/endpoints/users"
import { AuthedLayout } from "@/components/common/AuthedLayout"
import { DatePicker } from "@/components/common/DatePicker"
import { EmptyState } from "@/components/common/EmptyState"
import { ErrorState } from "@/components/common/ErrorState"
import { FilterBar, FilterChip, FilterTrigger } from "@/components/common/FilterBar"
import { PageShell } from "@/components/common/PageShell"
import { TableSkeleton } from "@/components/common/PageSkeletons"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Pagination } from "@/components/ui/pagination"
import { Sheet, SheetContent, SheetDescription, SheetTitle } from "@/components/ui/sheet"
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"
import { entityListKey } from "@/lib/queries"
import { enumOptions, enumParam, listSearchSchema } from "@/lib/search-params"
import type { AuditLog, EntityChange } from "@/types/entities"
import { ActionType } from "@/types/enums"
import { getStatusLabel } from "@/utils/statusColors"

export const Route = createFileRoute("/audit")({
  component: AuditRoute,
  validateSearch: listSearchSchema({
    action_type: enumParam(ActionType),
    resource_type: (v) => (typeof v === "string" && v.trim() ? v : undefined),
    resource_id: (v) => (typeof v === "string" && v.trim() ? v : undefined),
    user_id: (v) => (typeof v === "string" && v.trim() ? v : undefined),
    date_from: (v) => (typeof v === "string" && v.trim() ? v : undefined),
    date_to: (v) => (typeof v === "string" && v.trim() ? v : undefined),
  }),
})

const ACTION_OPTIONS = enumOptions(ActionType, "All actions")
const LIMIT = 25

const ACTION_TONE: Record<string, "default" | "secondary" | "destructive" | "outline"> = {
  CREATE: "secondary",
  UPDATE: "outline",
  DELETE: "destructive",
  LOGIN: "outline",
  LOGOUT: "outline",
  APPROVE: "secondary",
  REJECT: "destructive",
  LIST: "outline",
  VIEW: "outline",
  EXPORT: "outline",
  IMPORT: "outline",
}

function AuditRoute() {
  const searchParams = Route.useSearch()
  const navigate = Route.useNavigate()
  const [page, setPage] = useState(1)
  const [selected, setSelected] = useState<AuditLog | null>(null)

  const setFilter = (key: string, value: string | undefined) => {
    setPage(1)
    void navigate({ search: (prev) => ({ ...prev, [key]: value }) })
  }

  const params = {
    page,
    limit: LIMIT,
    action_type: searchParams.action_type,
    resource_type: searchParams.resource_type,
    resource_id: searchParams.resource_id,
    user_id: searchParams.user_id,
    start_date: searchParams.date_from,
    end_date: searchParams.date_to,
    sort_by: "occurred_at",
    sort_desc: true,
  }

  const query = useQuery({
    queryKey: entityListKey("audit", params),
    queryFn: () => auditApi.list(params),
  })

  const items = query.data?.items ?? []
  const total = query.data?.total ?? 0
  const hasFilters = Boolean(
    searchParams.action_type ||
    searchParams.resource_type ||
    searchParams.resource_id ||
    searchParams.user_id ||
    searchParams.date_from ||
    searchParams.date_to,
  )

  const actorNames = useActorNames(items)

  return (
    <AuthedLayout>
      <PageShell icon={ClipboardCheck} breadcrumb="Platform · Audit">
        <FilterBar>
          {searchParams.action_type ? (
            <FilterChip
              label={`Action: ${getStatusLabel(searchParams.action_type)}`}
              onRemove={() => setFilter("action_type", undefined)}
            />
          ) : null}
          {searchParams.resource_type ? (
            <FilterChip
              label={`Resource: ${getStatusLabel(searchParams.resource_type)}`}
              onRemove={() => setFilter("resource_type", undefined)}
            />
          ) : null}
          {searchParams.resource_id ? (
            <FilterChip
              label={`Resource id: ${searchParams.resource_id}`}
              onRemove={() => setFilter("resource_id", undefined)}
            />
          ) : null}
          {searchParams.user_id ? (
            <FilterChip
              label={`Actor id: ${searchParams.user_id}`}
              onRemove={() => setFilter("user_id", undefined)}
            />
          ) : null}
          <FilterTrigger
            label="All actions"
            value={searchParams.action_type ?? "all"}
            options={ACTION_OPTIONS}
            onChange={(v) => setFilter("action_type", v === "all" ? undefined : v)}
          />
          <Input
            placeholder="Resource type…"
            aria-label="Filter by resource type"
            className="h-7 w-36 text-xs"
            defaultValue={searchParams.resource_type ?? ""}
            onBlur={(e) => setFilter("resource_type", e.target.value.trim() || undefined)}
            onKeyDown={(e) => {
              if (e.key === "Enter") e.currentTarget.blur()
            }}
          />
          <Input
            placeholder="Resource id…"
            aria-label="Filter by resource id"
            className="h-7 w-40 text-xs"
            defaultValue={searchParams.resource_id ?? ""}
            onBlur={(e) => setFilter("resource_id", e.target.value.trim() || undefined)}
            onKeyDown={(e) => {
              if (e.key === "Enter") e.currentTarget.blur()
            }}
          />
          <Input
            placeholder="Actor id…"
            aria-label="Filter by actor id"
            className="h-7 w-40 text-xs"
            defaultValue={searchParams.user_id ?? ""}
            onBlur={(e) => setFilter("user_id", e.target.value.trim() || undefined)}
            onKeyDown={(e) => {
              if (e.key === "Enter") e.currentTarget.blur()
            }}
          />
          <DatePicker
            value={searchParams.date_from}
            onChange={(v) => setFilter("date_from", v)}
            placeholder="From date"
            aria-label="Filter from date"
          />
          <DatePicker
            value={searchParams.date_to}
            onChange={(v) => setFilter("date_to", v)}
            placeholder="To date"
            aria-label="Filter to date"
          />
          {hasFilters ? (
            <Button
              variant="ghost"
              size="sm"
              className="h-7 gap-1 px-2 text-xs text-fg-muted"
              onClick={() => void navigate({ search: {} })}
            >
              <X className="size-3" />
              Clear filters
            </Button>
          ) : null}
        </FilterBar>

        <div className="flex min-h-0 flex-1 flex-col bg-bg">
          {query.isLoading ? (
            <div className="flex-1 overflow-auto p-5">
              <TableSkeleton cols={5} />
            </div>
          ) : query.isError ? (
            <ErrorState message="Could not load audit logs." onRetry={() => void query.refetch()} />
          ) : items.length === 0 ? (
            <EmptyState
              icon={ClipboardCheck}
              title={hasFilters ? "No audit entries match your filters" : "No audit entries yet"}
              description={
                hasFilters
                  ? "Try a different filter or clear them."
                  : "Actions recorded across the tenant will appear here."
              }
            />
          ) : (
            <>
              <div className="relative min-h-0 flex-1 overflow-auto">
                <Table className="w-full caption-bottom text-sm" scrollable={false}>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Occurred</TableHead>
                      <TableHead>Actor</TableHead>
                      <TableHead>Action</TableHead>
                      <TableHead>Resource</TableHead>
                      <TableHead>Description</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {items.map((log) => (
                      <AuditRow
                        key={log.id}
                        log={log}
                        actorLabel={actorNames[log.user_id ?? ""] ?? log.user_id ?? "System"}
                        onSelect={() => setSelected(log)}
                      />
                    ))}
                  </TableBody>
                </Table>
              </div>
              <div className="shrink-0 border-t border-fg/10 bg-surface px-3 py-2">
                <Pagination
                  page={page}
                  total={total}
                  limit={LIMIT}
                  shownCount={items.length}
                  onPageChange={setPage}
                />
              </div>
            </>
          )}
        </div>
      </PageShell>

      <AuditDetailSheet
        log={selected}
        onOpenChange={(open) => {
          if (!open) setSelected(null)
        }}
      />
    </AuthedLayout>
  )
}

function AuditRow({
  log,
  actorLabel,
  onSelect,
}: {
  log: AuditLog
  actorLabel: string
  onSelect: () => void
}) {
  return (
    <TableRow
      className="cursor-pointer hover:bg-surface-hover"
      onClick={onSelect}
      tabIndex={0}
      role="button"
      aria-label={`View changes for ${log.action_type} on ${log.resource_type}`}
      onKeyDown={(e) => {
        if (e.key === "Enter" || e.key === " ") {
          e.preventDefault()
          onSelect()
        }
      }}
    >
      <TableCell className="whitespace-nowrap text-xs tabular-nums text-fg-muted">
        {formatOccurredAt(log.occurred_at)}
      </TableCell>
      <TableCell className="text-sm text-fg">{actorLabel}</TableCell>
      <TableCell>
        <Badge variant={ACTION_TONE[log.action_type] ?? "outline"} size="sm">
          {getStatusLabel(log.action_type)}
        </Badge>
      </TableCell>
      <TableCell className="text-sm text-fg">
        {getStatusLabel(log.resource_type)}
        {log.resource_id ? (
          <span className="ml-1 text-xs text-fg-muted">#{log.resource_id.slice(0, 8)}</span>
        ) : null}
      </TableCell>
      <TableCell className="max-w-[28ch] truncate text-sm text-fg-muted">
        {log.description ?? ""}
      </TableCell>
    </TableRow>
  )
}

/** ISO instant, in full: this is the only timestamp the API returns.
 * There is no separate processing/delivery time to show alongside it. */
function formatOccurredAt(iso: string): string {
  const d = new Date(iso)
  if (Number.isNaN(d.getTime())) return iso
  return d.toLocaleString(undefined, {
    year: "numeric",
    month: "short",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
  })
}

/** Resolves the actor's email for each unique user_id on the current page. */
function useActorNames(items: ReadonlyArray<AuditLog>): Record<string, string> {
  const ids = useMemo(
    () => [...new Set(items.map((i) => i.user_id).filter((id): id is string => Boolean(id)))],
    [items],
  )
  const results = useQueries({
    queries: ids.map((id) => ({
      queryKey: ["users", "detail", id],
      queryFn: () => usersApi.getById(id),
      staleTime: 5 * 60_000,
      retry: false,
    })),
  })
  return useMemo(() => {
    const map: Record<string, string> = {}
    ids.forEach((id, i) => {
      const email = results[i]?.data?.email
      if (email) map[id] = email
    })
    return map
  }, [ids, results])
}

function AuditDetailSheet({
  log,
  onOpenChange,
}: {
  log: AuditLog | null
  onOpenChange: (open: boolean) => void
}) {
  const changes = useQuery({
    queryKey: ["audit", "log-changes", log?.id],
    queryFn: () => auditApi.getChanges(log!.id),
    enabled: !!log,
  })

  return (
    <Sheet open={!!log} onOpenChange={onOpenChange}>
      <SheetContent side="right" className="flex h-full w-full flex-col gap-0 sm:max-w-lg">
        {log ? (
          <>
            <div className="border-b border-fg/10 px-5 py-4">
              <SheetTitle className="text-base font-semibold text-fg">
                {getStatusLabel(log.action_type)} · {getStatusLabel(log.resource_type)}
              </SheetTitle>
              <SheetDescription className="mt-1 text-xs text-fg-muted">
                {formatOccurredAt(log.occurred_at)}
                {log.resource_id ? ` · #${log.resource_id.slice(0, 8)}` : ""}
              </SheetDescription>
            </div>
            <div className="min-h-0 flex-1 overflow-y-auto px-5 py-4">
              {log.description ? <p className="mb-4 text-sm text-fg">{log.description}</p> : null}
              <ChangeDetails changes={changes} />
            </div>
          </>
        ) : null}
      </SheetContent>
    </Sheet>
  )
}

function ChangeDetails({
  changes,
}: {
  changes: { isPending: boolean; isError: boolean; data?: EntityChange[] }
}) {
  if (changes.isPending) return <p className="text-sm text-fg-muted">Loading changes…</p>
  if (changes.isError) {
    return (
      <p className="text-sm text-danger-fg" role="alert">
        Could not load the change details.
      </p>
    )
  }
  const list = changes.data ?? []
  if (list.length === 0) {
    return <p className="text-sm text-fg-muted">No field-level changes recorded.</p>
  }
  return (
    <div className="space-y-4">
      {list.map((change) => (
        <Table key={change.id} className="w-full text-sm" scrollable={false}>
          <TableHeader>
            <TableRow>
              <TableHead className="w-1/3">Field</TableHead>
              <TableHead>Before</TableHead>
              <TableHead>After</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {change.field_changes.map((fc) => (
              <TableRow key={fc.field_name}>
                <TableCell className="align-top text-fg-muted">{fc.field_name}</TableCell>
                <TableCell className="align-top text-fg">{fc.old_value ?? "—"}</TableCell>
                <TableCell className="align-top text-fg">{fc.new_value ?? "—"}</TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      ))}
    </div>
  )
}
