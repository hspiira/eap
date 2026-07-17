import { useCallback, useState } from "react"

import { useQuery, useQueryClient } from "@tanstack/react-query"
import { createFileRoute, Link, useNavigate } from "@tanstack/react-router"
import {
  ArrowLeft,
  CalendarClock,
  ChevronRight,
  Pencil,
  Plus,
  UserCog,
  Users,
} from "lucide-react"

import { clientsApi } from "@/api/endpoints/clients"
import { personsApi } from "@/api/endpoints/persons"
import { serviceSessionsApi } from "@/api/endpoints/service-sessions"
import { usersApi } from "@/api/endpoints/users"
import {
  DetailCard,
  DetailGrid,
  DetailRow,
  RailSection,
} from "@/components/common/DetailPrimitives"
import { renderDetailState } from "@/components/common/DetailStates"
import { EmptyState } from "@/components/common/EmptyState"
import { LifecycleActions } from "@/components/common/LifecycleActions"
import { PageShell } from "@/components/common/PageShell"
import { StatusBadge } from "@/components/common/StatusBadge"
import { Tab, TabPanel, Tabs, TabsList } from "@/components/common/Tabs"
import { PERSON_TYPE_LABELS, PersonFormSheet } from "@/components/PersonFormSheet"
import { Button } from "@/components/ui/button"
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"
import { useToast } from "@/contexts/ToastContext"
import { useTabSearchParam } from "@/hooks/useTabSearchParam"
import { displayName, personInitials } from "@/lib/display"
import { normalizeErrorMessage } from "@/lib/errors"
import { entityDetailKey, entityListKey, useEntityDetail } from "@/lib/queries"
import type { Client, Person, ServiceSession, User } from "@/types/entities"
import { PersonType } from "@/types/enums"
import type { LifecycleAction } from "@/utils/lifecycleConfig"

export const Route = createFileRoute("/persons/$personId")({
  component: PersonDetailPage,
})

type TabValue =
  | "overview"
  | "employment"
  | "family"
  | "emergency"
  | "sessions"
  | "history"
const TAB_VALUES: ReadonlyArray<TabValue> = [
  "overview",
  "employment",
  "family",
  "emergency",
  "sessions",
  "history",
]

