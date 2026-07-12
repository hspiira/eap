import { useEffect, useState } from "react"

import { createFileRoute, Link, useNavigate, useSearch } from "@tanstack/react-router"
import {
  Calendar,
  Download,
  ExternalLink,
  FileSignature,
  MoreHorizontal,
  Plus,
  RotateCw,
} from "lucide-react"

import { contractsApi } from "@/api/endpoints/contracts"
import { EmptyState } from "@/components/common/EmptyState"
import {
  FilterBar,
  FilterButton,
  FilterChip,
  FilterSearch,
  FilterTrigger,
} from "@/components/common/FilterBar"
import { PageShell } from "@/components/common/PageShell"
import { TableSkeleton } from "@/components/common/PageSkeletons"
import { SelectionBar } from "@/components/common/SelectionBar"
import { nextSort, SortHeader, type SortState } from "@/components/common/SortHeader"
import { StatusBadge } from "@/components/common/StatusBadge"
import { ContractFormSheet } from "@/components/ContractFormSheet"
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
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"
import { useCanWrite } from "@/hooks/useCanWrite"
import { useDebouncedValue } from "@/hooks/useDebouncedValue"
import { useTableSelection } from "@/hooks/useTableSelection"
import { normalizeErrorMessage } from "@/lib/errors"
import { useEntityList } from "@/lib/queries"
import type { Contract } from "@/types/entities"
import { ContractStatus } from "@/types/enums"

function isStatus(value: unknown): value is ContractStatus {
  return (
    value === ContractStatus.ACTIVE ||
    value === ContractStatus.PENDING ||
    value === ContractStatus.DRAFT ||
    value === ContractStatus.EXPIRED ||
    value === ContractStatus.RENEWED ||
    value === ContractStatus.TERMINATED
  )
}

export const Route = createFileRoute("/contracts/")({
  component: ContractsListPage,
  validateSearch: (search: Record<string, unknown>) => {
    const out: { new?: boolean; search?: string; status?: ContractStatus } = {}
    if (search.new === "1" || search.new === true) out.new = true
    if (typeof search.search === "string" && search.search.trim()) out.search = search.search
    if (isStatus(search.status)) out.status = search.status
    return out
  },
})

const STATUS_OPTIONS = [
  { value: "all", label: "All statuses" },
  { value: ContractStatus.ACTIVE, label: "Active" },
  { value: ContractStatus.PENDING, label: "Pending" },
  { value: ContractStatus.DRAFT, label: "Draft" },
  { value: ContractStatus.EXPIRED, label: "Expired" },
  { value: ContractStatus.RENEWED, label: "Renewed" },
  { value: ContractStatus.TERMINATED, label: "Terminated" },
] as const

const RENEWAL_OPTIONS = [
  { value: "all", label: "All renewal windows" },
  { value: "30d", label: "Renews in 30 days" },
  { value: "90d", label: "Renews in 90 days" },
  { value: "expired", label: "Already expired" },
] as const

type StatusFilter = (typeof STATUS_OPTIONS)[number]["value"]
type RenewalFilter = (typeof RENEWAL_OPTIONS)[number]["value"]

const ROW_BORDER = "border-fg/8"

