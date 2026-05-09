import { useEffect, useState } from "react"

import { useQueryClient } from "@tanstack/react-query"
import { createFileRoute, Link, useNavigate, useSearch } from "@tanstack/react-router"
import {
  Download,
  ExternalLink,
  MoreHorizontal,
  Plus,
  RotateCw,
  Wrench,
} from "lucide-react"

import { servicesApi } from "@/api/endpoints/services"
import { EmptyState } from "@/components/common/EmptyState"
import {
  FilterBar,
  FilterButton,
  FilterChip,
  FilterSearch,
  FilterTrigger,
} from "@/components/common/FilterBar"
import { PageShell } from "@/components/common/PageShell"
import { nextSort, SortHeader, type SortState } from "@/components/common/SortHeader"
import { StatusBadge } from "@/components/common/StatusBadge"
import { humanizeServiceType, ServiceFormSheet } from "@/components/ServiceFormSheet"
import { TableSkeleton } from "@/components/common/PageSkeletons"
import { Button } from "@/components/ui/button"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"
import { Pagination } from "@/components/ui/pagination"
import {
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"
import { useDebouncedValue } from "@/hooks/useDebouncedValue"
import { useEntityList } from "@/lib/queries"
import type { Service } from "@/types/entities"
import { BaseStatus } from "@/types/enums"
import { normalizeErrorMessage } from "@/lib/errors"

function isStatus(value: unknown): value is BaseStatus {
  return (
    value === BaseStatus.ACTIVE ||
    value === BaseStatus.INACTIVE ||
    value === BaseStatus.PENDING ||
    value === BaseStatus.ARCHIVED
  )
}

export const Route = createFileRoute("/services/")({
  component: ServicesListPage,
  validateSearch: (search: Record<string, unknown>) => {
    const out: { new?: boolean; search?: string; status?: BaseStatus } = {}
    if (search.new === "1" || search.new === true) out.new = true
    if (typeof search.search === "string" && search.search.trim()) out.search = search.search
    if (isStatus(search.status)) out.status = search.status
    return out
  },
})

const STATUS_OPTIONS = [
  { value: "all", label: "All statuses" },
  { value: BaseStatus.ACTIVE, label: "Active" },
  { value: BaseStatus.INACTIVE, label: "Inactive" },
  { value: BaseStatus.ARCHIVED, label: "Archived" },
] as const

const GROUP_OPTIONS = [
  { value: "all", label: "Any size" },
  { value: "individual", label: "Individual only" },
  { value: "group", label: "Group enabled" },
] as const

type StatusFilter = (typeof STATUS_OPTIONS)[number]["value"]
type GroupFilter = (typeof GROUP_OPTIONS)[number]["value"]

const ROW_BORDER = "border-fg/8"

function ServicesListPage() {
  const searchParams = useSearch({ from: "/services/" })
  const navigate = useNavigate({ from: "/services/" })
  const [searchInput, setSearchInput] = useState(searchParams.search ?? "")
  const [groupFilter, setGroupFilter] = useState<GroupFilter>("all")
  const [addOpen, setAddOpen] = useState(false)
  const [page, setPage] = useState(1)
  const [sort, setSort] = useState<SortState>({ field: undefined, desc: false })
  const limit = 20
  const queryClient = useQueryClient()

  const toggleSort = (field: string) => {
    setSort((prev) => nextSort(prev, field))
    setPage(1)
  }

  const debouncedSearch = useDebouncedValue(searchInput.trim(), 300)
  const activeSearch = debouncedSearch || undefined
  const activeStatus = searchParams.status

  useEffect(() => {
    if (searchParams.new) {
      setAddOpen(true)
      navigate({ search: (prev) => ({ ...prev, new: undefined }), replace: true })
    }
  }, [searchParams.new, navigate])

  useEffect(() => {
    if (activeSearch !== searchParams.search) {
      navigate({ search: (prev) => ({ ...prev, search: activeSearch }), replace: true })
      setPage(1)
    }
  }, [activeSearch, navigate, searchParams.search])

  const handleStatusChange = (next: StatusFilter) => {
    const status = next === "all" ? undefined : next
    navigate({ search: (prev) => ({ ...prev, status }), replace: true })
    setPage(1)
  }

  const query = useEntityList({
    resource: "services",
    params: {
      page,
      limit,
      search: activeSearch,
      status: activeStatus,
      sort_by: sort.field,
      sort_desc: sort.field ? sort.desc : undefined,
    },
    listFn: servicesApi.list,
  })
  const allItems = query.data?.items ?? []
  const items = filterByGroup(allItems, groupFilter)
  const total = query.data?.total ?? 0
  const loading = query.isPending
  const error = query.isError ? normalizeErrorMessage(query.error, "Failed to load data") : null
  const refetch = () => queryClient.invalidateQueries({ queryKey: ["services", "list"] })
  const hasFilters = Boolean(activeSearch) || Boolean(activeStatus) || groupFilter !== "all"

  return (
    <PageShell
      icon={Wrench}
      breadcrumb="Catalog · Services"
      actions={
        <>
          <IconButton label="Refresh" onClick={refetch} icon={RotateCw} />
          <IconButton label="Export" icon={Download} />
          <span className="mx-1 h-4 w-px bg-fg/15" aria-hidden />
          <Button size="sm" className="h-7 gap-1.5 px-2.5" onClick={() => setAddOpen(true)}>
            <Plus className="size-3.5" />
            Add service
          </Button>
        </>
      }
    >
      <FilterBar>
        <FilterButton
          options={[
            { id: "status", label: "Status" },
            { id: "type", label: "Type" },
            { id: "group", label: "Group size" },
          ]}
        />
        {activeStatus ? (
          <FilterChip
            label={`Status is ${activeStatus}`}
            onRemove={() => handleStatusChange("all")}
          />
        ) : null}
        <FilterTrigger
          label="All statuses"
          value={(activeStatus ?? "all") as StatusFilter}
          options={STATUS_OPTIONS}
          onChange={handleStatusChange}
        />
        <FilterTrigger
          label="Any size"
          value={groupFilter}
          options={GROUP_OPTIONS}
          onChange={setGroupFilter}
        />
        <div className="ml-auto" />
        <FilterSearch
          value={searchInput}
          onChange={setSearchInput}
          placeholder="Search services…"
        />
      </FilterBar>

      <ServiceFormSheet open={addOpen} onOpenChange={setAddOpen} onSaved={() => refetch()} />

      <div className="flex min-h-0 flex-1 flex-col bg-bg">
        {loading ? (
          <div className="flex-1 overflow-auto p-5">
            <TableSkeleton cols={5} />
          </div>
        ) : error ? (
          <ErrorState message={error} onRetry={refetch} />
        ) : items.length === 0 ? (
          <EmptyState
            icon={Wrench}
            title={hasFilters ? "No services match your filters" : "No services yet"}
            description={
              hasFilters
                ? "Try a different search or clear filters."
                : "Add an intervention to the catalog so contracts can cover it."
            }
            action={
              hasFilters ? null : (
                <Button size="sm" className="gap-1.5" onClick={() => setAddOpen(true)}>
                  <Plus className="size-4" />
                  Add service
                </Button>
              )
            }
          />
        ) : (
          <>
            <div className="relative min-h-0 flex-1 overflow-auto">
              <table className="w-full caption-bottom text-sm">
                <TableHeader className="sticky top-0 z-10 border-b-0 bg-surface shadow-[inset_0_-1px_0_rgb(0_0_0/0.08)]">
                  <TableRow className={`hover:bg-transparent ${ROW_BORDER}`}>
                    <TableHead className="w-10 px-3">
                      <input
                        type="checkbox"
                        aria-label="Select all"
                        className="size-3.5 cursor-pointer accent-primary"
                      />
                    </TableHead>
                    <TableHead>
                      <SortHeader field="name" sort={sort} onToggle={toggleSort}>
                        Service
                      </SortHeader>
                    </TableHead>
                    <TableHead>
                      <SortHeader field="service_type" sort={sort} onToggle={toggleSort}>
                        Type
                      </SortHeader>
                    </TableHead>
                    <TableHead>
                      <SortHeader field="status" sort={sort} onToggle={toggleSort}>
                        Status
                      </SortHeader>
                    </TableHead>
                    <TableHead>
                      <SortHeader field="duration_minutes" sort={sort} onToggle={toggleSort}>
                        Duration
                      </SortHeader>
                    </TableHead>
                    <TableHead className="text-fg/65">Group</TableHead>
                    <TableHead className="w-16 text-right text-fg/65">
                      <span className="sr-only">Actions</span>
                    </TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {items.map((row) => (
                    <ServiceRow key={row.id} row={row} />
                  ))}
                </TableBody>
              </table>
            </div>
            {total > 0 && (
              <div className="shrink-0 border-t border-fg/10 bg-surface px-3 py-2">
                <Pagination page={page} total={total} limit={limit} onPageChange={setPage} />
              </div>
            )}
          </>
        )}
      </div>
    </PageShell>
  )
}

function ServiceRow({ row }: { row: Service }) {
  const allowGroup = Boolean(row.group_settings?.allow_group_sessions)
  return (
    <TableRow className={`group cursor-default ${ROW_BORDER}`}>
      <TableCell className="px-3">
        <input
          type="checkbox"
          aria-label={`Select ${row.name}`}
          onClick={(e) => e.stopPropagation()}
          className="size-3.5 cursor-pointer accent-primary"
        />
      </TableCell>
      <TableCell>
        <Link
          to="/services/$serviceId"
          params={{ serviceId: row.id }}
          className="flex items-center gap-2.5"
        >
          <span
            aria-hidden
            className="grid size-6 shrink-0 place-items-center bg-primary/10 text-primary"
          >
            <Wrench className="size-3" />
          </span>
          <span className="min-w-0">
            <span className="block truncate text-sm font-medium text-fg group-hover:text-primary">
              {row.name}
            </span>
            {row.description ? (
              <span className="block truncate text-xs text-fg/55">{row.description}</span>
            ) : null}
          </span>
        </Link>
      </TableCell>
      <TableCell>
        {row.service_type ? (
          <span className="inline-flex items-center rounded-sm border border-fg/15 bg-bg px-1.5 py-0.5 text-[11px] font-medium text-fg/75">
            {humanizeServiceType(row.service_type)}
          </span>
        ) : (
          <span className="text-fg/40">—</span>
        )}
      </TableCell>
      <TableCell>
        <StatusBadge status={row.status} />
      </TableCell>
      <TableCell className="font-mono text-sm text-fg/75">
        {row.duration_minutes != null ? `${row.duration_minutes}m` : "—"}
      </TableCell>
      <TableCell>
        {allowGroup ? (
          <span className="text-xs text-fg">
            {row.group_settings?.min_group_size ?? "?"}–
            {row.group_settings?.max_group_size ?? "?"}
          </span>
        ) : (
          <span className="text-xs text-fg/55">Individual</span>
        )}
      </TableCell>
      <TableCell className="text-right">
        <div className="flex items-center justify-end gap-0.5 opacity-0 transition-opacity group-hover:opacity-100 focus-within:opacity-100">
          <Link
            to="/services/$serviceId"
            params={{ serviceId: row.id }}
            aria-label={`Open ${row.name}`}
            className="grid size-7 place-items-center rounded-sm text-fg/65 hover:bg-surface-hover hover:text-fg"
          >
            <ExternalLink className="size-3.5" />
          </Link>
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <button
                type="button"
                aria-label={`More actions for ${row.name}`}
                className="grid size-7 place-items-center rounded-sm text-fg/65 hover:bg-surface-hover hover:text-fg"
              >
                <MoreHorizontal className="size-4" />
              </button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end">
              <DropdownMenuItem asChild>
                <Link to="/services/$serviceId" params={{ serviceId: row.id }}>
                  View details
                </Link>
              </DropdownMenuItem>
              <DropdownMenuSeparator />
              <DropdownMenuItem className="text-destructive focus:text-destructive">
                Archive
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        </div>
      </TableCell>
    </TableRow>
  )
}

function ErrorState({ message, onRetry }: { message: string; onRetry: () => void }) {
  return (
    <div className="flex flex-1 items-center justify-center px-6 py-10">
      <div className="flex max-w-sm flex-col items-center text-center">
        <p className="text-sm text-danger-fg">{message}</p>
        <Button variant="outline" size="sm" className="mt-4 gap-1.5" onClick={onRetry}>
          <RotateCw className="size-4" />
          Try again
        </Button>
      </div>
    </div>
  )
}

function IconButton({
  label,
  icon: Icon,
  onClick,
}: {
  label: string
  icon: React.ElementType
  onClick?: () => void
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      aria-label={label}
      title={label}
      className="grid size-7 place-items-center rounded-sm text-fg/70 transition-colors hover:bg-surface-hover hover:text-fg"
    >
      <Icon className="size-3.5" />
    </button>
  )
}

function filterByGroup(items: Service[], filter: GroupFilter): Service[] {
  if (filter === "all") return items
  if (filter === "group") return items.filter((s) => s.group_settings?.allow_group_sessions)
  return items.filter((s) => !s.group_settings?.allow_group_sessions)
}
