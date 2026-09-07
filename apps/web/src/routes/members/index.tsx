import { useCallback, useState } from "react"

import { useQuery, useQueryClient } from "@tanstack/react-query"
import { createFileRoute, Link, useNavigate, useSearch } from "@tanstack/react-router"
import {
  Download,
  ExternalLink,
  FileDown,
  FileUp,
  MoreHorizontal,
  Plus,
  ScanSearch,
  User,
  Users,
} from "lucide-react"

import { type MemberDuplicateCandidate, membersApi } from "@/api/endpoints/members"
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
import { useListPage } from "@/hooks/useListPage"
import { useTableSelection } from "@/hooks/useTableSelection"
import { normalizeErrorMessage } from "@/lib/errors"
import { useEntityList } from "@/lib/queries"
import { enumParam, listSearchSchema } from "@/lib/search-params"
import type { Member } from "@/types/entities"
import { EligibilityStatus, MemberRelation } from "@/types/enums"

export const Route = createFileRoute("/members/")({
  component: MembersListPage,
  validateSearch: listSearchSchema({
    relation: enumParam(MemberRelation),
    status: enumParam(EligibilityStatus),
    client_id: (value) => (typeof value === "string" && value.trim() ? value : undefined),
  }),
})

const COLUMNS: ListColumn[] = [
  { header: "Member", sortField: "display_label" },
  {
    header: <span className="sr-only">Status</span>,
    sortField: "status",
    className: "text-center",
  },
  { header: "Member code", className: "text-fg/65" },
  { header: "Relationship", sortField: "relation", className: "text-fg/65" },
  { header: "Client", className: "text-fg/65" },
  { header: "Work email", className: "text-fg/65" },
  { header: "Personal email", className: "text-fg/65" },
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
  const list = useListPage({ searchParams, navigate })
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

  return (
    <PageShell
      icon={Users}
      breadcrumb="Members"
      actions={
        <>
          <IconButton
            label="Export members"
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
          <Button
            type="button"
            variant="ghost"
            size="sm"
            className="h-7 gap-1.5 px-2"
            onClick={() =>
              void download(membersApi.getImportTemplate(), "members-import-template.csv")
            }
          >
            <FileDown className="size-3.5" />
            Template
          </Button>
          <Button
            type="button"
            variant="ghost"
            size="sm"
            className="h-7 gap-1.5 px-2"
            onClick={scanDuplicates}
          >
            <ScanSearch className="size-3.5" />
            Find duplicates
          </Button>
          {canWrite ? (
            <Button
              type="button"
              variant="outline"
              size="sm"
              className="h-7 gap-1.5 rounded-none px-2"
              onClick={() => setImportOpen(true)}
            >
              <FileUp className="size-3.5" />
              Import
            </Button>
          ) : null}
          {canWrite ? (
            <Button
              size="sm"
              className="h-7 gap-1.5 rounded-none px-2.5"
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
        {searchParams.relation ? (
          <FilterChip
            label={`Relationship: ${searchParams.relation}`}
            onRemove={() => setRelation("all")}
          />
        ) : null}
        {searchParams.status ? (
          <FilterChip label={`Status: ${searchParams.status}`} onRemove={() => setStatus("all")} />
        ) : null}
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
        <div className="ml-auto" />
        <FilterSearch
          value={list.searchInput}
          onChange={list.setSearchInput}
          placeholder="Search members…"
        />
      </FilterBar>

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
                <Button size="sm" className="rounded-none" onClick={() => list.setAddOpen(true)}>
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
              <Button
                type="button"
                variant="destructive"
                size="sm"
                className="h-7 rounded-none px-2.5"
                onClick={() => setMergeOpen(true)}
              >
                Merge selected
              </Button>
            ) : null}
            <Button
              type="button"
              variant="outline"
              size="sm"
              className="h-7 rounded-none px-2.5"
              onClick={() =>
                void download(
                  membersApi.exportCsv({ member_ids: [...selection.selectedIds] }),
                  "selected-members.csv",
                )
              }
            >
              <Download className="mr-1.5 size-3.5" />
              Export selected
            </Button>
          </SelectionBar>
        }
      />
    </PageShell>
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
      <TableCell className="py-1.5 text-xs text-fg/70">{member.relation}</TableCell>
      <TableCell className="max-w-[12rem] truncate py-1.5 text-xs text-fg/70">
        {member.client_name ?? "-"}
      </TableCell>
      <TableCell className="max-w-[14rem] truncate py-1.5 text-xs text-fg/70">
        {member.work_email ?? "-"}
      </TableCell>
      <TableCell className="max-w-[14rem] truncate py-1.5 text-xs text-fg/70">
        {member.personal_email ?? "-"}
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
