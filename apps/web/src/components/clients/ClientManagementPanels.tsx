import { useEffect, useState } from "react"

import { useQueries, useQuery } from "@tanstack/react-query"
import { Link } from "@tanstack/react-router"
import type { ReactNode } from "react"

import { contactsApi } from "@/api/endpoints/contacts"
import { documentsApi } from "@/api/endpoints/documents"
import { personsApi } from "@/api/endpoints/persons"
import { serviceAssignmentsApi } from "@/api/endpoints/service-assignments"
import { servicesApi } from "@/api/endpoints/services"
import { utilisationApi } from "@/api/endpoints/utilisation"
import { Button } from "@/components/ui/button"
import { Checkbox } from "@/components/ui/checkbox"
import { Input } from "@/components/ui/input"
import { useToast } from "@/contexts/ToastContext"
import { normalizeErrorMessage } from "@/lib/errors"
import { entityListKey } from "@/lib/queries"
import type { Client, Contact, Contract, Document, Person, Service } from "@/types/entities"
import { PersonType } from "@/types/enums"

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

export function ClientHealthCard({
  client,
  stats,
  contacts,
  staffCount,
  contracts,
}: {
  client: Client
  stats: { child_clients_count?: number; active_contracts_count?: number } | null
  contacts: Contact[]
  staffCount: number
  contracts: Contract[]
}) {
  const signals = [
    { label: "Verified", ok: Boolean(client.is_verified) },
    { label: "Primary contact", ok: contacts.some((contact) => contact.is_primary) },
    {
      label: "Active contract",
      ok: Boolean(
        stats?.active_contracts_count ?? contracts.some((contract) => contract.is_active),
      ),
    },
    { label: "Roster started", ok: staffCount > 0 },
  ]
  const score = Math.round((signals.filter((signal) => signal.ok).length / signals.length) * 100)
  return (
    <Panel title="Client health">
      <div className="flex items-end gap-3">
        <span className="text-3xl font-semibold text-fg">{score}</span>
        <span className="pb-1 text-xs text-fg-muted">/ 100 engagement readiness</span>
      </div>
      <div className="grid grid-cols-2 gap-2 text-xs">
        {signals.map((signal) => (
          <div key={signal.label} className={signal.ok ? "text-emerald-700" : "text-fg-muted"}>
            {signal.ok ? "✓" : "○"} {signal.label}
          </div>
        ))}
      </div>
    </Panel>
  )
}