function PersonDetailPage() {
  const { personId } = Route.useParams()
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const [actionLoading, setActionLoading] = useState(false)
  const toast = useToast()
  const [tab, setTab] = useTabSearchParam<TabValue>(TAB_VALUES, "overview")
  const [editOpen, setEditOpen] = useState(false)

  const personQuery = useEntityDetail<Person>({
    resource: "persons",
    id: personId,
    detailFn: personsApi.getById,
  })
  const person = personQuery.data ?? null

  const clientId = person?.employment_info?.client_id
  const { data: client = null } = useQuery({
    queryKey: entityDetailKey("clients", clientId ?? ""),
    queryFn: () => clientsApi.getById(clientId as string),
    enabled: !!clientId,
  })

  const userId = person?.user_id
  const { data: user = null } = useQuery({
    queryKey: entityDetailKey("users", userId ?? ""),
    queryFn: () => usersApi.getById(userId as string),
    enabled: !!userId,
  })

  const primaryEmployeeId = person?.dependent_info?.primary_employee_id
  const { data: primaryEmployee = null } = useQuery({
    queryKey: entityDetailKey("persons", primaryEmployeeId ?? ""),
    queryFn: () => personsApi.getById(primaryEmployeeId as string),
    enabled: !!primaryEmployeeId,
  })

  const sessionsQuery = useQuery({
    queryKey: entityListKey("service-sessions", { person_id: personId, limit: 20 }),
    queryFn: () => serviceSessionsApi.list({ limit: 20, person_id: personId }),
  })
  const sessions = sessionsQuery.data?.items ?? []

  const handleAction = useCallback(
    async (id: string, action: LifecycleAction) => {
      setActionLoading(true)
      try {
        if (action === "activate") await personsApi.activate(id)
        else if (action === "deactivate") await personsApi.deactivate(id)
        else if (action === "archive") await personsApi.archive(id)
        else if (action === "restore") await personsApi.restore(id)
        else if (action === "terminate") await personsApi.terminate(id, "Terminated from UI")
        // Invalidate rather than refetch by hand: this also refreshes the persons
        // list behind the page, which a targeted refetch would leave stale.
        await queryClient.invalidateQueries({ queryKey: ["persons"] })
        toast.showSuccess("Status updated")
      } catch (err) {
        toast.showError(normalizeErrorMessage(err, "Action failed — please try again"))
      } finally {
        setActionLoading(false)
      }
    },
    [queryClient, toast],
  )

  const state = renderDetailState(personQuery, {
    icon: Users,
    breadcrumb: "People · Persons",
    entity: "person",
    backTo: () => navigate({ to: "/persons" }),
    backLabel: "Back to persons",
  })
  if (state || !person) return state

  const fullName = displayName(person, user)
  const isDependent = person.person_type === PersonType.DEPENDENT
  const isEmployee = person.person_type === PersonType.CLIENT_EMPLOYEE

  return (
    <PageShell
      icon={Users}
      breadcrumb={`People · Persons · ${fullName}`}
      actions={
        <>
          <Button
            type="button"
            variant="ghost"
            size="sm"
            onClick={() => navigate({ to: "/persons" })}
            aria-label="Back to persons"
            title="Back to persons"
            className="size-7 p-0 text-fg/70"
          >
            <ArrowLeft className="size-3.5" />
          </Button>
          <Button
            size="sm"
            variant="outline"
            className="h-7 gap-1.5 px-2.5"
            onClick={() => setEditOpen(true)}
          >
            <Pencil className="size-3.5" />
            Edit
          </Button>
        </>
      }
    >
      <Hero person={person} client={client} user={user} />

      <PersonFormSheet
        open={editOpen}
        onOpenChange={setEditOpen}
        person={person}
        client={client}
        onSaved={(updated) =>
          queryClient.setQueryData(entityDetailKey("persons", updated.id), updated)
        }
      />

      <div className="min-h-0 flex-1 overflow-y-auto bg-bg">
        <div className="grid grid-cols-12 gap-5 px-5 py-5">
          <div className="col-span-12 min-w-0 lg:col-span-8">
            <Tabs value={tab} onValueChange={(v) => setTab(v as TabValue)}>
              <TabsList className="-mx-3 mb-4 px-3">
                <Tab value="overview">Overview</Tab>
                <Tab value="employment" disabled={!isEmployee}>
                  Employment
                </Tab>
                <Tab value="family" disabled={!isDependent}>
                  Family
                </Tab>
                <Tab value="emergency">Emergency</Tab>
                <Tab value="sessions" count={sessions.length}>
                  Sessions
                </Tab>
                <Tab value="history">History</Tab>
              </TabsList>

              <TabPanel value="overview">
                <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
                  <DetailCard title="Identity">
                    <DetailGrid>
                      <DetailRow label="Role" value={PERSON_TYPE_LABELS[person.person_type]} />
                      <DetailRow
                        label="Account email"
                        value={user?.email ?? (person.user_id ? "Loading…" : null)}
                        fullWidth
                      />
                      {person.family_id ? (
                        <DetailRow
                          label="Family ID"
                          value={<span className="font-mono text-xs">{person.family_id}</span>}
                          fullWidth
                        />
                      ) : null}
                    </DetailGrid>
                  </DetailCard>

                  <DetailCard title="Eligibility">
                    <DetailGrid>
                      <DetailRow
                        label="Eligible for services"
                        value={person.is_eligible_for_services ? "Yes" : "No"}
                      />
                      <DetailRow
                        label="Last service"
                        value={person.last_service_date}
                      />
                      <DetailRow
                        label="Dual role"
                        value={
                          person.is_dual_role && person.secondary_person_type
                            ? PERSON_TYPE_LABELS[person.secondary_person_type]
                            : "No"
                        }
                      />
                    </DetailGrid>
                  </DetailCard>
                </div>
              </TabPanel>

              <TabPanel value="employment">
                {person.employment_info ? (
                  <DetailCard title="Employment">
                    <DetailGrid>
                      <DetailRow
                        label="Employee code"
                        value={
                          person.employment_info.employee_code ? (
                            <span className="font-mono">
                              {person.employment_info.employee_code}
                            </span>
                          ) : null
                        }
                      />
                      <DetailRow
                        label="Department"
                        value={person.employment_info.department}
                      />
                      <DetailRow label="Role" value={person.employment_info.role} />
                      <DetailRow
                        label="Start date"
                        value={person.employment_info.start_date}
                      />
                      <DetailRow
                        label="End date"
                        value={person.employment_info.end_date}
                      />
                      <DetailRow
                        label="Work status"
                        value={person.employment_info.status}
                      />
                    </DetailGrid>
                  </DetailCard>
                ) : (
                  <EmptyState
                    title="No employment info yet"
                    description="Edit this person to fill in role, department, and dates."
                    action={
                      <Button size="sm" className="gap-1.5" onClick={() => setEditOpen(true)}>
                        <Pencil className="size-4" />
                        Edit
                      </Button>
                    }
                  />
                )}
              </TabPanel>

              <TabPanel value="family">
                {person.dependent_info ? (
                  <DetailCard title="Dependent of">
                    {primaryEmployee ? (
                      <Link
                        to="/persons/$personId"
                        params={{ personId: primaryEmployee.id }}
                        className="flex items-center gap-2.5 rounded-sm border border-fg/10 bg-surface px-3 py-2 transition-colors hover:border-fg/25"
                      >
                        <span
                          aria-hidden
                          className="grid size-7 shrink-0 place-items-center bg-primary/10 font-mono text-[10px] font-semibold text-primary"
                        >
                          {personInitials(primaryEmployee)}
                        </span>
                        <div className="min-w-0 flex-1">
                          <p className="truncate text-sm font-medium text-fg">
                            {displayName(primaryEmployee)}
                          </p>
                          <p className="truncate font-mono text-[11px] text-fg/55">
                            {primaryEmployee.employment_info?.employee_code ??
                              primaryEmployee.id.slice(0, 8)}
                          </p>
                        </div>
                      </Link>
                    ) : (
                      <p className="text-xs text-fg/55">Loading employee…</p>
                    )}
                    <DetailGrid>
                      <DetailRow
                        label="Relationship"
                        value={person.dependent_info.relationship}
                      />
                      <DetailRow
                        label="Family ID"
                        value={person.family_id}
                      />
                    </DetailGrid>
                  </DetailCard>
                ) : (
                  <EmptyState
                    title="No family link"
                    description="Dependents need a primary employee to receive services."
                  />
                )}
              </TabPanel>

              <TabPanel value="emergency">
                {person.emergency_contact &&
                (person.emergency_contact.name ||
                  person.emergency_contact.phone ||
                  person.emergency_contact.email) ? (
                  <DetailCard title="Emergency contact">
                    <DetailGrid>
                      <DetailRow label="Name" value={person.emergency_contact.name} fullWidth />
                      <DetailRow label="Phone" value={person.emergency_contact.phone} />
                      <DetailRow label="Email" value={person.emergency_contact.email} />
                    </DetailGrid>
                  </DetailCard>
                ) : (
                  <EmptyState
                    title="No emergency contact"
                    description="Add a name and phone in case of incidents."
                    action={
                      <Button size="sm" className="gap-1.5" onClick={() => setEditOpen(true)}>
                        <Pencil className="size-4" />
                        Add contact
                      </Button>
                    }
                  />
                )}
              </TabPanel>

              <TabPanel value="sessions">
                <SessionsPanel
                  sessions={sessions}
                  loading={sessionsQuery.isPending}
                  personId={personId}
                />
              </TabPanel>

              <TabPanel value="history">
                <EmptyState
                  title="No activity yet"
                  description="Lifecycle changes will appear here once the audit feed is wired up."
                />
              </TabPanel>
            </Tabs>
          </div>

          <aside className="col-span-12 min-w-0 lg:col-span-4 lg:pt-14">
            <DetailRail
              person={person}
              client={client}
              user={user}
              onAction={handleAction}
              actionLoading={actionLoading}
            />
          </aside>
        </div>
      </div>
    </PageShell>
  )
}

