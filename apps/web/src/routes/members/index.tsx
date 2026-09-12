import { useCallback, useState } from "react"

import { useQuery, useQueryClient } from "@tanstack/react-query"
import { createFileRoute, Link, useNavigate, useSearch } from "@tanstack/react-router"
import {
  CirclePause,
  CirclePlay,
  CircleX,
  Download,
  ExternalLink,
  FileDown,
  FileUp,
  Merge,
  MoreHorizontal,
  Plus,
  ScanSearch,
  User,
  Users,
} from "lucide-react"

import { clientsApi } from "@/api/endpoints/clients"
import { type MemberDuplicateCandidate, membersApi } from "@/api/endpoints/members"
import { BulkAction } from "@/components/common/BulkAction"
import { EmptyState } from "@/components/common/EmptyState"
import { EntityListView, type ListColumn } from "@/components/common/EntityListView"
import { FilterBar, FilterChip, FilterSearch, FilterTrigger } from "@/components/common/FilterBar"
import { IconButton } from "@/components/common/IconButton"
import { PageShell } from "@/components/common/PageShell"
import { SelectionBar } from "@/components/common/SelectionBar"
import { StatusBadge } from "@/components/common/StatusBadge"
import { ROW_BORDER } from "@/components/common/tableStyles"
import { MemberFormSheet } from "@/components/MemberFormSheet"
import { MemberMergeDialog } from "@/components/MemberMergeDialog"
import { MemberImportDialog } from "@/components/members/MemberImportDialog"
import { Button } from "@/components/ui/button"
import { Checkbox } from "@/components/ui/checkbox"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"
import { TableCell, TableRow } from "@/components/ui/table"
import { useToast } from "@/contexts/ToastContext"
import { useCanWrite, useCurrentRole } from "@/hooks/useCanWrite"
import { NEWEST_FIRST, useListPage } from "@/hooks/useListPage"
import { useTableSelection } from "@/hooks/useTableSelection"
import { normalizeErrorMessage } from "@/lib/errors"
import { useEntityList } from "@/lib/queries"
import { enumParam, listSearchSchema } from "@/lib/search-params"
import type { Member, MemberStats } from "@/types/entities"
import { EligibilityStatus, MemberRelation } from "@/types/enums"
import { getStatusLabel } from "@/utils/statusColors"

export const Route = createFileRoute("/members/")({
  component: MembersListPage,
  validateSearch: listSearchSchema({
    relation: enumParam(MemberRelation),
    status: enumParam(EligibilityStatus),
    client_id: (value) => (typeof value === "string" && value.trim() ? value : undefined),
  }),
})

/**
 * Ranked by how much of the roster actually carries the field. Phone, personal
 * email and date of birth are filled on a handful of rows in a roster of
 * thousands, so they live on the member's own page instead of spending a column
 * on empty cells. Staff number earns one: it is the number an HR team quotes.
 */
const COLUMNS: ListColumn[] = [
  { header: "Member", sortField: "display_label" },
  {
    header: <span className="sr-only">Status</span>,
    sortField: "status",
    className: "text-center",
  },
  { header: "Member code", className: "text-fg/65" },
  { header: "Client", className: "text-fg/65" },
  { header: "Relationship", sortField: "relation", className: "text-fg/65" },
  { header: "Work email", className: "text-fg/65" },
  { header: "Phone", className: "text-fg/65" },
]

const RELATION_OPTIONS = [
  { value: "all", label: "All relationships" },
  { value: MemberRelation.EMPLOYEE, label: "Employees" },
  { value: MemberRelation.SPOUSE, label: "Spouses" },
  { value: MemberRelation.CHILD, label: "Children" },
  { value: MemberRelation.DOMESTIC_PARTNER, label: "Domestic partners" },
  { value: MemberRelation.DEPENDENT_OTHER, label: "Other beneficiaries" },
] as const

const STATUS_OPTIONS = [
  { value: "all", label: "All statuses" },
  { value: EligibilityStatus.ACTIVE, label: "Active" },
  { value: EligibilityStatus.SUSPENDED, label: "Suspended" },
  { value: EligibilityStatus.PENDING, label: "Pending" },
  { value: EligibilityStatus.TERMINATED, label: "Terminated" },
] as const

