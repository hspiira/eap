import { useEffect, useState } from "react"


import { createFileRoute, Link, useNavigate, useSearch } from "@tanstack/react-router"
import {
  Download,
  ExternalLink,
  FileCheck,
  MoreHorizontal,
  Plus,
  RotateCw,
} from "lucide-react"

import { serviceAssignmentsApi } from "@/api/endpoints/service-assignments"
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
import { ServiceAssignmentFormSheet } from "@/components/ServiceAssignmentFormSheet"
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
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
import { Checkbox } from "@/components/ui/checkbox"
} from "@/components/ui/table"
import { useDebouncedValue } from "@/hooks/useDebouncedValue"
import { useEntityList } from "@/lib/queries"
import type { ServiceAssignment } from "@/types/entities"
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

export const Route = createFileRoute("/service-assignments/")({
  component: ServiceAssignmentsListPage,
  validateSearch: (search: Record<string, unknown>) => {
    const out: {
      new?: boolean
      search?: string
      status?: BaseStatus
      contract_id?: string
    } = {}
    if (search.new === "1" || search.new === true) out.new = true
    if (typeof search.search === "string" && search.search.trim()) out.search = search.search
    if (isStatus(search.status)) out.status = search.status
    if (typeof search.contract_id === "string" && search.contract_id.trim()) {
      out.contract_id = search.contract_id
    }
    return out
  },
})

const STATUS_OPTIONS = [
  { value: "all", label: "All statuses" },
  { value: BaseStatus.ACTIVE, label: "Active" },
  { value: BaseStatus.PENDING, label: "Pending" },
  { value: BaseStatus.INACTIVE, label: "Inactive" },
  { value: BaseStatus.ARCHIVED, label: "Archived" },
] as const

type StatusFilter = (typeof STATUS_OPTIONS)[number]["value"]

const ROW_BORDER = "border-fg/8"

