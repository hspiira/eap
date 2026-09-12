import { useMemo } from "react"

import { useQuery } from "@tanstack/react-query"
import { createFileRoute, Link, useNavigate, useSearch } from "@tanstack/react-router"
import { Calendar, Download, ExternalLink, FileSignature, MoreHorizontal, Plus } from "lucide-react"

import { clientsApi } from "@/api/endpoints/clients"
import { type ContractListParams, contractsApi } from "@/api/endpoints/contracts"
import { EmptyState } from "@/components/common/EmptyState"
import { ErrorState } from "@/components/common/ErrorState"
import { FilterBar, FilterChip, FilterSearch, FilterTrigger } from "@/components/common/FilterBar"
import { IconButton } from "@/components/common/IconButton"
import { PageShell } from "@/components/common/PageShell"
import { TableSkeleton } from "@/components/common/PageSkeletons"
import { SortHeader } from "@/components/common/SortHeader"
import { StatusBadge } from "@/components/common/StatusBadge"
import { STICKY_TABLE_HEAD } from "@/components/common/tableStyles"
import { ContractFormSheet } from "@/components/ContractFormSheet"
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
} from "@/components/ui/table"
import { useCanWrite } from "@/hooks/useCanWrite"
import { NEWEST_FIRST, useListPage } from "@/hooks/useListPage"
import { termLabel, termTone } from "@/lib/contract-term"
import { contractValue } from "@/lib/display"
import { normalizeErrorMessage } from "@/lib/errors"
import { formatDay } from "@/lib/format"
import { useEntityList } from "@/lib/queries"
import { enumParam, listSearchSchema } from "@/lib/search-params"
import { cn } from "@/lib/utils"
import type { Client, Contract } from "@/types/entities"
import { ContractStatus } from "@/types/enums"

export const Route = createFileRoute("/contracts/")({
  component: ContractsListPage,
  validateSearch: listSearchSchema({
    client_id: (v) => (typeof v === "string" && v.trim() ? v : undefined),
    status: enumParam(ContractStatus),
    renewal: (v): Exclude<RenewalFilter, "all"> | undefined =>
      v === "30d" || v === "90d" || v === "expired" ? v : undefined,
  }),
})

/**
 * The clients endpoint caps limit at 100 (`pagination()` defaults in
 * app/api/dependencies/pagination.py). Asking for more 422s, which left the
 * lookup empty and every row reading "Unknown client".
 */
