import { useEffect, useState } from "react"

import { useQuery, type UseQueryResult } from "@tanstack/react-query"
import { Link } from "@tanstack/react-router"
import { ExternalLink, Plus, RotateCw, User, Users, X } from "lucide-react"
import type { ReactNode } from "react"

import { contactsApi } from "@/api/endpoints/contacts"
import { contractsApi } from "@/api/endpoints/contracts"
import { documentsApi } from "@/api/endpoints/documents"
import { membersApi } from "@/api/endpoints/members"
import { utilisationApi } from "@/api/endpoints/utilisation"
import type { PaginatedResponse } from "@/api/types"
import { DetailGrid, DetailRow, RailSection } from "@/components/common/DetailPrimitives"
import { DocumentFileLink } from "@/components/common/DocumentFileLink"
import { EmptyState } from "@/components/common/EmptyState"
import { FilterBar, FilterSearch, FilterTrigger } from "@/components/common/FilterBar"
import { TableSkeleton } from "@/components/common/PageSkeletons"
import { StatusBadge } from "@/components/common/StatusBadge"
import { ROW_BORDER, STICKY_TABLE_HEAD } from "@/components/common/tableStyles"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Pagination } from "@/components/ui/pagination"
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"
import { useToast } from "@/contexts/ToastContext"
import { useDebouncedValue } from "@/hooks/useDebouncedValue"
import { contractLabel, memberLabel, nameInitials } from "@/lib/display"
import { normalizeErrorMessage } from "@/lib/errors"
import { formatDay } from "@/lib/format"
import { entityListKey } from "@/lib/queries"
import { cn } from "@/lib/utils"
import type { Client, Contact, Document, Member } from "@/types/entities"
import { EligibilityStatus, MemberRelation } from "@/types/enums"
import { getStatusLabel } from "@/utils/statusColors"

function Panel({
  title,
  children,
  action,
}: {
  title: string
  children: ReactNode
  action?: ReactNode
}) {
  return (
    <section className="self-start space-y-3 border border-fg/10 bg-surface p-4">
      <div className="flex items-center justify-between gap-3">
        <h2 className="text-sm font-semibold text-fg">{title}</h2>
        {action}
      </div>
      {children}
    </section>
  )
}