function ServiceAssignmentsListPage() {
  const searchParams = useSearch({ from: "/service-assignments/" })
  const navigate = useNavigate({ from: "/service-assignments/" })
  const [searchInput, setSearchInput] = useState(searchParams.search ?? "")
  const [addOpen, setAddOpen] = useState(false)
  const [page, setPage] = useState(1)
  const [sort, setSort] = useState<SortState>({ field: undefined, desc: false })
  const limit = 20
  const toggleSort = (field: string) => {
    setSort((prev) => nextSort(prev, field))
    setPage(1)
  }

  const debouncedSearch = useDebouncedValue(searchInput.trim(), 300)
  const activeSearch = debouncedSearch || undefined
  const activeStatus = searchParams.status
  const activeContractId = searchParams.contract_id

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

  const clearContract = () => {
    navigate({ search: (prev) => ({ ...prev, contract_id: undefined }), replace: true })
    setPage(1)
  }

  const query = useEntityList({
    resource: "service-assignments",
    params: {
      page,
      limit,
      search: activeSearch,
      contract_id: activeContractId,
      status: activeStatus,
      sort_by: sort.field,
      sort_desc: sort.field ? sort.desc : undefined,
    },
    listFn: serviceAssignmentsApi.list,
  })
  const items = query.data?.items ?? []
  const total = query.data?.total ?? 0
  const loading = query.isPending
  const error = query.isError
    ? normalizeErrorMessage(query.error, "Failed to load data")
    : null
  const hasFilters =
    Boolean(activeSearch) || Boolean(activeStatus) || Boolean(activeContractId)

  return (
    <PageShell
      icon={FileCheck}
      breadcrumb="Commercial · Service Assignments"
      actions={
        <>
          <IconButton label="Refresh" onClick={() => void query.refetch()} icon={RotateCw} />
          <IconButton label="Export" icon={Download} />
          <span className="mx-1 h-4 w-px bg-fg/15" aria-hidden />
          <Button size="sm" className="h-7 gap-1.5 px-2.5" onClick={() => setAddOpen(true)}>
            <Plus className="size-3.5" />
            Add assignment
          </Button>
        </>
      }
    >
      <FilterBar>
        <FilterButton
          options={[
            { id: "status", label: "Status" },
            { id: "contract", label: "Contract" },
            { id: "service", label: "Service" },
          ]}
        />
        {activeStatus ? (
          <FilterChip
            label={`Status is ${activeStatus}`}
            onRemove={() => handleStatusChange("all")}
          />
        ) : null}
        {activeContractId ? (
          <FilterChip
            label={`Contract ${activeContractId.slice(0, 8)}`}
            onRemove={clearContract}
          />
        ) : null}
        <FilterTrigger
          label="All statuses"
          value={(activeStatus ?? "all") as StatusFilter}
          options={STATUS_OPTIONS}
          onChange={handleStatusChange}
        />
        <div className="ml-auto" />
        <FilterSearch
          value={searchInput}
          onChange={setSearchInput}
          placeholder="Search assignments…"
        />
      </FilterBar>

      <ServiceAssignmentFormSheet
        open={addOpen}
        onOpenChange={setAddOpen}
        contractId={activeContractId}
      />

      <div className="flex min-h-0 flex-1 flex-col bg-bg">
        {loading ? (
          <div className="flex-1 overflow-auto p-5">
            <TableSkeleton cols={5} />
          </div>
        ) : error ? (
          <ErrorState message={error} onRetry={() => void query.refetch()} />
        ) : items.length === 0 ? (
          <EmptyState
            icon={FileCheck}
            title={
              hasFilters ? "No assignments match your filters" : "No service assignments yet"
            }
            description={
              hasFilters
                ? "Try a different search or clear filters."
                : "Link a service to a contract so sessions can be billed against it."
            }
            action={
              hasFilters ? null : (
                <Button size="sm" className="gap-1.5" onClick={() => setAddOpen(true)}>
                  <Plus className="size-4" />
                  Add assignment
                </Button>
              )
            }
          />
        ) : (
          <>
            <div className="relative min-h-0 flex-1 overflow-auto">
              <Table className="w-full caption-bottom text-sm">
                <TableHeader className="sticky top-0 z-10 border-b-0 bg-surface shadow-[inset_0_-1px_0_rgb(0_0_0/0.08)]">
                  <TableRow className={`hover:bg-transparent ${ROW_BORDER}`}>
                    <TableHead className="w-10 px-3">
                      <Checkbox aria-label="Select all" />
                    </TableHead>
                    <TableHead>
                      <SortHeader field="contract_id" sort={sort} onToggle={toggleSort}>
                        Contract
                      </SortHeader>
                    </TableHead>
                    <TableHead>
                      <SortHeader field="service_id" sort={sort} onToggle={toggleSort}>
                        Service
                      </SortHeader>
                    </TableHead>
                    <TableHead>
                      <SortHeader field="status" sort={sort} onToggle={toggleSort}>
                        Status
                      </SortHeader>
                    </TableHead>
                    <TableHead>
                      <SortHeader field="start_date" sort={sort} onToggle={toggleSort}>
                        Start
                      </SortHeader>
                    </TableHead>
                    <TableHead>
                      <SortHeader field="end_date" sort={sort} onToggle={toggleSort}>
                        End
                      </SortHeader>
                    </TableHead>
                    <TableHead className="w-16 text-right text-fg/65">
                      <span className="sr-only">Actions</span>
                    </TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {items.map((row) => (
                    <AssignmentRow key={row.id} row={row} />
                  ))}
                </TableBody>
              </Table>
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

function AssignmentRow({ row }: { row: ServiceAssignment }) {
  return (
    <TableRow className={`group cursor-default ${ROW_BORDER}`}>
      <TableCell className="px-3">
        <Checkbox aria-label={`Select ${row.id}`} onClick={(e) => e.stopPropagation()} />
      </TableCell>
      <TableCell>
        <Link
          to="/contracts/$contractId"
          params={{ contractId: row.contract_id }}
          className="flex items-center gap-2.5"
        >
          <span
            aria-hidden
            className="grid size-6 shrink-0 place-items-center bg-primary/10 font-mono text-[10px] font-semibold text-primary"
          >
            CT
          </span>
          <span className="font-mono text-sm text-fg group-hover:text-primary">
            {row.contract_id.slice(0, 8)}
          </span>
        </Link>
      </TableCell>
      <TableCell>
        <Link to="/services" className="font-mono text-sm text-fg hover:text-primary">
          {row.service_id.slice(0, 8)}
        </Link>
      </TableCell>
      <TableCell>
        <StatusBadge status={row.status} />
      </TableCell>
      <TableCell className="text-sm text-fg/75">{row.start_date ?? "—"}</TableCell>
      <TableCell className="text-sm text-fg/75">{row.end_date ?? "—"}</TableCell>
      <TableCell className="text-right">
        <div className="flex items-center justify-end gap-0.5 opacity-0 transition-opacity group-hover:opacity-100 focus-within:opacity-100">
          <Link
            to="/service-assignments/$assignmentId"
            params={{ assignmentId: row.id }}
            aria-label={`Open assignment ${row.id.slice(0, 8)}`}
            className="grid size-7 place-items-center rounded-sm text-fg/65 hover:bg-surface-hover hover:text-fg"
          >
            <ExternalLink className="size-3.5" />
          </Link>
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button type="button" variant="ghost" size="sm" aria-label={`More actions for assignment ${row.id.slice(0, 8)}`} className="size-7 p-0 text-fg/65"><MoreHorizontal className="size-4" /></Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end">
              <DropdownMenuItem asChild>
                <Link
                  to="/service-assignments/$assignmentId"
                  params={{ assignmentId: row.id }}
                >
                  View details
                </Link>
              </DropdownMenuItem>
              <DropdownMenuItem asChild>
                <Link to="/contracts/$contractId" params={{ contractId: row.contract_id }}>
                  View contract
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
    <Button
      type="button"
      variant="ghost"
      size="sm"
      onClick={onClick}
      aria-label={label}
      title={label}
      className="size-7 p-0 text-fg/70"
    >
      <Icon className="size-3.5" />
    </Button>
  )
}
