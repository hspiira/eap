import { createFileRoute, Link, useNavigate } from "@tanstack/react-router"
import { useCallback, useEffect, useMemo, useState } from "react"
import { clientsApi } from "@/api/endpoints/clients"
import { contractsApi } from "@/api/endpoints/contracts"
import type { Client, ClientStats, ClientTag, Contract } from "@/types/entities"
import { ClientActivityCard } from "@/components/ClientActivityCard"
import { ClientAlertsCard } from "@/components/ClientAlertsCard"
import type { ClientAlert } from "@/components/ClientAlertsCard"
import { ClientOnboardingCard } from "@/components/ClientOnboardingCard"
import type { ClientOnboardingStep } from "@/components/ClientOnboardingCard"
import { ClientStaffSummaryCard } from "@/components/ClientStaffSummaryCard"
import { ClientTodaysTodoCard } from "@/components/ClientTodaysTodoCard"
import type { ClientTodaysTodoItem } from "@/components/ClientTodaysTodoCard"
import { ClientUpcomingCard } from "@/components/ClientUpcomingCard"
import type { ClientUpcomingItem } from "@/components/ClientUpcomingCard"
import { EmailCampaignCard } from "@/components/EmailCampaignCard"
import { ClientsPageHeader } from "@/components/ClientsPageHeader"
import { ClientDetailSkeleton } from "@/components/ClientsPageSkeletons"
import { LifecycleActions } from "@/components/common/LifecycleActions"
import { StatusBadge } from "@/components/common/StatusBadge"
import { Button } from "@/components/ui/button"
import { Skeleton } from "@/components/ui/skeleton"
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"
import { cn } from "@/lib/utils"
import type { LifecycleAction } from "@/utils/lifecycleConfig"

export const Route = createFileRoute("/clients/$clientId")({
  component: ClientDetailPage,
})

const skeletonClass = "rounded-none bg-[#5A626A]/15"

function Section({
  title,
  children,
  className,
}: {
  title: string
  children: React.ReactNode
  className?: string
}) {
  return (
    <div className={cn("border border-[#5A626A]/30 rounded-none bg-[#fafafa] overflow-hidden", className)}>
      <div className="px-6 py-3 border-b border-[#5A626A]/20 bg-[#E6E0D7]/20">
        <h2 className="text-sm font-medium text-[#5A626A]">{title}</h2>
      </div>
      <div className="px-6 py-4">{children}</div>
    </div>
  )
}

function DetailRow({ label, value }: { label: string; value: React.ReactNode }) {
  return (
    <div>
      <dt className="text-xs font-medium uppercase tracking-wide text-[#5A626A]/70">{label}</dt>
      <dd className="mt-1 text-[#5A626A]">{value ?? "—"}</dd>
    </div>
  )
}