export function ClientContactsPanel({
  clientId,
  client,
  contacts,
}: {
  clientId: string
  client: Client
  contacts: Contact[]
}) {
  const toast = useToast()
  const [manageOpen, setManageOpen] = useState(false)
  const [name, setName] = useState("")
  const [email, setEmail] = useState("")
  const [phone, setPhone] = useState("")
  const [saving, setSaving] = useState(false)
  const contactsQuery = useQuery({
    queryKey: entityListKey("contacts", { client_id: clientId }),
    queryFn: () => contactsApi.byClient(clientId),
    enabled: manageOpen,
  })
  const managedContacts = contactsQuery.data ?? contacts
  const hasClientContactInfo = Boolean(
    client.contact_info?.email || client.contact_info?.phone || client.contact_info?.address,
  )
  const primaryContact =
    managedContacts.find((contact) => contact.is_primary) ??
    (!hasClientContactInfo ? managedContacts[0] : null)
  const otherContacts = primaryContact
    ? managedContacts.filter((contact) => contact.id !== primaryContact.id)
    : managedContacts

  useEffect(() => {
    if (manageOpen) return
    setName("")
    setEmail("")
    setPhone("")
  }, [manageOpen])

  const save = async () => {
    if (!name.trim()) return
    setSaving(true)
    try {
      await contactsApi.create({
        client_id: clientId,
        name: name.trim(),
        email: email || null,
        phone: phone || null,
        is_primary: managedContacts.length === 0 && !hasClientContactInfo,
      })
      await contactsQuery.refetch()
      toast.showSuccess("Contact added")
    } catch (error) {
      toast.showError(normalizeErrorMessage(error, "Could not add contact"))
    } finally {
      setSaving(false)
    }
  }

  return (
    <Panel title="Contacts">
      <div className="space-y-1">
        <p className="text-xs font-medium text-fg">Main contact</p>
        {primaryContact ? (
          <div>
            <p className="text-sm font-medium text-fg">{primaryContact.name}</p>
            <p className="text-xs text-fg-muted">
              {[primaryContact.title, primaryContact.department].filter(Boolean).join(" · ") ||
                "Contact"}
            </p>
            <p className="text-xs text-fg-muted">
              {[primaryContact.email, primaryContact.phone].filter(Boolean).join(" · ") ||
                "No contact details"}
            </p>
          </div>
        ) : client.contact_info?.email ||
          client.contact_info?.phone ||
          client.contact_info?.address ? (
          <div>
            <p className="text-xs text-fg-muted">
              {[client.contact_info.email, client.contact_info.phone].filter(Boolean).join(" · ") ||
                "No email or phone"}
            </p>
            {client.contact_info.address ? (
              <p className="text-xs text-fg-muted">{client.contact_info.address}</p>
            ) : null}
          </div>
        ) : (
          <p className="mt-1 text-xs text-fg-muted">No contact details have been added.</p>
        )}
      </div>
      {otherContacts.length > 0 ? (
        <div className="space-y-2 border-t border-fg/10 pt-3">
          <p className="text-xs font-medium text-fg">Other contacts</p>
          {otherContacts.map((contact) => (
            <div key={contact.id} className="border-b border-fg/8 pb-2 text-xs last:border-b-0">
              <p className="font-medium text-fg">{contact.name}</p>
              <p className="text-fg-muted">
                {contact.title ?? "Contact"} · {contact.email ?? contact.phone ?? "No details"}
              </p>
            </div>
          ))}
        </div>
      ) : null}
      <div className="flex items-center justify-between gap-3">
        <p className="text-xs text-fg-muted">
          {contacts.length} contact person{contacts.length === 1 ? "" : "s"} on file
        </p>
        <Button
          type="button"
          size="sm"
          variant="outline"
          className="h-7"
          onClick={() => setManageOpen((open) => !open)}
        >
          {manageOpen ? "Done" : "Manage contacts"}
        </Button>
      </div>
      {manageOpen ? (
        <div className="space-y-3 border-t border-fg/10 pt-3">
          <p className="text-xs font-medium text-fg">Add contact person</p>
          <Input
            aria-label="Contact name"
            placeholder="Name"
            value={name}
            onChange={(event) => setName(event.target.value)}
            required
          />
          <Input
            aria-label="Contact email"
            placeholder="Email"
            type="email"
            value={email}
            onChange={(event) => setEmail(event.target.value)}
          />
          <Input
            aria-label="Contact phone"
            placeholder="Phone"
            value={phone}
            onChange={(event) => setPhone(event.target.value)}
          />
          <Button
            type="button"
            size="sm"
            disabled={saving || !name.trim()}
            onClick={() => void save()}
          >
            {saving ? "Adding…" : "Add contact"}
          </Button>
        </div>
      ) : null}
    </Panel>
  )
}