type RelationFilter = (typeof RELATION_OPTIONS)[number]["value"]
type StatusFilter = (typeof STATUS_OPTIONS)[number]["value"]

function MembersListPage() {
  const searchParams = useSearch({ from: "/members/" })
  const navigate = useNavigate({ from: "/members/" })
  const list = useListPage({
    searchParams,
    navigate,
    initialSort: NEWEST_FIRST,
  })
  const canWrite = useCanWrite()
  const queryClient = useQueryClient()
  const toast = useToast()
  const [editing, setEditing] = useState<Member | null>(null)
  const [mergeOpen, setMergeOpen] = useState(false)
  const [importOpen, setImportOpen] = useState(false)
  const [duplicatesOpen, setDuplicatesOpen] = useState(false)
  const role = useCurrentRole()
  const query = useEntityList({
    resource: "members",
    params: {
      page: list.page,
      limit: list.limit,
      search: list.activeSearch,
      relation: searchParams.relation,
      status: searchParams.status,
      client_id: searchParams.client_id,
      ...list.sortParams,
    },
    listFn: membersApi.list,
  })
  const duplicatesQuery = useQuery({
    queryKey: ["member-duplicates"],
    queryFn: membersApi.scanDuplicates,
    enabled: false,
  })
  const statsFilters = {
    search: list.activeSearch,
    relation: searchParams.relation,
    status: searchParams.status,
    client_id: searchParams.client_id,
  }
  const statsQuery = useQuery({
    queryKey: ["members", "stats", statsFilters],
    queryFn: () => membersApi.getStats(statsFilters),
  })
  const clientsQuery = useQuery({
    queryKey: ["clients", "roster-filter"],
    queryFn: () => clientsApi.list({ limit: 100 }),
  })
  const clientOptions = [
    { value: "all", label: "All clients" },
    ...(clientsQuery.data?.items ?? []).map((client) => ({
      value: client.id,
      label: client.name,
    })),
  ]
  const clientLabel =
    clientsQuery.data?.items.find((client) => client.id === searchParams.client_id)?.name ??
    searchParams.client_id
  const items = query.data?.items ?? []
  const selection = useTableSelection(items)
  const mergeMembers = items.filter((member) => selection.selectedIds.has(member.id))
  const mergePair = mergeMembers.length === 2 ? (mergeMembers as [Member, Member]) : null

  const download = useCallback(
    async (promise: Promise<Blob>, filename: string) => {
      try {
        const blob = await promise
        const url = URL.createObjectURL(blob)
        const anchor = document.createElement("a")
        anchor.href = url
        anchor.download = filename
        anchor.click()
        URL.revokeObjectURL(url)
      } catch (error) {
        toast.showError(normalizeErrorMessage(error, "Could not download members"))
      }
    },
    [toast],
  )

  const setRelation = (value: RelationFilter) => {
    list.setFilter("relation", value === "all" ? undefined : value)
  }
  const setStatus = (value: StatusFilter) => {
    list.setFilter("status", value === "all" ? undefined : value)
  }
  const scanDuplicates = () => {
    setDuplicatesOpen(true)
    void duplicatesQuery.refetch()
  }
  const hasFilters = Boolean(
    list.activeSearch || searchParams.relation || searchParams.status || searchParams.client_id,
  )
  const clearFilters = () => {
    list.setSearchInput("")
    navigate({ search: {}, replace: true })
  }

  return (
    <PageShell
      icon={Users}
      breadcrumb="Members"
      actions={
        <>
          <IconButton
            label="Export"
            icon={Download}
            onClick={() =>
              void download(
                membersApi.exportCsv({
                  search: list.activeSearch,
                  relation: searchParams.relation,
                  status: searchParams.status,
                  client_id: searchParams.client_id,
                }),
                "members.csv",
              )
            }
          />
          <IconButton
            label="Download import template"
            icon={FileDown}
            onClick={() =>
              void download(membersApi.getImportTemplate(), "members-import-template.csv")
            }
          />
          <IconButton label="Find duplicates" icon={ScanSearch} onClick={scanDuplicates} />
          {canWrite ? (
            <IconButton
              label="Import"
              icon={FileUp}
              emphasis="raised"
              onClick={() => setImportOpen(true)}
            />
          ) : null}
          {canWrite ? (
            <Button
              variant="primary"
              size="sm"
              className="h-7 gap-1.5 px-2.5"
              onClick={() => list.setAddOpen(true)}
            >
              <Plus className="size-3.5" />
              Add member
            </Button>
          ) : null}
        </>
      }
    >
      <FilterBar>
        {searchParams.client_id ? (
          <FilterChip
            label={`Client: ${clientLabel}`}
            onRemove={() => list.setFilter("client_id", undefined)}
          />
        ) : null}
        {searchParams.relation ? (
          <FilterChip
            label={`Relationship: ${getStatusLabel(searchParams.relation)}`}
            onRemove={() => setRelation("all")}
          />
        ) : null}
        {searchParams.status ? (
          <FilterChip
            label={`Status: ${getStatusLabel(searchParams.status)}`}
            onRemove={() => setStatus("all")}
          />
        ) : null}
        <FilterTrigger
          label="All clients"
          value={searchParams.client_id ?? "all"}
          options={clientOptions}
          onChange={(value) => list.setFilter("client_id", value === "all" ? undefined : value)}
        />
        <FilterTrigger
          label="All relationships"
          value={(searchParams.relation ?? "all") as RelationFilter}
          options={RELATION_OPTIONS}
          onChange={setRelation}
        />
        <FilterTrigger
          label="All statuses"
          value={(searchParams.status ?? "all") as StatusFilter}
          options={STATUS_OPTIONS}
          onChange={setStatus}
        />
        {hasFilters ? (
          <Button
            type="button"
            variant="ghost"
            size="sm"
            className="h-8 shrink-0 rounded-sm px-2 text-sm text-fg-muted"
            onClick={clearFilters}
          >
            Clear filters
          </Button>
        ) : null}
        <div className="ml-auto" />
        <FilterSearch
          value={list.searchInput}
          onChange={list.setSearchInput}
          placeholder="Search name, member code or staff number…"
        />
      </FilterBar>

      <MemberRosterSummary stats={statsQuery.data} loading={statsQuery.isPending} />

      <MemberImportDialog
        open={importOpen}
        onOpenChange={setImportOpen}
        onImported={() => void queryClient.invalidateQueries({ queryKey: ["members"] })}
      />

      <MemberDuplicateScanDialog
        open={duplicatesOpen}
        onOpenChange={setDuplicatesOpen}
        loading={duplicatesQuery.isFetching}
        scanned={duplicatesQuery.data?.scanned ?? 0}
        items={duplicatesQuery.data?.items ?? []}
      />

      <MemberFormSheet
        open={list.addOpen || editing !== null}
        onOpenChange={(open) => {
          if (!open) {
            list.setAddOpen(false)
            setEditing(null)
          }
        }}
        member={editing}
        clientId={searchParams.client_id}
        onSaved={() => {
          void queryClient.invalidateQueries({ queryKey: ["members"] })
          list.setAddOpen(false)
          setEditing(null)
        }}
      />
      <MemberMergeDialog
        open={mergeOpen}
        onOpenChange={setMergeOpen}
        members={mergePair}
        onMerged={() => {
          selection.clearSelection()
          void queryClient.invalidateQueries({ queryKey: ["members"] })
        }}
      />

      <EntityListView
        columns={COLUMNS}
        items={items}
        rowKey={(row) => row.id}
        renderRow={(row) => (
          <MemberRow
            member={row}
            selected={selection.selectedIds.has(row.id)}
            onToggle={() => selection.toggleSelect(row.id)}
            onEdit={canWrite ? () => setEditing(row) : undefined}
          />
        )}
        loading={query.isPending}
        error={query.isError ? normalizeErrorMessage(query.error, "Failed to load members") : null}
        onRetry={() => void query.refetch()}
        empty={
          <EmptyState
            icon={Users}
            title={hasFilters ? "No members match your filters" : "No members yet"}
            description={
              hasFilters
                ? "Try a different search or clear a filter."
                : "Add or import the client-covered people who can use the wellness programme."
            }
            action={
              canWrite && !hasFilters ? (
                <Button variant="primary" size="sm" onClick={() => list.setAddOpen(true)}>
                  Add member
                </Button>
              ) : null
            }
          />
        }
        sort={list.sort}
        onToggleSort={list.toggleSort}
        page={list.page}
        total={query.data?.total ?? 0}
        limit={list.limit}
        onPageChange={list.setPage}
        selectAllState={selection.selectAllState}
        onToggleSelectAll={selection.toggleSelectAll}
        toolbar={
          <SelectionBar count={selection.selectedIds.size} onClear={selection.clearSelection}>
            {role === "Admin" && mergePair ? (
              <IconButton
                label="Merge selected"
                icon={Merge}
                destructive
                onClick={() => setMergeOpen(true)}
              />
            ) : null}
            <BulkAction
              ids={selection.selectedIds}
              label="Suspend"
              icon={CirclePause}
              confirmTitle="Suspend members"
              confirmDescription={(n) => `Suspend ${n} selected member${n === 1 ? "" : "s"}?`}
              action={membersApi.suspend}
              invalidateKey={["members"]}
              verb="suspended"
              noun="member"
              labelFor={(id) => mergeMembers.find((m) => m.id === id)?.display_label ?? id}
              onDone={selection.clearSelection}
            />
            <BulkAction
              ids={selection.selectedIds}
              label="Reinstate"
              icon={CirclePlay}
              confirmTitle="Reinstate members"
              confirmDescription={(n) => `Reinstate ${n} selected member${n === 1 ? "" : "s"}?`}
              action={membersApi.reinstate}
              invalidateKey={["members"]}
              verb="reinstated"
              noun="member"
              labelFor={(id) => mergeMembers.find((m) => m.id === id)?.display_label ?? id}
              onDone={selection.clearSelection}
            />
            <BulkAction
              ids={selection.selectedIds}
              label="Terminate"
              icon={CircleX}
              confirmTitle="Terminate members"
              confirmDescription={(n) =>
                `Terminate ${n} selected member${n === 1 ? "" : "s"}? This ends their eligibility.`
              }
              destructive
              action={membersApi.terminate}
              invalidateKey={["members"]}
              verb="terminated"
              noun="member"
              labelFor={(id) => mergeMembers.find((m) => m.id === id)?.display_label ?? id}
              onDone={selection.clearSelection}
            />
            <IconButton
              label="Export selected"
              icon={Download}
              onClick={() =>
                void download(
                  membersApi.exportCsv({ member_ids: [...selection.selectedIds] }),
                  "selected-members.csv",
                )
              }
            />
          </SelectionBar>
        }
      />
    </PageShell>
  )
}

