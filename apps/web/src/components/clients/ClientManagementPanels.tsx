import { useEffect, useState } from "react"

import { useQuery, type UseQueryResult } from "@tanstack/react-query"
import { Link } from "@tanstack/react-router"
import type { ReactNode } from "react"

import { contactsApi } from "@/api/endpoints/contacts"
import { contractsApi } from "@/api/endpoints/contracts"
import { documentsApi } from "@/api/endpoints/documents"
import { membersApi } from "@/api/endpoints/members"
import { serviceAssignmentsApi } from "@/api/endpoints/service-assignments"
import { servicesApi } from "@/api/endpoints/services"
import { utilisationApi } from "@/api/endpoints/utilisation"
import type { PaginatedResponse } from "@/api/types"
import { StatusBadge } from "@/components/common/StatusBadge"
import { DocumentFileLink } from "@/components/common/DocumentFileLink"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import { useToast } from "@/contexts/ToastContext"
import { useDebouncedValue } from "@/hooks/useDebouncedValue"
import { normalizeErrorMessage } from "@/lib/errors"
import { entityListKey } from "@/lib/queries"
import type { Client, Contact, Document, Member } from "@/types/entities"
import { contractLabel, memberLabel } from "@/lib/display"
import { MemberRelation, EligibilityStatus } from "@/types/enums"
import { formatDay } from "@/lib/format"
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
  const debouncedSearch = useDebouncedValue(search.trim())
  const params = { client_id: clientId, page, limit: 20, search: debouncedSearch || undefined,
    relation: relation === "all" ? undefined : relation,
    status: status === "all" ? undefined : status }
  const filtered = Boolean(debouncedSearch || relation !== "all" || status !== "all" || page !== 1)
  const filteredQuery = useQuery({
    queryKey: entityListKey("members", params),
    queryFn: () => membersApi.list(params),
    enabled: filtered,
  })
  const roster = filtered ? filteredQuery : query
  return (
    <Panel
      title="Members"
      action={
        onAdd ? (
          <Button
            type="button"
            size="sm"
            variant="outline"
            className="h-7 rounded-none"
            onClick={onAdd}
          >
            Add member
          </Button>
        ) : null
      }
    >
      <p className="text-sm text-fg-muted">Employees and beneficiaries covered by this client. Open a member to manage their details and dependants.</p>
      <div className="flex flex-col gap-3 border-y border-fg/10 py-4 sm:flex-row">
        <Input aria-label="Search members" placeholder="Search name, employee number or email" value={search}
          onChange={(event) => { setSearch(event.target.value); setPage(1) }} className="sm:flex-1" />
        <Select value={relation} onValueChange={(value) => { setRelation(value as MemberRelation | "all"); setPage(1) }}>
          <SelectTrigger aria-label="Relationship" className="sm:w-44"><SelectValue /></SelectTrigger>
          <SelectContent><SelectItem value="all">All relationships</SelectItem>
            {Object.values(MemberRelation).map((value) => <SelectItem key={value} value={value}>{getStatusLabel(value)}</SelectItem>)}
          </SelectContent>
        </Select>
        <Select value={status} onValueChange={(value) => { setStatus(value as EligibilityStatus | "all"); setPage(1) }}>
          <SelectTrigger aria-label="Eligibility status" className="sm:w-40"><SelectValue /></SelectTrigger>
          <SelectContent><SelectItem value="all">All statuses</SelectItem>
            {Object.values(EligibilityStatus).map((value) => <SelectItem key={value} value={value}>{getStatusLabel(value)}</SelectItem>)}
          </SelectContent>
        </Select>
        {(search || relation !== "all" || status !== "all") && <Button variant="ghost" onClick={() => { setSearch(""); setRelation("all"); setStatus("all"); setPage(1) }}>Clear filters</Button>}
      </div>
      <ClientRosterContent query={roster} filtered={filtered} />
      {roster.data && roster.data.total > 20 && <div className="flex items-center justify-between border-t border-fg/10 pt-3 text-sm">
        <span>Page {page} of {Math.ceil(roster.data.total / 20)}</span>
        <div className="flex gap-2">
          <Button variant="outline" disabled={page === 1 || roster.isFetching} onClick={() => setPage(page - 1)}>Previous</Button>
          <Button variant="outline" disabled={page * 20 >= roster.data.total || roster.isFetching} onClick={() => setPage(page + 1)}>Next</Button>
        </div>
      </div>}
    </Panel>
  )
}