export function ClientRosterPanel({
  clientId,
  query,
  onAdd,
}: {
  clientId: string
  query: UseQueryResult<PaginatedResponse<Member>>
  onAdd?: () => void
}) {
  const [search, setSearch] = useState("")
  const [relation, setRelation] = useState<MemberRelation | "all">("all")
  const [status, setStatus] = useState<EligibilityStatus | "all">("all")
  const [page, setPage] = useState(1)
  const [selectedId, setSelectedId] = useState<string | null>(null)
  const debouncedSearch = useDebouncedValue(search.trim())
  const params = {
    client_id: clientId,
    page,
    limit: 20,
    search: debouncedSearch || undefined,
    relation: relation === "all" ? undefined : relation,
    status: status === "all" ? undefined : status,
  }
  const filtered = Boolean(debouncedSearch || relation !== "all" || status !== "all" || page !== 1)
  const filteredQuery = useQuery({
    queryKey: entityListKey("members", params),
    queryFn: () => membersApi.list(params),
    enabled: filtered,
  })
  const roster = filtered ? filteredQuery : query
  const items = roster.data?.items ?? []
  const selectedMember = items.find((member) => member.id === selectedId) ?? null
  const hasFilters = Boolean(search || relation !== "all" || status !== "all")
  const clearFilters = () => {
    setSearch("")
    setRelation("all")
    setStatus("all")
    setPage(1)
  }

  return (
    <div className="grid grid-cols-12 gap-3 lg:h-[70vh]">
      <div className="col-span-12 flex min-h-0 min-w-0 flex-col border border-fg/10 bg-surface lg:col-span-8 lg:h-full">
        <FilterBar>
          <FilterTrigger
            label="All relationships"
            value={relation}
            options={RELATION_FILTER_OPTIONS}
            onChange={(value) => {
              setRelation(value)
              setPage(1)
            }}
          />
          <FilterTrigger
            label="All statuses"
            value={status}
            options={STATUS_FILTER_OPTIONS}
            onChange={(value) => {
              setStatus(value)
              setPage(1)
            }}
          />
          {hasFilters && (
            <Button variant="ghost" size="sm" className="h-8 shrink-0" onClick={clearFilters}>
              Clear filters
            </Button>
          )}
          <div className="ml-auto" />
          <FilterSearch
            value={search}
            onChange={(value) => {
              setSearch(value)
              setPage(1)
            }}
            placeholder="Search name, employee number or email"
          />
          {onAdd && (
            <Button type="button" size="sm" className="h-8 shrink-0 gap-1.5 px-2.5" onClick={onAdd}>
              <Plus className="size-3.5" />
              Add member
            </Button>
          )}
        </FilterBar>
        <div className="min-h-0 flex-1 overflow-y-auto">
          <ClientRosterTable
            query={roster}
            filtered={filtered}
            selectedId={selectedId}
            onSelect={setSelectedId}
          />
        </div>
        {roster.data && roster.data.total > 20 && (
          <div className="shrink-0 border-t border-fg/10 px-3 py-2">
            <Pagination page={page} total={roster.data.total} limit={20} onPageChange={setPage} />
          </div>
        )}
      </div>

      <div className="col-span-12 flex min-h-0 min-w-0 flex-col lg:col-span-4 lg:h-full">
        {selectedMember ? (
          <MemberSummaryCard member={selectedMember} onClose={() => setSelectedId(null)} />
        ) : (
          <RosterDetailsPlaceholder />
        )}
      </div>
    </div>
  )
}

const RELATION_FILTER_OPTIONS = [
  { value: "all", label: "All relationships" },
  ...Object.values(MemberRelation).map((value) => ({ value, label: getStatusLabel(value) })),
] as const

const STATUS_FILTER_OPTIONS = [
  { value: "all", label: "All statuses" },
  ...Object.values(EligibilityStatus).map((value) => ({ value, label: getStatusLabel(value) })),
] as const

