import { useCallback, useEffect, useMemo, useState } from "react"

import { createFileRoute, Link, useNavigate } from "@tanstack/react-router"
import {
  ArrowLeft,
  BadgeCheck,
  Building2,
  ChevronRight,
  Pencil,
  Plus,
  RotateCw,
} from "lucide-react"

import { clientsApi } from "@/api/endpoints/clients"
import { contractsApi } from "@/api/endpoints/contracts"
import { ClientActivityCard } from "@/components/ClientActivityCard"
import type { ClientAlert } from "@/components/ClientAlertsCard"
import { ClientAlertsCard } from "@/components/ClientAlertsCard"
import { ClientFormSheet } from "@/components/ClientFormSheet"
import type { ClientOnboardingStep } from "@/components/ClientOnboardingCard"
import { ClientOnboardingCard } from "@/components/ClientOnboardingCard"
import { ClientStaffSummaryCard } from "@/components/ClientStaffSummaryCard"
import type { ClientTodaysTodoItem } from "@/components/ClientTodaysTodoCard"
import { ClientTodaysTodoCard } from "@/components/ClientTodaysTodoCard"
import type { ClientUpcomingItem } from "@/components/ClientUpcomingCard"
import { ClientUpcomingCard } from "@/components/ClientUpcomingCard"
import { EmptyState } from "@/components/common/EmptyState"
import { LifecycleActions } from "@/components/common/LifecycleActions"
import { PageShell } from "@/components/common/PageShell"
import { DetailSkeleton } from "@/components/common/PageSkeletons"
import {
  compareSort,
  nextSort,
  SortHeader,
  type SortState,
} from "@/components/common/SortHeader"
import { StatusBadge } from "@/components/common/StatusBadge"
import { Tab, TabPanel, Tabs, TabsList } from "@/components/common/Tabs"
import { TierBadge } from "@/components/common/TierBadge"
import { ContractFormSheet } from "@/components/ContractFormSheet"
import { EmailCampaignCard } from "@/components/EmailCampaignCard"
import { PersonFormSheet } from "@/components/PersonFormSheet"
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
import { normalizeErrorMessage } from "@/lib/errors"
import { cn } from "@/lib/utils"
import type { Client, ClientStats, ClientTag, Contract } from "@/types/entities"
import { PersonType } from "@/types/enums"
import type { LifecycleAction } from "@/utils/lifecycleConfig"

export const Route = createFileRoute("/clients/$clientId")({
  component: ClientDetailPage,
})

const ROW_BORDER = "border-fg/8"

type TabValue = "overview" | "activity" | "contracts" | "staff"
const TAB_VALUES: ReadonlyArray<TabValue> = ["overview", "activity", "contracts", "staff"]