const CLIENT_LOOKUP_LIMIT = 100

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
  const canWrite = useCanWrite()

  const activeStatus = searchParams.status
  const activeClientId = searchParams.client_id
  const activeRenewal: RenewalFilter = searchParams.renewal ?? "all"

  // Anchored to the selected window, not to render: an inline `new Date()` would
  // mint a fresh query key every render and refetch in a loop.
  const renewalWindow = useMemo(() => renewalParams(activeRenewal, new Date()), [activeRenewal])

  const handleStatusChange = (next: StatusFilter) => {
    const status = next === "all" ? undefined : next
    setFilter("status", status)
  }

  const handleRenewalChange = (next: RenewalFilter) => {
    const renewal = next === "all" ? undefined : next
    setFilter("renewal", renewal)
  }

  const { data: clientsData } = useQuery({
    queryKey: ["clients", "lookup"],
    queryFn: () => clientsApi.list({ limit: CLIENT_LOOKUP_LIMIT }),
    staleTime: 5 * 60_000,
  })
  const clientsById = useMemo(() => {
    const m = new Map<string, Client>()
    for (const c of clientsData?.items ?? []) m.set(c.id, c)
    return m
  }, [clientsData])

  const query = useEntityList<Contract, ContractListParams>({
    resource: "contracts",
    params: {
      page,
      limit,
      search: activeSearch,
      client_id: activeClientId,
      status: activeStatus,
      ...renewalWindow,
      ...sortParams,
    },
    listFn: contractsApi.list,
  })
  const items = query.data?.items ?? []
  const total = query.data?.total ?? 0
  const loading = query.isPending
  const error = query.isError ? normalizeErrorMessage(query.error, "Failed to load data") : null
  const hasFilters =
    Boolean(activeSearch) ||
    Boolean(activeClientId) ||
    Boolean(activeStatus) ||
    activeRenewal !== "all"

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
        {activeClientId ? (
          <FilterChip
            label={`Client ${activeClientId.slice(0, 8)}`}
            onRemove={() => setFilter("client_id", undefined)}
          />
        ) : null}
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
          value={activeRenewal}
          options={RENEWAL_OPTIONS}
          onChange={handleRenewalChange}
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
            <TableSkeleton cols={9} />
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
            <div
              className="relative min-h-0 flex-1 overflow-auto"
              data-scroll-restoration-id="list"
            >
              <Table className="w-full caption-bottom text-sm" scrollable={false}>
                <TableHeader className={STICKY_TABLE_HEAD}>
                  <TableRow className={`hover:bg-transparent ${ROW_BORDER}`}>
                    <TableHead className="text-fg/65">Client</TableHead>
                    <TableHead className="text-center">
                      <SortHeader field="status" sort={sort} onToggle={toggleSort}>
                        <span className="sr-only">Status</span>
                      </SortHeader>
                    </TableHead>
                    <TableHead className="text-center">
                      <SortHeader field="payment_status" sort={sort} onToggle={toggleSort}>
                        Payment
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
                    <TableHead className="text-fg/65">Renewal</TableHead>
                    <TableHead className="text-right text-fg/65">Amount</TableHead>
                    <TableHead className="text-fg/65">Frequency</TableHead>
                    <TableHead className="w-16 text-right text-fg/65">
                      <span className="sr-only">Actions</span>
                    </TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {items.map((row) => (
                    <ContractRow key={row.id} row={row} clientsById={clientsById} />
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

function ContractRow({ row, clientsById }: { row: Contract; clientsById: Map<string, Client> }) {
  const billing = formatBilling(row)
  const clientName = clientsById.get(row.client_id)?.name ?? "Unknown client"
  return (
    <TableRow className={`group h-9 cursor-default ${ROW_BORDER}`}>
      <TableCell className="max-w-[16rem]">
        <Link
          to="/contracts/$contractId"
          params={{ contractId: row.id }}
          className="flex items-center gap-2.5"
        >
          <span
            aria-hidden
            className="grid size-6 shrink-0 place-items-center bg-fg/6 text-fg-muted"
          >
            <FileSignature className="size-3" />
          </span>
          <span className="truncate text-sm font-medium text-fg group-hover:text-primary">
            {clientName}
          </span>
        </Link>
      </TableCell>
      <TableCell className="text-center">
        <StatusBadge status={row.status} iconOnly />
      </TableCell>
      <TableCell className="text-center">
        <StatusBadge status={row.payment_status} iconOnly />
      </TableCell>
      <TableCell className="whitespace-nowrap text-xs text-fg/70">
        {formatDay(row.period.start_date)}
      </TableCell>
      <TableCell className="whitespace-nowrap text-xs text-fg/70">
        {formatDay(row.period.end_date)}
      </TableCell>
      <TableCell className={cn("whitespace-nowrap text-xs", termTone(row))}>
        {termLabel(row)}
      </TableCell>
      <TableCell className="whitespace-nowrap text-right tabular-nums text-xs text-fg">
        {billing.amount}
      </TableCell>
      <TableCell className="whitespace-nowrap text-xs text-fg/70">{billing.frequency}</TableCell>
      <TableCell className="text-right">
        <div className="flex items-center justify-end gap-0.5 opacity-0 transition-opacity group-hover:opacity-100 focus-within:opacity-100">
          <Link
            to="/contracts/$contractId"
            params={{ contractId: row.id }}
            aria-label={`Open the ${clientName} contract`}
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
                aria-label={`More actions for the ${clientName} contract`}
                className="size-7 p-0 text-fg/65"
              >
                <MoreHorizontal className="size-4" />
              </Button>
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

/**
 * Maps the renewal dropdown onto server-side params.
 *
 * This replaces a client-side filter that could never match: it keyed on
 * `renewal_date ?? end_date`, and the BE sends neither at the top level, so
 * every window returned an empty list. The term now lives in `period`, and the
 * server filters it via an indexed range on the term end.
 *
 * "Renews in N days" means an auto-renewing contract whose term ends inside the
 * window: a contract ending then without auto-renew is expiring, not renewing.
 * "Already expired" is any term that has ended, renewing or not.
 *
 * Bounds are computed here rather than named to the server because the window is
 * relative to the viewer's clock.
 */
export function renewalParams(
  window: RenewalFilter,
  now: Date,
): Pick<ContractListParams, "ends_from" | "ends_to" | "is_auto_renew"> {
  if (window === "all") return {}
  if (window === "expired") return { ends_to: now.toISOString() }
  const days = window === "30d" ? 30 : 90
  return {
    is_auto_renew: true,
    ends_from: now.toISOString(),
    ends_to: new Date(now.getTime() + days * 86_400_000).toISOString(),
  }
}

function formatBilling(c: Contract): { amount: string; frequency: string } {
  return { amount: contractValue(c), frequency: c.payment_frequency }
}