function ClientRosterTable({
  query,
  filtered,
  selectedId,
  onSelect,
}: {
  query: UseQueryResult<PaginatedResponse<Member>>
  filtered: boolean
  selectedId: string | null
  onSelect: (id: string) => void
}) {
  if (query.isPending)
    return (
      <TableSkeleton
        cols={7}
        rows={6}
        headers={[
          "Member",
          "Status",
          "Member code",
          "Relationship",
          "Work email",
          "Personal email",
          "Phone",
        ]}
      />
    )
  if (query.isError) {
    return (
      <div role="alert" className="flex flex-col items-center gap-2 p-8 text-center text-sm">
        <p className="text-danger-fg">
          {normalizeErrorMessage(query.error, "Could not load members")}
        </p>
        <Button
          type="button"
          size="sm"
          variant="outline"
          className="gap-1.5"
          onClick={() => void query.refetch()}
        >
          <RotateCw className="size-3.5" />
          Try again
        </Button>
      </div>
    )
  }
  const { items, total } = query.data
  if (total === 0)
    return (
      <EmptyState
        icon={Users}
        title={filtered ? "No members match these filters" : "No members yet"}
        description={
          filtered
            ? "Try a different search or clear a filter."
            : "Add or import the people covered by this client."
        }
      />
    )
  return (
    <Table className="w-full text-sm" scrollable={false}>
      <TableHeader className={STICKY_TABLE_HEAD}>
        <TableRow className={`hover:bg-transparent ${ROW_BORDER}`}>
          <TableHead>Member</TableHead>
          <TableHead className="text-center">
            <span className="sr-only">Status</span>
          </TableHead>
          <TableHead className="text-fg/65">Member code</TableHead>
          <TableHead className="text-fg/65">Relationship</TableHead>
          <TableHead className="text-fg/65">Work email</TableHead>
          <TableHead className="text-fg/65">Personal email</TableHead>
          <TableHead className="text-fg/65">Phone</TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        {items.map((member) => (
          <RosterRow
            key={member.id}
            member={member}
            selected={selectedId === member.id}
            onSelect={() => onSelect(member.id)}
          />
        ))}
      </TableBody>
    </Table>
  )
}

function RosterRow({
  member,
  selected,
  onSelect,
}: {
  member: Member
  selected: boolean
  onSelect: () => void
}) {
  return (
    <TableRow
      onClick={onSelect}
      className={cn("cursor-pointer", ROW_BORDER, selected && "bg-primary/5 hover:bg-primary/5")}
    >
      <TableCell>
        <span className="flex items-center gap-2.5">
          <span
            aria-hidden
            className="grid size-6 shrink-0 place-items-center bg-primary/10 text-primary"
          >
            <User className="size-3.5" />
          </span>
          <span className={cn("truncate font-medium", selected ? "text-primary" : "text-fg")}>
            {memberLabel(member)}
          </span>
        </span>
      </TableCell>
      <TableCell className="text-center">
        <StatusBadge status={member.status} iconOnly />
      </TableCell>
      <TableCell className="text-xs text-fg/65">{member.employer_member_id}</TableCell>
      <TableCell className="text-xs text-fg/65">{getStatusLabel(member.relation)}</TableCell>
      <TableCell className="max-w-[14rem] truncate text-xs text-fg/65">
        {member.work_email ?? <span className="text-fg-subtle">-</span>}
      </TableCell>
      <TableCell className="max-w-[14rem] truncate text-xs text-fg/65">
        {member.personal_email ?? <span className="text-fg-subtle">-</span>}
      </TableCell>
      <TableCell className="whitespace-nowrap text-xs text-fg/65">
        {member.phone ?? <span className="text-fg-subtle">-</span>}
      </TableCell>
    </TableRow>
  )
}