function ContractsListPage() {
  const searchParams = useSearch({ from: "/contracts/" })
  const navigate = useNavigate({ from: "/contracts/" })
  const [searchInput, setSearchInput] = useState(searchParams.search ?? "")
  const [renewal, setRenewal] = useState<RenewalFilter>("all")
  const [addOpen, setAddOpen] = useState(false)
  const [page, setPage] = useState(1)
  const [sort, setSort] = useState<SortState>({ field: undefined, desc: false })
  const canWrite = useCanWrite()
  const limit = 20
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
    resource: "contracts",
    params: {
      page,
      limit,
      search: activeSearch,
      status: activeStatus,
      sort_by: sort.field,
      sort_desc: sort.field ? sort.desc : undefined,
    },
    listFn: contractsApi.list,
  })
  const allItems = query.data?.items ?? []
  const items = filterByRenewal(allItems, renewal)
  const total = query.data?.total ?? 0
  const selection = useTableSelection(items)
  const loading = query.isPending
  const error = query.isError ? normalizeErrorMessage(query.error, "Failed to load data") : null
  const hasFilters = Boolean(activeSearch) || Boolean(activeStatus) || renewal !== "all"

  return (
    <PageShell
      icon={FileSignature}
      breadcrumb="Commercial · Contracts"
      actions={
        <>
          <IconButton label="Export" icon={Download} />
          <span className="mx-1 h-4 w-px bg-fg/15" aria-hidden />
          {canWrite && (
            <Button size="sm" className="h-7 gap-1.5 px-2.5" onClick={() => setAddOpen(true)}>
              <Plus className="size-3.5" />
              Add contract
            </Button>
          )}
        </>
      }
    >
      <FilterBar>
        <FilterButton
          options={[
            { id: "status", label: "Status" },
            { id: "renewal", label: "Renewal window" },
            { id: "client", label: "Client" },
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
          icon={Calendar}
          label="Renewal window"
          value={renewal}
          options={RENEWAL_OPTIONS}
          onChange={setRenewal}
        />
        <div className="ml-auto" />
        <FilterSearch
          value={searchInput}
          onChange={setSearchInput}
          placeholder="Search contracts…"
        />
      </FilterBar>

      <ContractFormSheet open={addOpen} onOpenChange={setAddOpen} />

      <div className="flex min-h-0 flex-1 flex-col bg-bg">
        {loading ? (
          <div className="flex-1 overflow-auto p-5">
            <TableSkeleton cols={6} />
          </div>
        ) : error ? (
          <ErrorState message={error} onRetry={() => void query.refetch()} />
        ) : items.length === 0 ? (
          <EmptyState
            icon={FileSignature}
            title={hasFilters ? "No contracts match your filters" : "No contracts yet"}
            description={
              hasFilters
                ? "Try a different search or clear filters."
                : "Add your first contract to start tracking lifecycle and billing."
            }
            action={
              hasFilters || !canWrite ? null : (
                <Button size="sm" className="gap-1.5" onClick={() => setAddOpen(true)}>
                  <Plus className="size-4" />
                  Add contract
                </Button>
              )
            }
          />
        ) : (
          <>
            <SelectionBar count={selection.selectedIds.size} onClear={selection.clearSelection} />
            <div className="relative min-h-0 flex-1 overflow-auto">
              <Table className="w-full caption-bottom text-sm">
                <TableHeader className="sticky top-0 z-10 border-b-0 bg-surface shadow-[inset_0_-1px_0_rgb(0_0_0/0.08)]">
                  <TableRow className={`hover:bg-transparent ${ROW_BORDER}`}>
                    <TableHead className="w-10 px-3">
                      <Checkbox
                        aria-label="Select all"
                        checked={selection.selectAllState}
                        onCheckedChange={selection.toggleSelectAll}
                      />
                    </TableHead>
                    <TableHead>
                      <SortHeader field="contract_number" sort={sort} onToggle={toggleSort}>
                        Number
                      </SortHeader>
                    </TableHead>
                    <TableHead>
                      <SortHeader field="client_id" sort={sort} onToggle={toggleSort}>
                        Client
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
                        End / Renewal
                      </SortHeader>
                    </TableHead>
                    <TableHead className="text-fg/65">Billing</TableHead>
                    <TableHead className="w-16 text-right text-fg/65">
                      <span className="sr-only">Actions</span>
                    </TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {items.map((row) => (
                    <ContractRow
                      key={row.id}
                      row={row}
                      isSelected={selection.selectedIds.has(row.id)}
                      onToggle={() => selection.toggleSelect(row.id)}
                    />
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

function ContractRow({ row, isSelected, onToggle }: { row: Contract; isSelected: boolean; onToggle: () => void }) {
  const number = row.contract_number ?? row.id.slice(0, 8)
  const billing = formatBilling(row)
  const ending = row.renewal_date ?? row.end_date ?? null
  return (
    <TableRow className={`group cursor-default ${ROW_BORDER}`}>
      <TableCell className="px-3">
        <Checkbox aria-label={`Select ${number}`} checked={isSelected} onCheckedChange={onToggle} />
      </TableCell>
      <TableCell>
        <Link
          to="/contracts/$contractId"
          params={{ contractId: row.id }}
          className="flex items-center gap-2.5"
        >
          <span
            aria-hidden
            className="grid size-6 shrink-0 place-items-center bg-primary/10 font-mono text-[10px] font-semibold text-primary"
          >
            <FileSignature className="size-3" />
          </span>
          <span className="font-mono text-sm font-medium text-fg group-hover:text-primary">
            {number}
          </span>
        </Link>
      </TableCell>
      <TableCell>
        <Link
          to="/clients/$clientId"
          params={{ clientId: row.client_id }}
          className="text-sm text-fg hover:text-primary"
        >
          {row.client_id.slice(0, 8)}
        </Link>
      </TableCell>
      <TableCell>
        <StatusBadge status={row.status} />
      </TableCell>
      <TableCell className="text-sm text-fg/75">{row.start_date}</TableCell>
      <TableCell>
        {ending ? (
          <span className="block min-w-0">
            <span className="block truncate text-sm text-fg">{ending}</span>
            <span className="block truncate text-xs text-fg/55">
              {row.renewal_date ? "Renewal" : "End"}
            </span>
          </span>
        ) : (
          <span className="text-fg/40">—</span>
        )}
      </TableCell>
      <TableCell>
        {billing ? (
          <span className="block min-w-0">
            <span className="block truncate font-mono text-sm text-fg">{billing.amount}</span>
            <span className="block truncate text-xs text-fg/55">{billing.frequency}</span>
          </span>
        ) : (
          <span className="text-fg/40">—</span>
        )}
      </TableCell>
      <TableCell className="text-right">
        <div className="flex items-center justify-end gap-0.5 opacity-0 transition-opacity group-hover:opacity-100 focus-within:opacity-100">
          <Link
            to="/contracts/$contractId"
            params={{ contractId: row.id }}
            aria-label={`Open ${number}`}
            className="grid size-7 place-items-center rounded-sm text-fg/65 hover:bg-surface-hover hover:text-fg"
          >
            <ExternalLink className="size-3.5" />
          </Link>
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button type="button" variant="ghost" size="sm" aria-label={`More actions for ${number}`} className="size-7 p-0 text-fg/65"><MoreHorizontal className="size-4" /></Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end">
              <DropdownMenuItem asChild>
                <Link to="/contracts/$contractId" params={{ contractId: row.id }}>
                  View details
                </Link>
              </DropdownMenuItem>
              <DropdownMenuItem asChild>
                <Link to="/clients/$clientId" params={{ clientId: row.client_id }}>
                  View client
                </Link>
              </DropdownMenuItem>
              <DropdownMenuSeparator />
              <DropdownMenuItem className="text-destructive focus:text-destructive">
                Terminate
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

function filterByRenewal(items: Contract[], window: RenewalFilter): Contract[] {
  if (window === "all") return items
  const now = new Date()
  if (window === "expired") {
    return items.filter((c) => {
      const end = c.end_date ? new Date(c.end_date) : null
      return end ? end < now : false
    })
  }
  const days = window === "30d" ? 30 : 90
  const horizon = new Date(now.getTime() + days * 24 * 60 * 60 * 1000)
  return items.filter((c) => {
    const target = c.renewal_date ?? c.end_date
    if (!target) return false
    const d = new Date(target)
    return d >= now && d <= horizon
  })
}

function formatBilling(c: Contract): { amount: string; frequency: string } | null {
  if (c.billing_amount == null && !c.billing_frequency) return null
  const amount =
    c.billing_amount != null
      ? `${c.currency ?? ""} ${c.billing_amount.toLocaleString()}`.trim()
      : "—"
  const frequency = c.billing_frequency ?? "—"
  return { amount, frequency }
}