function ClientDetailPage() {
  const { clientId } = Route.useParams()
  const navigate = useNavigate()
  const [client, setClient] = useState<Client | null>(null)
  const [loading, setLoading] = useState(true)
  const [actionLoading, setActionLoading] = useState(false)
  const [stats, setStats] = useState<ClientStats | null>(null)
  const [statsLoading, setStatsLoading] = useState(false)
  const [children, setChildren] = useState<Client[]>([])
  const [childrenLoading, setChildrenLoading] = useState(false)
  const [contracts, setContracts] = useState<Contract[]>([])
  const [contractsLoading, setContractsLoading] = useState(false)
  const [tags, setTags] = useState<ClientTag[]>([])
  const [tagsLoading, setTagsLoading] = useState(false)

  const fetchClient = useCallback(async () => {
    try {
      setLoading(true)
      const data = await clientsApi.getById(clientId)
      setClient(data)
    } catch {
      setClient(null)
    } finally {
      setLoading(false)
    }
  }, [clientId])

  useEffect(() => {
    fetchClient()
  }, [fetchClient])

  useEffect(() => {
    if (!client) return
    setStatsLoading(true)
    setChildrenLoading(true)
    setContractsLoading(true)
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

    contractsApi
      .list({ limit: 20, ...({ client_id: clientId } as Record<string, unknown>) })
      .then((res) => {
        const items = (res.items ?? []).filter((c: Contract) => c.client_id === clientId)
        setContracts(items.slice(0, 10))
      })
      .catch(() => setContracts([]))
      .finally(() => setContractsLoading(false))

    clientsApi
      .getTags(clientId)
      .then(setTags)
      .catch(() => setTags([]))
      .finally(() => setTagsLoading(false))
  }, [client, clientId])

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
      } finally {
        setActionLoading(false)
      }
    },
    [fetchClient]
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

  const alerts = useMemo((): ClientAlert[] => {
    if (!client) return []
    const list: ClientAlert[] = []
    if (!(client.is_verified ?? stats?.is_verified)) {
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
  }, [client, stats?.is_verified, hasBilling, contracts])

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
      { id: "billing", label: "Billing address set", done: !!hasBilling },
      { id: "verified", label: "Client verified", done: !!(client.is_verified ?? stats?.is_verified) },
    ]
  }, [client, stats?.is_verified, contracts.length, hasBilling])

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
      <ClientsPageHeader breadcrumb="Clients > …">
        <div className="content-area-scroll flex-1 min-h-0 overflow-x-auto overflow-y-auto p-4">
          <ClientDetailSkeleton />
        </div>
      </ClientsPageHeader>
    )
  }

  if (!client) {
    return (
      <div className="content-area-scroll flex-1 min-h-0 overflow-x-auto overflow-y-auto p-4">
        <div className="border border-[#5A626A]/20 rounded-none bg-[#E6E0D7]/20 p-8 text-center">
          <p className="text-[#5A626A]">Client not found.</p>
          <Button
            variant="secondary"
            className="mt-4 rounded-none border-[#5A626A]/30 text-[#5A626A]"
            onClick={() => navigate({ to: "/clients" })}
          >
            Back to clients
          </Button>
        </div>
      </div>
    )
  }

  const hasBillingDisplay =
    client.billing_address &&
    (client.billing_address.street ||
      client.billing_address.city ||
      client.billing_address.postal_code ||
      client.billing_address.country)

  return (
    <ClientsPageHeader breadcrumb={`Clients > ${client.name}`}>
      <div className="content-area-scroll flex-1 min-h-0 overflow-x-auto overflow-y-auto p-4 space-y-4">
        <div className="border border-[#5A626A]/30 rounded-none bg-[#fafafa] overflow-hidden">
          <div className="px-6 py-5 border-b border-[#5A626A]/20 bg-[#E6E0D7]/30">
            <div className="flex flex-wrap items-center gap-2">
              <h1 className="text-xl font-semibold text-[#5A626A]">{client.name}</h1>
              <StatusBadge status={client.status} />
              {(client.is_verified ?? stats?.is_verified) && (
                <span className="text-xs font-medium px-2 py-0.5 border border-natural bg-natural/20 text-[#5A626A]">
                  Verified
                </span>
              )}
            </div>
            <p className="text-sm text-[#5A626A]/70 mt-1">Code: {client.code}</p>
          </div>

          <div className="px-6 py-5">
            <h2 className="text-sm font-medium text-[#5A626A] mb-3">Contact</h2>
            <dl className="grid gap-4 sm:grid-cols-2">
              <DetailRow label="Email" value={client.contact_info?.email} />
              <DetailRow label="Phone" value={client.contact_info?.phone} />
              <DetailRow label="Address" value={client.contact_info?.address} />
              {client.preferred_contact_method && (
                <DetailRow label="Preferred contact" value={client.preferred_contact_method} />
              )}
            </dl>
          </div>

          {hasBillingDisplay && (
            <div className="px-6 py-5 border-t border-[#5A626A]/15">
              <h2 className="text-sm font-medium text-[#5A626A] mb-3">Billing address</h2>
              <dl className="grid gap-2 sm:grid-cols-2">
                {client.billing_address?.street && (
                  <DetailRow label="Street" value={client.billing_address.street} />
                )}
                {client.billing_address?.city && (
                  <DetailRow label="City" value={client.billing_address.city} />
                )}
                {client.billing_address?.postal_code && (
                  <DetailRow label="Postal code" value={client.billing_address.postal_code} />
                )}
                {client.billing_address?.country && (
                  <DetailRow label="Country" value={client.billing_address.country} />
                )}
              </dl>
            </div>
          )}

          {client.parent_client_id && (
            <div className="px-6 py-3 border-t border-[#5A626A]/15">
              <span className="text-xs font-medium uppercase tracking-wide text-[#5A626A]/70">
                Parent client
              </span>
              <p className="mt-1">
                <Link
                  to="/clients/$clientId"
                  params={{ clientId: client.parent_client_id }}
                  className="text-natural hover:underline"
                >
                  View parent client
                </Link>
              </p>
            </div>
          )}
        </div>

        <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
          <ClientAlertsCard alerts={alerts} />
          <ClientUpcomingCard items={upcomingItems} />
        </div>

        <EmailCampaignCard />

        <div className="grid grid-cols-1 gap-4 lg:grid-cols-3">
          <div className="lg:col-span-2">
            <ClientActivityCard clientId={clientId} limit={10} />
          </div>
          <div className="space-y-4">
            <Section title="Overview">
          {statsLoading ? (
            <div className="grid grid-cols-2 gap-4">
              <Skeleton className={cn(skeletonClass, "h-12 w-full")} />
              <Skeleton className={cn(skeletonClass, "h-12 w-full")} />
            </div>
          ) : (
            <dl className="grid grid-cols-2 gap-4">
              <DetailRow
                label="Child clients"
                value={stats?.child_count != null ? String(stats.child_count) : "—"}
              />
              <DetailRow
                label="Contracts"
                value={stats?.contract_count != null ? String(stats.contract_count) : "—"}
              />
            </dl>
          )}
            </Section>

            <ClientStaffSummaryCard clientId={clientId} />
            <ClientTodaysTodoCard items={todaysTodoItems} />

            <Section title="Child clients">
          {childrenLoading ? (
            <Table>
              <TableHeader>
                <TableRow className="hover:bg-transparent border-[#5A626A]/15">
                  <TableHead className="text-[#5A626A]">Name</TableHead>
                  <TableHead className="text-[#5A626A]">Code</TableHead>
                  <TableHead className="text-[#5A626A]">Status</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {[1, 2, 3].map((i) => (
                  <TableRow key={i}>
                    <TableCell><Skeleton className={cn(skeletonClass, "h-4 w-24")} /></TableCell>
                    <TableCell><Skeleton className={cn(skeletonClass, "h-4 w-12")} /></TableCell>
                    <TableCell><Skeleton className={cn(skeletonClass, "h-5 w-14")} /></TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          ) : children.length === 0 ? (
            <p className="text-sm text-[#5A626A]/80">No child clients.</p>
          ) : (
            <Table>
              <TableHeader>
                <TableRow className="hover:bg-transparent border-[#5A626A]/15">
                  <TableHead className="text-[#5A626A]">Name</TableHead>
                  <TableHead className="text-[#5A626A]">Code</TableHead>
                  <TableHead className="text-[#5A626A]">Status</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {children.map((c) => (
                  <TableRow key={c.id}>
                    <TableCell>
                      <Link to="/clients/$clientId" params={{ clientId: c.id }} className="text-natural hover:underline">
                        {c.name}
                      </Link>
                    </TableCell>
                    <TableCell className="text-[#5A626A]">{c.code}</TableCell>
                    <TableCell><StatusBadge status={c.status} /></TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
            </Section>

            <Section title="Contracts">
          {contractsLoading ? (
            <Table>
              <TableHeader>
                <TableRow className="hover:bg-transparent border-[#5A626A]/15">
                  <TableHead className="text-[#5A626A]">Number</TableHead>
                  <TableHead className="text-[#5A626A]">Status</TableHead>
                  <TableHead className="text-[#5A626A]">Dates</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {[1, 2].map((i) => (
                  <TableRow key={i}>
                    <TableCell><Skeleton className={cn(skeletonClass, "h-4 w-20")} /></TableCell>
                    <TableCell><Skeleton className={cn(skeletonClass, "h-5 w-16")} /></TableCell>
                    <TableCell><Skeleton className={cn(skeletonClass, "h-4 w-28")} /></TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          ) : contracts.length === 0 ? (
            <p className="text-sm text-[#5A626A]/80">No contracts.</p>
          ) : (
            <Table>
              <TableHeader>
                <TableRow className="hover:bg-transparent border-[#5A626A]/15">
                  <TableHead className="text-[#5A626A]">Number</TableHead>
                  <TableHead className="text-[#5A626A]">Status</TableHead>
                  <TableHead className="text-[#5A626A]">Dates</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {contracts.map((c) => (
                  <TableRow key={c.id}>
                    <TableCell>
                      <Link to="/contracts/$contractId" params={{ contractId: c.id }} className="text-natural hover:underline">
                        {c.contract_number ?? c.id}
                      </Link>
                    </TableCell>
                    <TableCell><StatusBadge status={c.status} /></TableCell>
                    <TableCell className="text-[#5A626A] text-sm">
                      {c.start_date}
                      {c.end_date ? ` – ${c.end_date}` : ""}
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
            </Section>

            <Section title="Tags">
          {tagsLoading ? (
            <div className="flex flex-wrap gap-2">
              <Skeleton className={cn(skeletonClass, "h-6 w-20")} />
              <Skeleton className={cn(skeletonClass, "h-6 w-24")} />
            </div>
          ) : tags.length === 0 ? (
            <p className="text-sm text-[#5A626A]/80">No tags.</p>
          ) : (
            <div className="flex flex-wrap gap-2">
              {tags.map((t) => (
                <span
                  key={t.id}
                  className="inline-flex items-center px-2 py-0.5 text-xs font-medium border border-[#5A626A]/30 bg-[#E6E0D7]/50 text-[#5A626A] rounded-none"
                >
                  {t.name}
                </span>
              ))}
            </div>
          )}
            </Section>

            <ClientOnboardingCard steps={onboardingSteps} />

            <div className="border border-[#5A626A]/30 rounded-none bg-[#fafafa] overflow-hidden">
              <div className="px-6 py-4 border-b border-[#5A626A]/20 bg-[#E6E0D7]/20">
                <h2 className="text-sm font-medium text-[#5A626A]">Actions</h2>
              </div>
              <div className="px-6 py-4">
                <LifecycleActions
                  entityId={client.id}
                  currentStatus={client.status}
                  kind="client"
                  onAction={handleAction}
                  loading={actionLoading}
                />
              </div>
            </div>
          </div>
        </div>
      </div>
    </ClientsPageHeader>
  )
}