function MemberSummaryCard({ member, onClose }: { member: Member; onClose: () => void }) {
  const label = memberLabel(member)
  const summary = [
    getStatusLabel(member.relation),
    getStatusLabel(member.status),
    member.employer_member_id,
  ]
    .filter(Boolean)
    .join(" · ")

  return (
    <div className="flex min-h-0 flex-1 flex-col border border-fg/10 bg-surface">
      <header className="flex items-start gap-3 border-b border-fg/10 px-4 py-3">
        <span
          aria-hidden
          className="grid size-9 shrink-0 place-items-center bg-primary/10 text-xs font-semibold text-primary"
        >
          {nameInitials(label)}
        </span>
        <div className="min-w-0 flex-1">
          <h3 className="truncate text-sm font-semibold leading-tight text-fg">{label}</h3>
          <p className="mt-1 truncate text-xs text-fg-muted">{summary}</p>
        </div>
        <Button
          type="button"
          variant="ghost"
          size="sm"
          onClick={onClose}
          aria-label="Close details"
          className="size-7 shrink-0 p-0 text-fg-muted"
        >
          <X className="size-4" />
        </Button>
      </header>

      <div className="flex min-h-0 flex-1 flex-col gap-5 overflow-y-auto p-4">
        <RailSection title="Personal">
          <DetailGrid>
            <DetailRow label="Date of birth" value={member.date_of_birth} />
            <DetailRow
              label="Gender"
              value={member.gender ? getStatusLabel(member.gender) : null}
            />
          </DetailGrid>
        </RailSection>
        <RailSection title="Contact" className="border-t border-fg/10 pt-4">
          <DetailGrid>
            <DetailRow label="Phone" value={member.phone} />
            <DetailRow label="Work email" value={member.work_email} />
            <DetailRow label="Personal email" value={member.personal_email} fullWidth />
          </DetailGrid>
        </RailSection>
        <Link
          to="/members/$memberId"
          params={{ memberId: member.id }}
          className="mt-auto inline-flex items-center gap-1.5 border-t border-fg/10 pt-4 text-sm font-medium text-primary hover:underline"
        >
          Open full profile
          <ExternalLink className="size-3.5" />
        </Link>
      </div>
    </div>
  )
}

function RosterDetailsPlaceholder() {
  return (
    <div className="flex flex-1 flex-col items-center justify-center gap-1 border border-dashed border-fg/15 p-8 text-center">
      <div className="mb-2 grid size-9 place-items-center bg-primary/10">
        <Users className="size-4 text-primary" />
      </div>
      <h3 className="text-sm font-semibold text-fg">Pick a member</h3>
      <p className="max-w-[24ch] text-xs text-fg/60">Select a row to view their summary.</p>
    </div>
  )
}

async function allPages<T>(
  fetchPage: (page: number) => Promise<PaginatedResponse<T>>,
): Promise<T[]> {
  const items: T[] = []
  for (let page = 1; ; page++) {
    const result = await fetchPage(page)
    items.push(...result.items)
    if (items.length >= result.total || !result.items.length) return items
  }
}

function ClientQueryPanel<T>({
  title,
  description,
  query,
  children,
}: {
  title: string
  description: string
  query: UseQueryResult<T>
  children: (data: T) => ReactNode
}) {
  return (
    <Panel title={title}>
      <p className="text-sm text-fg-muted">{description}</p>
      {query.isPending ? (
        <p role="status" className="py-8 text-sm text-fg-muted">
          Loading…
        </p>
      ) : query.isError ? (
        <div role="alert" className="border border-danger-fg/20 p-4 text-sm">
          <p>{normalizeErrorMessage(query.error, "Could not load records")}</p>
          <Button
            variant="outline"
            size="sm"
            className="mt-3 rounded-none"
            onClick={() => void query.refetch()}
          >
            Retry
          </Button>
        </div>
      ) : (
        children(query.data)
      )}
    </Panel>
  )
}

const clientContracts = (clientId: string) =>
  allPages((page) => contractsApi.list({ client_id: clientId, page, limit: 100 }))