function Hero({ person, client, user }: { person: Person; client: Client | null; user: User | null }) {
  const fullName = displayName(person, user)
  return (
    <div className="flex shrink-0 items-center gap-3 border-b border-fg/10 bg-surface px-5 py-3">
      <span
        aria-hidden
        className="grid size-9 shrink-0 place-items-center rounded-sm bg-primary/10 font-mono text-xs font-semibold text-primary"
      >
        {personInitials(person, user)}
      </span>
      <h1 className="shrink truncate text-base font-semibold leading-tight text-fg">
        {fullName}
      </h1>
      {person.employment_info?.employee_code ? (
        <span className="font-mono text-xs text-fg/55">
          {person.employment_info.employee_code}
        </span>
      ) : null}
      <span className="h-4 w-px shrink-0 bg-fg/15" aria-hidden />
      <span className="inline-flex items-center rounded-sm border border-fg/15 bg-bg px-1.5 py-0.5 text-[11px] font-medium text-fg/75">
        {PERSON_TYPE_LABELS[person.person_type]}
      </span>
      <StatusBadge status={person.status} />
      {client ? (
        <Link
          to="/clients/$clientId"
          params={{ clientId: client.id }}
          className="ml-auto text-xs text-fg/60 hover:text-primary"
        >
          {client.name}
        </Link>
      ) : null}
    </div>
  )
}