function ClientDetailPage() {
  const { clientId } = Route.useParams()
  const navigate = useNavigate()
  const [client, setClient] = useState<Client | null>(null)
  const [loading, setLoading] = useState(true)
  const [actionLoading, setActionLoading] = useState(false)
  const toast = useToast()
  const [stats, setStats] = useState<ClientStats | null>(null)
  const [statsLoading, setStatsLoading] = useState(false)
  const [children, setChildren] = useState<Client[]>([])
  const [childrenLoading, setChildrenLoading] = useState(false)
  const [contracts, setContracts] = useState<Contract[]>([])
  const [contractsLoading, setContractsLoading] = useState(false)
  const [tags, setTags] = useState<ClientTag[]>([])
  const [tagsLoading, setTagsLoading] = useState(false)
  const [tab, setTab] = useTabSearchParam<TabValue>(TAB_VALUES, "overview")
  const [editOpen, setEditOpen] = useState(false)
  const [addContractOpen, setAddContractOpen] = useState(false)
  const [addPersonOpen, setAddPersonOpen] = useState(false)

  const fetchClient = useCallback(async () => {
    try {
      setLoading(true)
      const data = await clientsApi.getById(clientId)
      setClient(data)
    } catch (_err) {
      setClient(null)
    } finally {
      setLoading(false)
    }
  }, [clientId])

  useEffect(() => {
    fetchClient()
  }, [fetchClient])

  const fetchContracts = useCallback(() => {
    setContractsLoading(true)
    return contractsApi
      .list({ limit: 20, ...({ client_id: clientId } as Record<string, unknown>) })
      .then((res) => {
        const items = (res.items ?? []).filter((c: Contract) => c.client_id === clientId)
        setContracts(items.slice(0, 10))
      })
      .catch(() => setContracts([]))
      .finally(() => setContractsLoading(false))
  }, [clientId])

  useEffect(() => {
    if (!client) return
    setStatsLoading(true)
    setChildrenLoading(true)
    setTagsLoading(true)

    clientsApi
      .getStats(clientId)
      .then(setStats)
      .catch(() => setStats(null))
      .finally(() => setStatsLoading(false))

    clientsApi
      .getChildren(clientId, { limit: 10 })
      .then((res) => setChildren(res.items ?? []))
      .catch(() => setChildren([]))
      .finally(() => setChildrenLoading(false))

    fetchContracts()

    clientsApi
      .getTags(clientId)
      .then(setTags)
      .catch(() => setTags([]))
      .finally(() => setTagsLoading(false))
  }, [client, clientId, fetchContracts])

  const handleAction = useCallback(
    async (id: string, action: LifecycleAction) => {
      setActionLoading(true)
      try {
        if (action === "activate") await clientsApi.activate(id)
        else if (action === "deactivate") await clientsApi.deactivate(id)
        else if (action === "archive") await clientsApi.archive(id)
        else if (action === "restore") await clientsApi.restore(id)
        else if (action === "terminate") await clientsApi.terminate(id, "Terminated from UI")
        await fetchClient()
        toast.showSuccess("Status updated")
      } catch (err) {
        toast.showError(normalizeErrorMessage(err, "Action failed — please try again"))
      } finally {
        setActionLoading(false)
      }
    },
    [fetchClient, toast],
  )

  const hasBilling = client
    ? !!(
        client.billing_address &&
        (client.billing_address.street ||
          client.billing_address.city ||
          client.billing_address.postal_code ||
          client.billing_address.country)
      )
    : false

  const isVerified = !!(client?.is_verified ?? stats?.is_verified)

  const alerts = useMemo((): ClientAlert[] => {
    if (!client) return []
    const list: ClientAlert[] = []
    if (!isVerified) {
      list.push({
        id: "verify",
        title: "Client not verified",
        description: "Verify this client to confirm their details.",
        severity: "medium",
      })
    }
    if (!hasBilling) {
      list.push({
        id: "billing",
        title: "Billing address missing",
        description: "Add a billing address for invoicing.",
        severity: "medium",
      })
    }
    const now = new Date()
    const in30Days = new Date(now.getTime() + 30 * 24 * 60 * 60 * 1000)
    contracts.forEach((c) => {
      const end = c.end_date ? new Date(c.end_date) : null
      if (end && end <= in30Days && end >= now) {
        list.push({
          id: `contract-expiring-${c.id}`,
          title: `Contract ending soon: ${c.contract_number ?? c.id}`,
          description: `End date: ${c.end_date}`,
          severity: "high",
          link: `/contracts/${c.id}`,
          linkLabel: "View contract",
        })
      }
    })
    return list
  }, [client, isVerified, hasBilling, contracts])

  const upcomingItems = useMemo((): ClientUpcomingItem[] => {
    const list: ClientUpcomingItem[] = []
    const now = new Date()
    const in90Days = new Date(now.getTime() + 90 * 24 * 60 * 60 * 1000)
    contracts.forEach((c) => {
      if (c.renewal_date) {
        const d = new Date(c.renewal_date)
        if (d >= now && d <= in90Days) {
          list.push({
            id: `renewal-${c.id}`,
            title: `Contract renewal: ${c.contract_number ?? c.id}`,
            date: c.renewal_date,
            context: "Renewal",
            link: `/contracts/${c.id}`,
            linkLabel: "View",
          })
        }
      }
      if (c.end_date) {
        const d = new Date(c.end_date)
        if (d >= now && d <= in90Days) {
          list.push({
            id: `end-${c.id}`,
            title: `Contract ends: ${c.contract_number ?? c.id}`,
            date: c.end_date,
            context: "End date",
            link: `/contracts/${c.id}`,
            linkLabel: "View",
          })
        }
      }
    })
    return list.slice(0, 5).sort((a, b) => a.date.localeCompare(b.date))
  }, [contracts])

  const onboardingSteps = useMemo((): ClientOnboardingStep[] => {
    if (!client) return []
    const hasContact = !!(client.contact_info?.email || client.contact_info?.phone)
    const hasContract = contracts.length > 0
    return [
      { id: "contact", label: "Contact info added", done: hasContact },
      { id: "contract", label: "At least one contract", done: hasContract },
      { id: "billing", label: "Billing address set", done: hasBilling },
      { id: "verified", label: "Client verified", done: isVerified },
    ]
  }, [client, isVerified, contracts.length, hasBilling])

  const todaysTodoItems = useMemo((): ClientTodaysTodoItem[] => {
    const today = new Date().toISOString().slice(0, 10)
    return upcomingItems
      .filter((u) => u.date.slice(0, 10) === today)
      .map((u, i) => ({
        id: u.id,
        title: u.title,
        time: u.time ?? (i === 0 ? "09:00" : `${9 + i}:00`),
        link: u.link,
        linkLabel: u.linkLabel ?? "View",
      }))
  }, [upcomingItems])

  if (loading) {
    return (
      <PageShell icon={Building2} breadcrumb="Organization & Clients · Clients · …">
        <div className="min-h-0 flex-1 overflow-auto p-5">
          <DetailSkeleton railPanels={6} />
        </div>
      </PageShell>
    )
  }

  if (!client) {
    return (
      <PageShell icon={Building2} breadcrumb="Organization & Clients · Clients · Not found">
        <EmptyState
          icon={Building2}
          title="Client not found"
          description="The client you're looking for may have been archived or doesn't exist."
          action={
            <Button variant="outline" size="sm" className="gap-1.5" onClick={() => navigate({ to: "/clients" })}>
              <ArrowLeft className="size-4" />
              Back to clients
            </Button>
          }
        />
      </PageShell>
    )
  }

  return (
    <PageShell
      icon={Building2}
      breadcrumb={`Organization & Clients · Clients · ${client.name}`}
      actions={
        <>
          <Button
            type="button"
            variant="ghost"
            size="sm"
            onClick={() => navigate({ to: "/clients" })}
            aria-label="Back to clients"
            title="Back to clients"
            className="size-7 p-0 text-fg/70"
          >
            <ArrowLeft className="size-3.5" />
          </Button>
          <Button
            type="button"
            variant="ghost"
            size="sm"
            onClick={fetchClient}
            aria-label="Refresh"
            title="Refresh"
            className="size-7 p-0 text-fg/70"
            >
            <RotateCw className="size-3.5" />
            </Button>
          <span className="mx-1 h-4 w-px bg-fg/15" aria-hidden />
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
      <Hero client={client} verified={isVerified} />

      <ClientFormSheet
        open={editOpen}
        onOpenChange={setEditOpen}
        client={client}
        onSaved={(updated) => setClient(updated)}
      />

      <ContractFormSheet
        open={addContractOpen}
        onOpenChange={setAddContractOpen}
        clientId={clientId}
        client={client}
        onSaved={() => {
          fetchContracts()
          setTab("contracts")
        }}
      />

      <PersonFormSheet
        open={addPersonOpen}
        onOpenChange={setAddPersonOpen}
        clientId={clientId}
        client={client}
        lockType={PersonType.CLIENT_EMPLOYEE}
        onSaved={() => {
          setTab("staff")
        }}
      />

      <div className="min-h-0 flex-1 overflow-y-auto bg-bg">
        <div className="grid grid-cols-12 gap-5 px-5 py-5">
          <div className="col-span-12 min-w-0 lg:col-span-8">
            <Tabs value={tab} onValueChange={(v) => setTab(v as TabValue)}>
              <TabsList className="-mx-3 mb-4 px-3">
                <Tab value="overview">Overview</Tab>
                <Tab value="activity">Activity</Tab>
                <Tab value="contracts" count={contracts.length}>
                  Contracts
                </Tab>
                <Tab value="staff">Staff</Tab>
              </TabsList>

              <TabPanel value="overview">
                <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
                  <ClientAlertsCard alerts={alerts} />
                  <ClientUpcomingCard items={upcomingItems} />
                  <ClientOnboardingCard steps={onboardingSteps} />
                  <ClientTodaysTodoCard items={todaysTodoItems} />
                </div>
                <div className="mt-4">
                  <EmailCampaignCard />
                </div>
              </TabPanel>

              <TabPanel value="activity">
                <ClientActivityCard clientId={clientId} limit={20} />
              </TabPanel>

              <TabPanel value="contracts">
                <ContractsPanel
                  contracts={contracts}
                  loading={contractsLoading}
                  onAdd={() => setAddContractOpen(true)}
                />
              </TabPanel>

              <TabPanel value="staff">
                <div className="space-y-3">
                  <div className="flex items-center justify-between">
                    <p className="text-xs text-fg/55">
                      Employees, dependents and providers linked to this client.
                    </p>
                    <Button
                      size="sm"
                      variant="outline"
                      className="h-7 gap-1.5 px-2.5"
                      onClick={() => setAddPersonOpen(true)}
                    >
                      <Plus className="size-3.5" />
                      Add person
                    </Button>
                  </div>
                  <ClientStaffSummaryCard clientId={clientId} />
                </div>
              </TabPanel>
            </Tabs>
          </div>

          <aside className="col-span-12 min-w-0 lg:col-span-4 lg:pt-14">
            <DetailRail
              client={client}
              stats={stats}
              statsLoading={statsLoading}
              tags={tags}
              tagsLoading={tagsLoading}
              children={children}
              childrenLoading={childrenLoading}
              onAction={handleAction}
              actionLoading={actionLoading}
            />
          </aside>
        </div>
      </div>
    </PageShell>
  )
}

function Hero({ client, verified }: { client: Client; verified: boolean }) {
  return (
    <div className="flex shrink-0 items-center gap-3 border-b border-fg/10 bg-surface px-5 py-3">
      <span
        aria-hidden
        className="grid size-9 shrink-0 place-items-center rounded-sm bg-primary/10 font-mono text-xs font-semibold text-primary"
      >
        {initial(client.name)}
      </span>
      <h1 className="shrink truncate text-base font-semibold leading-tight text-fg">
        {client.name}
      </h1>
      <span className="font-mono text-xs text-fg/55">{client.code}</span>
      <span className="h-4 w-px shrink-0 bg-fg/15" aria-hidden />
      <StatusBadge status={client.status} />
      <TierBadge tier={client.tier} />
      {verified ? (
        <span className="inline-flex items-center gap-1 rounded-sm border border-primary/30 bg-primary/10 px-1.5 py-0.5 text-[11px] font-medium text-primary">
          <BadgeCheck className="size-3" />
          Verified
        </span>
      ) : null}
    </div>
  )
}

function ContractsPanel({
  contracts,
  loading,
  onAdd,
}: {
  contracts: Contract[]
  loading: boolean
  onAdd: () => void
}) {
  const [sort, setSort] = useState<SortState>({ field: undefined, desc: false })
  const toggleSort = (field: string) => setSort((prev) => nextSort(prev, field))
  const sorted = compareSort(contracts, sort, (row, field) => {
    if (field === "number") return row.contract_number ?? row.id
    return (row as unknown as Record<string, unknown>)[field]
  })

  if (loading) {
    return <p className="text-sm text-fg/65">Loading contracts…</p>
  }
  if (contracts.length === 0) {
    return (
      <EmptyState
        title="No contracts yet"
        description="Add a contract once it's signed."
        action={
          <Button size="sm" className="gap-1.5" onClick={onAdd}>
            <Plus className="size-4" />
            Add contract
          </Button>
        }
      />
    )
  }
  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between">
        <p className="text-xs text-fg/55">
          {contracts.length} contract{contracts.length === 1 ? "" : "s"}
        </p>
        <Button size="sm" variant="outline" className="h-7 gap-1.5 px-2.5" onClick={onAdd}>
          <Plus className="size-3.5" />
          Add contract
        </Button>
      </div>
      <div className="overflow-hidden border border-fg/10 bg-surface">
      <Table className="w-full caption-bottom text-sm">
        <TableHeader className="border-b-0 bg-surface shadow-[inset_0_-1px_0_rgb(0_0_0/0.08)]">
          <TableRow className={`hover:bg-transparent ${ROW_BORDER}`}>
            <TableHead>
              <SortHeader field="number" sort={sort} onToggle={toggleSort}>
                Number
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
            <TableHead className="w-10 text-right text-fg/65">
              <span className="sr-only">Open</span>
            </TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {sorted.map((c) => (
            <TableRow key={c.id} className={`group ${ROW_BORDER}`}>
              <TableCell>
                <Link
                  to="/contracts/$contractId"
                  params={{ contractId: c.id }}
                  className="font-medium text-fg group-hover:text-primary"
                >
                  {c.contract_number ?? c.id}
                </Link>
              </TableCell>
              <TableCell>
                <StatusBadge status={c.status} />
              </TableCell>
              <TableCell className="text-sm text-fg/75">{c.start_date}</TableCell>
              <TableCell className="text-sm text-fg/75">{c.end_date ?? "—"}</TableCell>
              <TableCell className="text-right">
                <Link
                  to="/contracts/$contractId"
                  params={{ contractId: c.id }}
                  aria-label="Open contract"
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

interface DetailRailProps {
  client: Client
  stats: ClientStats | null
  statsLoading: boolean
  tags: ClientTag[]
  tagsLoading: boolean
  children: Client[]
  childrenLoading: boolean
  onAction: (id: string, action: LifecycleAction) => Promise<void>
  actionLoading: boolean
}

function DetailRail({
  client,
  stats,
  statsLoading,
  tags,
  tagsLoading,
  children,
  childrenLoading,
  onAction,
  actionLoading,
}: DetailRailProps) {
  const ba = client.billing_address
  const hasBilling = !!(ba?.street || ba?.city || ba?.postal_code || ba?.country)
  return (
    <div className="space-y-5">
      <RailSection title="At a glance">
        <div className="grid grid-cols-2 gap-3">
          <Stat label="Child clients" value={statsLoading ? "…" : fmtCount(stats?.child_count)} />
          <Stat label="Contracts" value={statsLoading ? "…" : fmtCount(stats?.contract_count)} />
        </div>
      </RailSection>

      <RailSection title="Contact">
        <DetailGrid>
          <DetailRow label="Email" value={client.contact_info?.email} />
          <DetailRow label="Phone" value={client.contact_info?.phone} />
          <DetailRow label="Address" value={client.contact_info?.address} fullWidth />
          {client.preferred_contact_method ? (
            <DetailRow
              label="Preferred"
              value={client.preferred_contact_method}
            />
          ) : null}
        </DetailGrid>
      </RailSection>

      <RailSection title="Billing address">
        {hasBilling ? (
          <DetailGrid>
            {ba?.street ? <DetailRow label="Street" value={ba.street} fullWidth /> : null}
            {ba?.city ? <DetailRow label="City" value={ba.city} /> : null}
            {ba?.postal_code ? <DetailRow label="Postal" value={ba.postal_code} /> : null}
            {ba?.country ? <DetailRow label="Country" value={ba.country} /> : null}
          </DetailGrid>
        ) : (
          <p className="text-xs text-fg/55">No billing address on file.</p>
        )}
      </RailSection>

      {client.parent_client_id || children.length > 0 ? (
        <RailSection title="Hierarchy">
          {client.parent_client_id ? (
            <Link
              to="/clients/$clientId"
              params={{ clientId: client.parent_client_id }}
              className="inline-flex items-center gap-1.5 text-sm text-primary hover:underline"
            >
              <ArrowLeft className="size-3.5" />
              Parent client
            </Link>
          ) : null}
          {childrenLoading ? (
            <p className="mt-2 text-xs text-fg/55">Loading children…</p>
          ) : children.length > 0 ? (
            <ul className="mt-2 space-y-1">
              {children.map((c) => (
                <li key={c.id}>
                  <Link
                    to="/clients/$clientId"
                    params={{ clientId: c.id }}
                    className="inline-flex items-center gap-1.5 text-sm text-fg hover:text-primary"
                  >
                    <ChevronRight className="size-3.5 text-fg/45" />
                    <span className="truncate">{c.name}</span>
                    <span className="font-mono text-[11px] text-fg/55">{c.code}</span>
                  </Link>
                </li>
              ))}
            </ul>
          ) : null}
        </RailSection>
      ) : null}

      <RailSection title="Tags">
        {tagsLoading ? (
          <p className="text-xs text-fg/55">Loading…</p>
        ) : tags.length === 0 ? (
          <p className="text-xs text-fg/55">No tags assigned.</p>
        ) : (
          <div className="flex flex-wrap gap-1.5">
            {tags.map((t) => (
              <span
                key={t.id}
                className="inline-flex items-center gap-1.5 rounded-sm border border-fg/15 bg-bg px-1.5 py-0.5 text-xs text-fg"
              >
                <span
                  aria-hidden
                  className="block size-2 border border-fg/15"
                  style={t.color ? { backgroundColor: t.color } : undefined}
                />
                {t.name}
              </span>
            ))}
          </div>
        )}
      </RailSection>

      <RailSection title="Lifecycle">
        <LifecycleActions
          entityId={client.id}
          currentStatus={client.status}
          kind="client"
          onAction={onAction}
          loading={actionLoading}
        />
      </RailSection>
    </div>
  )
}

function RailSection({
  title,
  children,
  className,
}: {
  title: string
  children: React.ReactNode
  className?: string
}) {
  return (
    <section className={cn("space-y-2", className)}>
      <h3 className="text-xs font-semibold tracking-wide text-fg/55">
        {title}
      </h3>
      {children}
    </section>
  )
}

function Stat({ label, value }: { label: string; value: React.ReactNode }) {
  return (
    <div className="rounded-sm border border-fg/10 bg-surface px-3 py-2">
      <div className="text-[11px] font-medium tracking-wide text-fg/55">
        {label}
      </div>
      <div className="mt-0.5 font-mono text-base font-semibold text-fg">{value}</div>
    </div>
  )
}

function DetailGrid({ children }: { children: React.ReactNode }) {
  return <dl className="grid grid-cols-2 gap-x-3 gap-y-2.5">{children}</dl>
}

function DetailRow({
  label,
  value,
  fullWidth,
}: {
  label: string
  value: React.ReactNode
  fullWidth?: boolean
}) {
  return (
    <div className={cn(fullWidth && "col-span-2")}>
      <dt className="text-[11px] font-medium tracking-wide text-fg/55">
        {label}
      </dt>
      <dd className="mt-0.5 truncate text-sm text-fg">
        {value || <span className="text-fg/40">—</span>}
      </dd>
    </div>
  )
}

function fmtCount(n: number | null | undefined): string {
  if (n == null) return "—"
  return n.toLocaleString()
}

function initial(name: string): string {
  const trimmed = name.trim()
  if (!trimmed) return "·"
  const parts = trimmed.split(/\s+/)
  if (parts.length >= 2) return (parts[0][0] + parts[1][0]).toUpperCase()
  return trimmed.slice(0, 2).toUpperCase()
}