export function ClientDocumentsPanel({ clientId }: { clientId: string }) {
  const [page, setPage] = useState(1)
  const query = useQuery({
    queryKey: entityListKey("documents", { client_id: clientId, page, limit: 20 }),
    queryFn: () => documentsApi.list({ client_id: clientId, page, limit: 20 }),
  })
  return (
    <ClientQueryPanel
      title="Documents"
      description="Files and records linked to this client."
      query={query}
    >
      {(data) => (
        <>
          {data.total === 0 ? (
            <p className="border border-dashed border-fg/15 p-8 text-center text-sm text-fg-muted">
              No documents linked yet.
            </p>
          ) : (
            <div className="divide-y divide-fg/10">
              {data.items.map((document) => (
                <DocumentRow key={document.id} document={document} />
              ))}
            </div>
          )}
          {data.total > 20 && (
            <div className="flex items-center justify-between border-t border-fg/10 pt-3 text-sm">
              <span>
                Page {page} of {Math.ceil(data.total / 20)} · {data.total} documents
              </span>
              <div className="flex gap-2">
                <Button variant="outline" disabled={page === 1} onClick={() => setPage(page - 1)}>
                  Previous
                </Button>
                <Button
                  variant="outline"
                  disabled={page * 20 >= data.total}
                  onClick={() => setPage(page + 1)}
                >
                  Next
                </Button>
              </div>
            </div>
          )}
        </>
      )}
    </ClientQueryPanel>
  )
}

function DocumentRow({ document }: { document: Document }) {
  return (
    <div className="flex items-center justify-between gap-4 py-4">
      <div className="min-w-0">
        <p className="truncate text-sm font-medium text-fg">{document.name}</p>
        <p className="mt-1 text-xs text-fg-muted">
          {getStatusLabel(document.document_type)} · Version {document.version ?? 1}
        </p>
      </div>
      <DocumentFileLink document={document} />
    </div>
  )
}

export function ClientUtilisationPanel({ clientId }: { clientId: string }) {
  const query = useQuery({
    queryKey: ["clients", "utilisation", clientId],
    queryFn: async () => {
      const contracts = await clientContracts(clientId)
      const groups = await Promise.all(
        contracts.map(async (contract) => ({
          contract,
          events: await utilisationApi.byContract(contract.id),
        })),
      )
      return groups
        .flatMap(({ contract, events }) => events.map((event) => ({ contract, event })))
        .sort((a, b) => b.event.occurred_on.localeCompare(a.event.occurred_on))
    },
  })
  return (
    <ClientQueryPanel
      title="Sessions"
      description="Recorded service usage across all contract terms."
      query={query}
    >
      {(rows) =>
        !rows.length ? (
          <p className="border border-dashed border-fg/15 p-8 text-center text-sm text-fg-muted">
            No service delivery recorded yet.
          </p>
        ) : (
          <>
            <div className="grid grid-cols-2 gap-4 border-y border-fg/10 py-4">
              <div>
                <p className="text-2xl font-semibold tabular-nums">
                  {rows.reduce((sum, { event }) => sum + event.units, 0).toLocaleString()}
                </p>
                <p className="text-xs text-fg-muted">Recorded units</p>
              </div>
              <div>
                <p className="text-2xl font-semibold tabular-nums">
                  {rows.length.toLocaleString()}
                </p>
                <p className="text-xs text-fg-muted">Recorded events</p>
              </div>
            </div>
            <div className="overflow-x-auto">
              <Table className="w-full text-left text-sm" scrollable={false}>
                <TableHeader className="border-b border-fg/10 text-xs text-fg-muted">
                  <TableRow>
                    <TableHead className="py-3">Date</TableHead>
                    <TableHead>Service event</TableHead>
                    <TableHead>Contract term</TableHead>
                    <TableHead className="text-right">Units</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody className="divide-y divide-fg/10">
                  {rows.map(({ event, contract }) => (
                    <TableRow key={event.id}>
                      <TableCell className="whitespace-nowrap py-3 pr-4">
                        {formatDay(event.occurred_on)}
                      </TableCell>
                      <TableCell className="pr-4">{getStatusLabel(event.event_type)}</TableCell>
                      <TableCell>
                        <Link
                          to="/contracts/$contractId"
                          params={{ contractId: contract.id }}
                          className="text-primary hover:underline"
                        >
                          {contractLabel(contract)}
                        </Link>
                      </TableCell>
                      <TableCell className="text-right tabular-nums">{event.units}</TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>
          </>
        )
      }
    </ClientQueryPanel>
  )
}