export function ClientContactsPanel({
  clientId,
  contacts,
}: {
  clientId: string
  contacts: Contact[]
}) {
  const toast = useToast()
  const [manageOpen, setManageOpen] = useState(false)
  const [name, setName] = useState("")
  const [email, setEmail] = useState("")
  const [phone, setPhone] = useState("")
  const [makePrimary, setMakePrimary] = useState(false)
  const [saving, setSaving] = useState(false)
  const contactsQuery = useQuery({
    queryKey: entityListKey("contacts", { client_id: clientId }),
    queryFn: () => contactsApi.byClient(clientId),
    enabled: manageOpen,
  })
  const primaryQuery = useQuery({
    queryKey: ["contacts", "primary", clientId],
    queryFn: () => contactsApi.primary(clientId),
    retry: false,
  })
  const managedContacts = contactsQuery.data ?? contacts
  const primaryContact =
    primaryQuery.data ?? managedContacts.find((contact) => contact.is_primary) ?? null

  useEffect(() => {
    if (manageOpen) return
    setName("")
    setEmail("")
    setPhone("")
    setMakePrimary(false)
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
        is_primary: managedContacts.length === 0 || makePrimary,
      })
      await contactsQuery.refetch()
      await primaryQuery.refetch()
      toast.showSuccess("Contact added")
    } catch (error) {
      toast.showError(normalizeErrorMessage(error, "Could not add contact"))
    } finally {
      setSaving(false)
    }
  }

  const setPrimary = async (contact: Contact) => {
    try {
      await contactsApi.update(contact.id, { is_primary: true })
      await contactsQuery.refetch()
      await primaryQuery.refetch()
      toast.showSuccess("Primary contact updated")
    } catch (error) {
      toast.showError(normalizeErrorMessage(error, "Could not update primary contact"))
    }
  }

  return (
    <Panel title="Contacts and primary contact">
      <div className="rounded-sm border border-primary/20 bg-primary/5 p-3">
        <p className="text-[11px] font-medium uppercase tracking-wide text-primary">
          Primary contact
        </p>
        {primaryContact ? (
          <div className="mt-1">
            <p className="text-sm font-medium text-fg">{primaryContact.name}</p>
            <p className="text-xs text-fg-muted">
              {[primaryContact.title, primaryContact.department].filter(Boolean).join(" · ") ||
                "Primary contact"}
            </p>
            <p className="text-xs text-fg-muted">
              {primaryContact.email ?? primaryContact.phone ?? "No contact details"}
            </p>
          </div>
        ) : (
          <p className="mt-1 text-xs text-fg-muted">No primary contact has been assigned.</p>
        )}
      </div>
      <div className="flex items-center justify-between gap-3">
        <p className="text-xs text-fg-muted">
          {contacts.length} contact{contacts.length === 1 ? "" : "s"} on file
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
          <p className="text-xs font-medium text-fg">Contact people</p>
          {managedContacts.length === 0 ? (
            <p className="text-xs text-fg-muted">No contacts yet.</p>
          ) : null}
          {managedContacts.map((contact) => (
            <div
              key={contact.id}
              className="flex items-center justify-between gap-3 border-b border-fg/8 pb-2 text-xs"
            >
              <div>
                <p className="font-medium text-fg">
                  {contact.name}
                  {contact.is_primary ? " · Primary" : ""}
                </p>
                <p className="text-fg-muted">
                  {contact.title ?? "Contact"} · {contact.email ?? contact.phone ?? "No details"}
                </p>
              </div>
              {!contact.is_primary ? (
                <Button
                  type="button"
                  size="sm"
                  variant="ghost"
                  className="h-7 text-xs"
                  onClick={() => void setPrimary(contact)}
                >
                  Make primary
                </Button>
              ) : null}
            </div>
          ))}
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
            <label className="flex items-center gap-2 text-xs text-fg-muted">
              <Checkbox
                checked={makePrimary}
                onCheckedChange={(checked) => setMakePrimary(checked === true)}
              />
              Make this contact primary
            </label>
            <Button
              type="button"
              size="sm"
              disabled={saving || !name.trim()}
              onClick={() => void save()}
            >
              {saving ? "Adding…" : "Add contact"}
            </Button>
          </div>
        </div>
      ) : null}
    </Panel>
  )
}

export function ClientRosterPanel({ clientId, onAdd }: { clientId: string; onAdd: () => void }) {
  const rosterQuery = useQuery({
    queryKey: entityListKey("persons", { client_id: clientId, limit: 100 }),
    queryFn: () => personsApi.list({ client_id: clientId, limit: 100 }),
  })
  const people = rosterQuery.data?.items ?? []
  return (
    <Panel
      title="Employee and dependent roster"
      action={
        <Button type="button" size="sm" variant="outline" className="h-7" onClick={onAdd}>
          Add person
        </Button>
      }
    >
      <p className="text-xs text-fg-muted">
        {people.length} linked people · employees and dependents
      </p>
      {people.length === 0 ? (
        <p className="text-xs text-fg-muted">No roster records yet.</p>
      ) : (
        <div className="grid items-start gap-2 sm:grid-cols-2">
          {people.map((person) => (
            <RosterRow key={person.id} person={person} />
          ))}
        </div>
      )}
    </Panel>
  )
}

function RosterRow({ person }: { person: Person }) {
  const detail =
    person.person_type === PersonType.CLIENT_EMPLOYEE
      ? (person.employment_info?.role ?? person.employment_info?.department)
      : person.dependent_info?.relationship
  return (
    <Link
      to="/persons/$personId"
      params={{ personId: person.id }}
      className="border border-fg/8 p-2 text-xs hover:border-primary/40"
    >
      <div className="font-medium text-fg">{person.person_type}</div>
      <div className="text-fg-muted">{detail ?? person.user_id}</div>
    </Link>
  )
}

