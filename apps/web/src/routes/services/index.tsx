import { createFileRoute, Link, useNavigate, useSearch } from "@tanstack/react-router"
import { Download, ExternalLink, MoreHorizontal, Plus, Wrench } from "lucide-react"

import { type ServiceListParams, servicesApi } from "@/api/endpoints/services"
import { EmptyState } from "@/components/common/EmptyState"
import { ErrorState } from "@/components/common/ErrorState"
import { FilterBar, FilterChip, FilterSearch, FilterTrigger } from "@/components/common/FilterBar"
import { IconButton } from "@/components/common/IconButton"
import { InfiniteScrollSentinel } from "@/components/common/InfiniteScrollSentinel"
import { PagedTableBody } from "@/components/common/PagedTableBody"
import { PageShell } from "@/components/common/PageShell"
import { TableSkeleton } from "@/components/common/PageSkeletons"
import { SortHeader } from "@/components/common/SortHeader"
import { StatusBadge } from "@/components/common/StatusBadge"
import { STICKY_TABLE_HEAD } from "@/components/common/tableStyles"
import { CATEGORY_LABELS, ServiceFormSheet } from "@/components/ServiceFormSheet"
import { Button } from "@/components/ui/button"
import { Checkbox } from "@/components/ui/checkbox"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"
import { Pagination } from "@/components/ui/pagination"
import { Table, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import { NEWEST_FIRST, useListPage } from "@/hooks/useListPage"
import { useVisiblePage } from "@/hooks/useVisiblePage"
import { normalizeErrorMessage } from "@/lib/errors"
import { useEntityListPages } from "@/lib/queries"
import { listSearchSchema } from "@/lib/search-params"
import type { Service } from "@/types/entities"
import { BaseStatus } from "@/types/enums"

const SERVICE_STATUSES: ReadonlyArray<BaseStatus> = [
  BaseStatus.ACTIVE,
  BaseStatus.INACTIVE,
  BaseStatus.PENDING,
  BaseStatus.ARCHIVED,
]

export const Route = createFileRoute("/services/")({
  component: ServicesListPage,
  validateSearch: listSearchSchema({
    status: (v) => (SERVICE_STATUSES.includes(v as BaseStatus) ? (v as BaseStatus) : undefined),
    group: (v): "individual" | "group" | undefined =>
      v === "individual" || v === "group" ? v : undefined,
  }),
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
  const {
    searchInput,
    setSearchInput,
    activeSearch,
    addOpen,
    setAddOpen,
    page,
    setPage,
    limit,
    sort,
    toggleSort,
    setFilter,
    sortParams,
  } = useListPage({
    searchParams,
    navigate,
    initialSort: NEWEST_FIRST,
  })

  const activeStatus = searchParams.status
  const activeGroup: GroupFilter = searchParams.group ?? "all"

  const handleStatusChange = (next: StatusFilter) =>
    setFilter("status", next === "all" ? undefined : next)

  const handleGroupChange = (next: GroupFilter) =>
    setFilter("group", next === "all" ? undefined : next)

  const [visiblePage, setVisiblePage] = useVisiblePage(page)

  const query = useEntityListPages<Service, ServiceListParams>({
    resource: "services",
    params: {
      page,
      limit,
      search: activeSearch,
      status: activeStatus,
      is_group_service: activeGroup === "all" ? undefined : activeGroup === "group",
      ...sortParams,
    },
    listFn: servicesApi.list,
  })
  const items = query.data?.items ?? []
  const total = query.data?.total ?? 0
  const loading = query.isPending
  const error = query.isError ? normalizeErrorMessage(query.error, "Failed to load data") : null
  const hasFilters = Boolean(activeSearch) || Boolean(activeStatus) || activeGroup !== "all"

  return (
    <PageShell
      icon={Wrench}
      breadcrumb="Catalog · Services"
      actions={
        <>
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
          value={activeGroup}
          options={GROUP_OPTIONS}
          onChange={handleGroupChange}
        />
        <div className="ml-auto" />
        <FilterSearch
          value={searchInput}
          onChange={setSearchInput}
          placeholder="Search services…"
        />
      </FilterBar>

      <ServiceFormSheet open={addOpen} onOpenChange={setAddOpen} />

      <div className="flex min-h-0 flex-1 flex-col bg-bg">
        {loading ? (
          <div className="flex-1 overflow-auto p-5">
            <TableSkeleton cols={5} />
          </div>
        ) : error ? (
          <ErrorState message={error} onRetry={() => void query.refetch()} />
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
            <div
              className="relative min-h-0 flex-1 overflow-auto"
              data-scroll-restoration-id="list"
            >
              <Table className="w-full caption-bottom text-sm" scrollable={false}>
                <TableHeader className={STICKY_TABLE_HEAD}>
                  <TableRow className={`hover:bg-transparent ${ROW_BORDER}`}>
                    <TableHead className="w-10 px-3">
                      <Checkbox aria-label="Select all" />
                    </TableHead>
                    <TableHead>
                      <SortHeader field="name" sort={sort} onToggle={toggleSort}>
                        Service
                      </SortHeader>
                    </TableHead>
                    <TableHead>
                      <SortHeader field="category" sort={sort} onToggle={toggleSort}>
                        Category
                      </SortHeader>
                    </TableHead>
                    <TableHead className="text-center">
                      <SortHeader field="status" sort={sort} onToggle={toggleSort}>
                        <span className="sr-only">Status</span>
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
                <PagedTableBody
                  items={items}
                  anchorPage={page}
                  limit={limit}
                  rowKey={(row) => row.id}
                  renderRow={(row) => <ServiceRow row={row} />}
                  onVisiblePageChange={setVisiblePage}
                />
              </Table>
              <InfiniteScrollSentinel
                onLoadMore={query.loadMore}
                hasMore={query.hasMore}
                loadingMore={query.loadingMore}
              />
            </div>
            {total > 0 && (
              <div className="shrink-0 border-t border-fg/10 bg-surface px-3 py-2">
                <Pagination
                  page={visiblePage}
                  total={total}
                  limit={limit}
                  shownCount={items.length}
                  onPageChange={setPage}
                />
              </div>
            )}
          </>
        )}
      </div>
    </PageShell>
  )
}

function ServiceRow({ row }: { row: Service }) {
  const allowGroup = Boolean(row.is_group_service)
  return (
    <TableRow className={`group cursor-default ${ROW_BORDER}`}>
      <TableCell className="px-3">
        <Checkbox aria-label={`Select ${row.name}`} onClick={(e) => e.stopPropagation()} />
      </TableCell>
      <TableCell>
        <Link
          to="/services/$serviceId"
          params={{ serviceId: row.id }}
          className="flex items-center gap-2.5"
        >
          <span
            aria-hidden
            className="grid size-6 shrink-0 place-items-center bg-fg/6 text-fg-muted"
          >
            <Wrench className="size-3" />
          </span>
          <span className="block max-w-[40ch] truncate text-sm font-medium text-fg group-hover:text-primary">
            {row.name}
          </span>
        </Link>
      </TableCell>
      <TableCell>
        {row.category ? (
          <span className="inline-flex items-center rounded-sm border border-fg/15 bg-bg px-1.5 py-0.5 text-[11px] font-medium text-fg/75">
            {CATEGORY_LABELS[row.category]}
          </span>
        ) : (
          <span className="text-fg-subtle">-</span>
        )}
      </TableCell>
      <TableCell className="text-center">
        <StatusBadge status={row.status} iconOnly />
      </TableCell>
      <TableCell className="tabular-nums text-sm text-fg/75">
        {row.duration_minutes != null ? `${row.duration_minutes}m` : "-"}
      </TableCell>
      <TableCell>
        {allowGroup ? (
          <span className="text-xs text-fg">Group</span>
        ) : (
          <span className="text-xs text-fg-muted">Individual</span>
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
              <Button
                type="button"
                variant="ghost"
                size="sm"
                aria-label={`More actions for ${row.name}`}
                className="size-7 p-0 text-fg/65"
              >
                <MoreHorizontal className="size-4" />
              </Button>
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