interface DetailRailProps {
  person: Person
  client: Client | null
  user: User | null
  onAction: (id: string, action: LifecycleAction) => Promise<void>
  actionLoading: boolean
}

function DetailRail({ person, client, user, onAction, actionLoading }: DetailRailProps) {
  return (
    <div className="space-y-5">
      <RailSection title="At a glance">
        <DetailGrid>
          <DetailRow
            label="Eligible"
            value={person.is_eligible_for_services ? "Yes" : "No"}
          />
          <DetailRow
            label="Last service"
            value={person.last_service_date ?? "—"}
          />
        </DetailGrid>
      </RailSection>

      {client ? (
        <RailSection title="Client">
          <Link
            to="/clients/$clientId"
            params={{ clientId: client.id }}
            className="flex items-center gap-2.5 rounded-sm border border-fg/10 bg-surface px-3 py-2 transition-colors hover:border-fg/25"
          >
            <span
              aria-hidden
              className="grid size-7 shrink-0 place-items-center bg-primary/10 font-mono text-[10px] font-semibold text-primary"
            >
              {clientInitial(client.name)}
            </span>
            <div className="min-w-0 flex-1">
              <p className="truncate text-sm font-medium text-fg">{client.name}</p>
              <p className="truncate font-mono text-[11px] text-fg/55">{client.code}</p>
            </div>
          </Link>
        </RailSection>
      ) : null}

      <RailSection title="User account">
        {user ? (
          <Link
            to="/users/$userId"
            params={{ userId: user.id }}
            className="flex items-center gap-2.5 rounded-sm border border-fg/10 bg-surface px-3 py-2 transition-colors hover:border-fg/25"
          >
            <span
              aria-hidden
              className="grid size-7 shrink-0 place-items-center bg-primary/10 text-primary"
            >
              <UserCog className="size-3.5" />
            </span>
            <div className="min-w-0 flex-1">
              <p className="truncate text-sm font-medium text-fg">{user.email}</p>
              <p className="truncate text-[11px] text-fg/55">
                {user.is_two_factor_enabled ? "2FA on" : "2FA off"} ·{" "}
                {user.is_email_verified ? "verified" : "unverified"}
              </p>
            </div>
          </Link>
        ) : person.user_id ? (
          <p className="text-xs text-fg/55">Loading user…</p>
        ) : (
          <p className="text-xs text-fg/55">No user account linked.</p>
        )}
      </RailSection>

      <RailSection title="Lifecycle">
        <LifecycleActions
          entityId={person.id}
          currentStatus={person.status}
          kind="base"
          onAction={onAction}
          loading={actionLoading}
        />
      </RailSection>
    </div>
  )
}