export function ClientServicesPanel({ contracts }: { contracts: Contract[] }) {
  const assignmentQueries = useQueries({
    queries: contracts.map((contract) => ({
      queryKey: entityListKey("service-assignments", { contract_id: contract.id, limit: 50 }),
      queryFn: () => serviceAssignmentsApi.list({ contract_id: contract.id, limit: 50 }),
    })),
  })
  const assignments = assignmentQueries.flatMap((query) => query.data?.items ?? [])
  const serviceIds = [...new Set(assignments.map((assignment) => assignment.service_id))]
  const serviceQueries = useQueries({
    queries: serviceIds.map((serviceId) => ({
      queryKey: ["services", serviceId],
      queryFn: () => servicesApi.getById(serviceId),
    })),
  })
  const services = serviceQueries.map(
    (query, index) => query.data ?? ({ id: serviceIds[index], name: serviceIds[index] } as Service),
  )
  return (
    <Panel title="Services">
      <p className="text-xs text-fg-muted">
        {assignments.length} service assignments across {contracts.length} contracts.
      </p>
      {services.length === 0 ? (
        <p className="text-xs text-fg-muted">No services assigned.</p>
      ) : (
        <div className="grid items-start gap-2 sm:grid-cols-2">
          {services.map((service) => (
            <Link
              key={service.id}
              to="/services/$serviceId"
              params={{ serviceId: service.id }}
              className="border border-fg/8 p-2 text-xs hover:border-primary/40"
            >
              <div className="font-medium text-fg">{service.name}</div>
              <div className="text-fg-muted">{service.category ?? "Service"}</div>
            </Link>
          ))}
        </div>
      )}
    </Panel>
  )
}

export function ClientDocumentsPanel({ clientId }: { clientId: string }) {
  const documentsQuery = useQuery({
    queryKey: entityListKey("documents", { client_id: clientId, limit: 100 }),
    queryFn: () => documentsApi.list({ client_id: clientId, limit: 100 }),
  })
  const documents = documentsQuery.data?.items ?? []
  return (
    <Panel title="Documents">
      <p className="text-xs text-fg-muted">{documents.length} client documents.</p>
      {documents.length === 0 ? (
        <p className="text-xs text-fg-muted">No documents linked to this client.</p>
      ) : (
        <div className="space-y-2">
          {documents.map((document) => (
            <DocumentRow key={document.id} document={document} />
          ))}
        </div>
      )}
    </Panel>
  )
}

function DocumentRow({ document }: { document: Document }) {
  return (
    <div className="flex items-center justify-between gap-3 border-b border-fg/8 pb-2 text-xs">
      <div>
        <div className="font-medium text-fg">{document.name}</div>
        <div className="text-fg-muted">
          {document.document_type} · v{document.version ?? 1}
        </div>
      </div>
      {document.file_url ? (
        <a href={document.file_url} target="_blank" rel="noreferrer" className="text-primary">
          Open
        </a>
      ) : null}
    </div>
  )
}

export function ClientUtilisationPanel({ contracts }: { contracts: Contract[] }) {
  const eventQueries = useQueries({
    queries: contracts.map((contract) => ({
      queryKey: ["utilisation-events", contract.id],
      queryFn: () => utilisationApi.byContract(contract.id),
    })),
  })
  const events = eventQueries.flatMap((query) => query.data ?? [])
  const units = events.reduce((sum, event) => sum + event.units, 0)
  return (
    <Panel title="Utilisation">
      <div className="flex items-end gap-3">
        <span className="text-2xl font-semibold text-fg">{units}</span>
        <span className="pb-0.5 text-xs text-fg-muted">units across {events.length} events</span>
      </div>
      {events.length === 0 ? (
        <p className="text-xs text-fg-muted">No utilisation recorded.</p>
      ) : (
        <div className="space-y-1 text-xs text-fg-muted">
          {events
            .slice(-8)
            .reverse()
            .map((event) => (
              <div key={event.id} className="flex justify-between">
                <span>
                  {event.occurred_on} · {event.service_code ?? event.event_type}
                </span>
                <span>{event.units}</span>
              </div>
            ))}
        </div>
      )}
    </Panel>
  )
}