/** Roster counts for the current filter context, above the table. */
function MemberRosterSummary({ stats, loading }: { stats?: MemberStats; loading: boolean }) {
  if (loading || !stats) return null
  // A roster of thousands is mostly one status. Counts that are zero say
  // nothing and crowd out the ones that do.
  const cells = [
    { label: "On roster", value: stats.total, emphasis: true },
    { label: "Active", value: stats.active },
    { label: "Suspended", value: stats.suspended },
    { label: "Pending", value: stats.pending },
    { label: "Terminated", value: stats.terminated },
    { label: "Portal accounts", value: stats.with_account },
  ].filter((cell) => cell.emphasis || cell.value > 0)
  return (
    <div className="flex shrink-0 flex-wrap items-center gap-x-6 gap-y-1 border-b border-fg/10 bg-surface px-3 py-2">
      {cells.map((cell) => (
        <span key={cell.label} className="flex items-baseline gap-1.5">
          <span
            className={`text-sm tabular-nums ${cell.emphasis ? "font-semibold text-fg" : "font-medium text-fg/80"}`}
          >
            {cell.value.toLocaleString()}
          </span>
          <span className="text-xs text-fg-muted">{cell.label}</span>
        </span>
      ))}
    </div>
  )
}

function MemberDuplicateScanDialog({
  open,
  onOpenChange,
  loading,
  scanned,
  items,
}: {
  open: boolean
  onOpenChange: (open: boolean) => void
  loading: boolean
  scanned: number
  items: MemberDuplicateCandidate[]
}) {
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-h-[80vh] overflow-y-auto sm:max-w-2xl">
        <DialogHeader>
          <DialogTitle>Duplicate member IDs</DialogTitle>
          <DialogDescription>
            {loading
              ? "Scanning members…"
              : `${items.length} exact matches in ${scanned} members. Only the same tenant, client, and Staff_ID are compared.`}
          </DialogDescription>
        </DialogHeader>
        {!loading && items.length === 0 ? (
          <p className="text-sm text-fg-muted">No duplicate Staff_IDs found.</p>
        ) : (
          <div className="space-y-2">
            {items.map((item) => (
              <div
                key={`${item.first.id}-${item.second.id}`}
                className="grid gap-3 rounded-md border p-3 sm:grid-cols-[1fr_auto_1fr] sm:items-center"
              >
                <MemberDuplicateCard member={item.first} />
                <span className="text-center text-xs text-fg-muted">{item.reason}</span>
                <MemberDuplicateCard member={item.second} />
              </div>
            ))}
          </div>
        )}
      </DialogContent>
    </Dialog>
  )
}