function ClientRosterContent({ query, filtered }: { query: UseQueryResult<PaginatedResponse<Member>>, filtered: boolean }) {
  if (query.isPending) return <p className="text-xs text-fg-muted">Loading members…</p>
  if (query.isError) {
    return (
      <div role="alert" className="space-y-2 text-xs text-danger-fg">
        <p>{normalizeErrorMessage(query.error, "Could not load members")}</p>
        <Button
          type="button"
          size="sm"
          variant="outline"
          className="rounded-none"
          onClick={() => void query.refetch()}
        >
          Retry
        </Button>
      </div>
    )
  }
  const { items, total } = query.data
  if (total === 0) return <p className="border border-dashed border-fg/15 p-8 text-center text-sm text-fg-muted">{filtered ? "No members match these filters." : "No members yet."}</p>
  return (
    <>
      <p className="text-xs text-fg-muted">
        Showing {items.length} of {total} members · employees and beneficiaries
      </p>
      <Table>
        <TableHeader><TableRow><TableHead>Member</TableHead><TableHead>Relationship</TableHead><TableHead>Contact</TableHead><TableHead>Status</TableHead></TableRow></TableHeader>
        <TableBody>{items.map((member) => <RosterRow key={member.id} member={member} />)}</TableBody>
      </Table>
    </>
  )
}

function RosterRow({ member }: { member: Member }) {
  return (
    <TableRow>
      <TableCell><Link to="/members/$memberId" params={{ memberId: member.id }} className="font-medium text-primary hover:underline">{memberLabel(member)}</Link>
        <p className="mt-1 text-xs text-fg-muted">{member.employer_member_id}</p>
      </TableCell>
      <TableCell>{getStatusLabel(member.relation)}</TableCell>
      <TableCell><p>{member.work_email || member.personal_email || "No email"}</p><p className="mt-1 text-xs text-fg-muted">{member.phone || "No phone"}</p></TableCell>
      <TableCell><StatusBadge status={member.status} /></TableCell>
    </TableRow>
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

export function ClientServicesPanel({ clientId }: { clientId: string }) {
  const query = useQuery({
    queryKey: ["clients", "services", clientId],
    queryFn: async () => {
      const contracts = await clientContracts(clientId)
      const groups = await Promise.all(
        contracts.map(async (contract) => ({
          contract,
          assignments: await allPages((page) =>
            serviceAssignmentsApi.list({ contract_id: contract.id, page, limit: 100 }),
          ),
        })),
      )
      const serviceIds = [
        ...new Set(groups.flatMap(({ assignments }) => assignments.map((a) => a.service_id))),
      ]
      const services = new Map(await Promise.all(serviceIds.map(async (id) => [id, await servicesApi.getById(id)] as const)))
      return groups.map(({contract, assignments}) => ({contract, assignments: assignments.map((assignment) => ({assignment, service: services.get(assignment.service_id)!}))}))
    },
  })
  return (
    <ClientQueryPanel
      title="Services by contract"
      description="Each contract has its own service assignments and coverage. Open a contract to manage its services."
      query={query}
    >
      {(rows) =>
        !rows.length ? (
          <p className="border border-dashed border-fg/15 p-8 text-center text-sm text-fg-muted">
            Add a contract before assigning services.
          </p>
        ) : (
          <div className="space-y-4">
            {rows.map(({ contract, assignments }) => (
              <article key={contract.id} className="border border-fg/10">
                <header className="flex items-center justify-between gap-3 border-b border-fg/10 bg-fg/3 p-4">
                  <div><p className="mb-1 text-xs text-fg-muted">Contract term · {assignments.length} services</p>
                  <Link to="/contracts/$contractId" params={{ contractId: contract.id }} search={{tab: "services"}} className="font-medium text-primary hover:underline">{contractLabel(contract)}</Link></div>
                  <StatusBadge status={contract.status} />
                </header>
                {assignments.length ? <div className="divide-y divide-fg/10">{assignments.map(({assignment, service}) => <div key={assignment.id ?? service.id} className="flex items-center justify-between gap-4 p-4">
                  <div><Link to="/services/$serviceId" params={{serviceId: service.id}} className="text-sm font-medium text-primary hover:underline">{service.name}</Link>
                  <p className="mt-1 text-xs text-fg-muted">{getStatusLabel(service.category ?? "Service")}</p>
                  {assignment.notes && <p className="mt-2 text-sm text-fg-muted">{assignment.notes}</p>}</div>
                  <StatusBadge status={assignment.status} />
                </div>)}</div> : <p className="p-6 text-sm text-fg-muted">No services assigned to this contract yet.</p>}
              </article>
            ))}
          </div>
        )
      }
    </ClientQueryPanel>
  )
}

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
              <Table className="w-full text-left text-sm">
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