function clientInitial(name: string): string {
  const trimmed = name.trim()
  if (!trimmed) return "·"
  const parts = trimmed.split(/\s+/)
  if (parts.length >= 2) return (parts[0][0] + parts[1][0]).toUpperCase()
  return trimmed.slice(0, 2).toUpperCase()
}

function SessionsPanel({
  sessions,
  loading,
  personId,
}: {
  sessions: ServiceSession[]
  loading: boolean
  personId: string
}) {
  if (loading) return <p className="text-sm text-fg/65">Loading sessions…</p>
  if (sessions.length === 0) {
    return (
      <EmptyState
        icon={CalendarClock}
        title="No sessions yet"
        description="Sessions delivered to this person will show up here."
        action={
          <Link
            to="/service-sessions"
            search={{ new: true, person_id: personId }}
            className="inline-flex h-9 items-center gap-1.5 rounded-sm border border-fg/15 bg-surface px-3 text-sm font-medium text-fg hover:bg-surface-hover"
          >
            <Plus className="size-4" />
            Schedule session
          </Link>
        }
      />
    )
  }
  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between">
        <p className="text-xs text-fg/55">{sessions.length} recent sessions.</p>
        <Link
          to="/service-sessions"
          search={{ person_id: personId }}
          className="text-xs font-medium text-primary hover:underline"
        >
          View all
        </Link>
      </div>
      <div className="overflow-hidden border border-fg/10 bg-surface">
        <Table className="w-full caption-bottom text-sm">
          <TableHeader className="border-b-0 bg-surface shadow-[inset_0_-1px_0_rgb(0_0_0/0.08)]">
            <TableRow className="border-fg/8 hover:bg-transparent">
              <TableHead>Scheduled</TableHead>
              <TableHead>Service</TableHead>
              <TableHead>Status</TableHead>
              <TableHead className="w-10 text-right text-fg/65">
                <span className="sr-only">Open</span>
              </TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {sessions.slice(0, 10).map((s) => (
              <TableRow key={s.id} className="group border-fg/8">
                <TableCell className="text-sm text-fg">
                  {new Date(s.scheduled_at).toLocaleString()}
                </TableCell>
                <TableCell>
                  <Link
                    to="/services/$serviceId"
                    params={{ serviceId: s.service_id }}
                    className="font-mono text-xs text-fg/75 hover:text-primary"
                  >
                    {s.service_id.slice(0, 8)}
                  </Link>
                </TableCell>
                <TableCell>
                  <StatusBadge status={s.status} />
                </TableCell>
                <TableCell className="text-right">
                  <Link
                    to="/service-sessions/$sessionId"
                    params={{ sessionId: s.id }}
                    aria-label="Open session"
                    className="inline-grid size-7 place-items-center rounded-sm text-fg/55 hover:bg-surface-hover hover:text-fg"
                  >
                    <ChevronRight className="size-3.5" />
                  </Link>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </div>
    </div>
  )
}