function MemberDuplicateCard({ member }: { member: MemberDuplicateCandidate["first"] }) {
  return (
    <Link
      to="/members/$memberId"
      params={{ memberId: member.id }}
      className="min-w-0 rounded-sm hover:bg-surface-hover"
    >
      <p className="truncate text-sm font-medium text-fg">{member.display_label}</p>
      <p className="truncate text-xs text-fg-muted">
        {member.employer_member_id} · {member.client_name ?? member.client_id} · {member.relation}
      </p>
    </Link>
  )
}

function MemberRow({
  member,
  selected,
  onToggle,
  onEdit,
}: {
  member: Member
  selected: boolean
  onToggle: () => void
  onEdit?: () => void
}) {
  const label = member.display_label ?? member.employer_member_id
  return (
    <TableRow className={`group h-9 ${ROW_BORDER}`}>
      <TableCell className="px-3 py-1.5">
        <Checkbox aria-label={`Select ${label}`} checked={selected} onCheckedChange={onToggle} />
      </TableCell>
      <TableCell className="max-w-[14rem] truncate py-1.5">
        <Link
          to="/members/$memberId"
          params={{ memberId: member.id }}
          className="flex items-center gap-2.5"
        >
          <span
            aria-hidden
            className="grid size-6 shrink-0 place-items-center bg-primary/10 text-primary"
          >
            <User className="size-3.5" />
          </span>
          <span className="truncate text-sm font-medium text-fg group-hover:text-primary">
            {label}
          </span>
        </Link>
      </TableCell>
      <TableCell className="text-center">
        <StatusBadge status={member.status} iconOnly />
      </TableCell>
      <TableCell className="py-1.5 text-xs text-fg/70">{member.employer_member_id}</TableCell>
      <TableCell className="max-w-[12rem] truncate py-1.5 text-xs text-fg/70">
        {member.client_name ? (
          <Link
            to="/clients/$clientId"
            params={{ clientId: member.client_id }}
            className="hover:text-primary hover:underline"
          >
            {member.client_name}
          </Link>
        ) : (
          "-"
        )}
      </TableCell>
      <TableCell className="py-1.5 text-xs text-fg/70">{getStatusLabel(member.relation)}</TableCell>
      <TableCell className="max-w-[14rem] truncate py-1.5 text-xs text-fg/70">
        {member.work_email ?? "-"}
      </TableCell>
      <TableCell className="whitespace-nowrap py-1.5 text-xs text-fg/70">
        {member.phone ?? "-"}
      </TableCell>
      <TableCell className="py-1.5 text-right">
        <div className="flex items-center justify-end gap-0.5 opacity-0 transition-opacity group-hover:opacity-100 focus-within:opacity-100">
          <Link
            to="/members/$memberId"
            params={{ memberId: member.id }}
            aria-label={`Open ${label}`}
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
                aria-label={`More actions for ${label}`}
                className="size-7 p-0 text-fg/65"
              >
                <MoreHorizontal className="size-4" />
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end">
              <DropdownMenuItem asChild>
                <Link to="/members/$memberId" params={{ memberId: member.id }}>
                  View details
                </Link>
              </DropdownMenuItem>
              {onEdit ? <DropdownMenuItem onSelect={onEdit}>Edit</DropdownMenuItem> : null}
            </DropdownMenuContent>
          </DropdownMenu>
        </div>
      </TableCell>
    </TableRow>
  )
}
