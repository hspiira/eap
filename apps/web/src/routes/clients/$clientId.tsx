import { useCallback, useMemo, useState } from "react"

import { useQuery, useQueryClient } from "@tanstack/react-query"
import { createFileRoute, useNavigate } from "@tanstack/react-router"
import {
  ArrowLeft,
  Building2,
  Pencil,
  Plus,
} from "lucide-react"

import { clientsApi } from "@/api/endpoints/clients"
import { contractsApi } from "@/api/endpoints/contracts"
import { ClientActivityCard } from "@/components/ClientActivityCard"
import type { ClientAlert } from "@/components/ClientAlertsCard"
import { ClientAlertsCard } from "@/components/ClientAlertsCard"
import { ClientFormSheet } from "@/components/ClientFormSheet"
import type { ClientOnboardingStep } from "@/components/ClientOnboardingCard"
import { ClientOnboardingCard } from "@/components/ClientOnboardingCard"
import {
  ContractsPanel,
  DetailRail,
  Hero,
} from "@/components/clients/ClientDetailWidgets"
import { ClientStaffSummaryCard } from "@/components/ClientStaffSummaryCard"
import type { ClientTodaysTodoItem } from "@/components/ClientTodaysTodoCard"
import { ClientTodaysTodoCard } from "@/components/ClientTodaysTodoCard"
import type { ClientUpcomingItem } from "@/components/ClientUpcomingCard"
import { ClientUpcomingCard } from "@/components/ClientUpcomingCard"
import { renderDetailState } from "@/components/common/DetailStates"
import { PageShell } from "@/components/common/PageShell"
import { Tab, TabPanel, Tabs, TabsList } from "@/components/common/Tabs"
import { ContractFormSheet } from "@/components/ContractFormSheet"
import { EmailCampaignCard } from "@/components/EmailCampaignCard"
import { PersonFormSheet } from "@/components/PersonFormSheet"
import { Button } from "@/components/ui/button"
import { useToast } from "@/contexts/ToastContext"
import { useTabSearchParam } from "@/hooks/useTabSearchParam"
import { normalizeErrorMessage } from "@/lib/errors"
import { entityDetailKey, entityListKey, useEntityDetail } from "@/lib/queries"
import type { Client } from "@/types/entities"
import type { ClientTier} from "@/types/enums";
import { PersonType } from "@/types/enums"
import type { LifecycleAction } from "@/utils/lifecycleConfig"

export const Route = createFileRoute("/clients/$clientId")({
  component: ClientDetailPage,
})

type TabValue = "overview" | "activity" | "contracts" | "staff"
const TAB_VALUES: ReadonlyArray<TabValue> = ["overview", "activity", "contracts", "staff"]

function ClientDetailPage() {
  const { clientId } = Route.useParams()
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const [actionLoading, setActionLoading] = useState(false)
  const toast = useToast()
  const [tab, setTab] = useTabSearchParam<TabValue>(TAB_VALUES, "overview")
  const [tierLoading, setTierLoading] = useState(false)
  const [editOpen, setEditOpen] = useState(false)
  const [addContractOpen, setAddContractOpen] = useState(false)
  const [addPersonOpen, setAddPersonOpen] = useState(false)

  const clientQuery = useEntityDetail<Client>({
    resource: "clients",
    id: clientId,
    detailFn: clientsApi.getById,
  })
  const client = clientQuery.data ?? null

  // The related panels only make sense once the client itself resolves; gating
  // on it also stops them firing for an id that turns out not to exist.
  const enabled = !!client

  const statsQuery = useQuery({
    queryKey: ["clients", "stats", clientId],
    queryFn: () => clientsApi.getStats(clientId),
    enabled,
  })
  const stats = statsQuery.data ?? null

  const childrenQuery = useQuery({
    queryKey: entityListKey("clients", { parent: clientId, limit: 10 }),
    queryFn: () => clientsApi.getChildren(clientId, { limit: 10 }),
    enabled,
  })
  const children = childrenQuery.data?.items ?? []

  const contractsQuery = useQuery({
    queryKey: entityListKey("contracts", { client_id: clientId, limit: 10 }),
    queryFn: () => contractsApi.list({ limit: 10, client_id: clientId }),
    enabled,
  })
  const contracts = contractsQuery.data?.items ?? []

  const tagsQuery = useQuery({
    queryKey: ["client-tags", "for-client", clientId],
    queryFn: () => clientsApi.getTags(clientId),
    enabled,
  })
  const tags = tagsQuery.data ?? []

  const handleAction = useCallback(
    async (id: string, action: LifecycleAction) => {
      setActionLoading(true)
      try {
        if (action === "activate") await clientsApi.activate(id)
        else if (action === "deactivate") await clientsApi.deactivate(id)
        else if (action === "archive") await clientsApi.archive(id)
        else if (action === "restore") await clientsApi.restore(id)
        else if (action === "terminate") await clientsApi.terminate(id, "Terminated from UI")
        await queryClient.invalidateQueries({ queryKey: ["clients"] })
        toast.showSuccess("Status updated")
      } catch (err) {
        toast.showError(normalizeErrorMessage(err, "Action failed — please try again"))
      } finally {
        setActionLoading(false)
      }
    },
    [queryClient, toast],
  )

  const handleTierChange = useCallback(
    async (tier: ClientTier | null) => {
      setTierLoading(true)
      try {
        const updated = await clientsApi.setTier(clientId, tier)
        queryClient.setQueryData(entityDetailKey("clients", clientId), updated)
        toast.showSuccess("Tier updated")
      } catch (err) {
        toast.showError(normalizeErrorMessage(err, "Tier update failed"))
      } finally {
        setTierLoading(false)
      }
    },
    [clientId, queryClient, toast],
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
      const end = new Date(c.period.end_date)
      if (end <= in30Days && end >= now) {
        list.push({
          id: `contract-expiring-${c.id}`,
          title: `Contract ending soon: ${c.id.slice(0, 8)}`,
          description: `End date: ${end.toLocaleDateString()}`,
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
      // One item per contract: the term end is either a renewal or an ending,
      // decided by is_auto_renew. This used to branch on a renewal_date field the
      // BE has never sent, so neither branch ever fired.
      {
        const d = new Date(c.period.end_date)
        if (d >= now && d <= in90Days) {
          list.push({
            id: `${c.is_auto_renew ? "renewal" : "end"}-${c.id}`,
            title: `${c.is_auto_renew ? "Contract renewal" : "Contract ends"}: ${c.id.slice(0, 8)}`,
            date: c.period.end_date,
            context: c.is_auto_renew ? "Renewal" : "End date",
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

  const state = renderDetailState(clientQuery, {
    icon: Building2,
    breadcrumb: "Organization & Clients · Clients",
    entity: "client",
    backTo: () => navigate({ to: "/clients" }),
    backLabel: "Back to clients",
  })
  if (state || !client) return state

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
        onSaved={(updated) =>
          queryClient.setQueryData(entityDetailKey("clients", updated.id), updated)
        }
      />

      <ContractFormSheet
        open={addContractOpen}
        onOpenChange={setAddContractOpen}
        clientId={clientId}
        client={client}
        onSaved={() => {
          void queryClient.invalidateQueries({ queryKey: ["contracts"] })
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
                  loading={contractsQuery.isPending}
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
              statsLoading={statsQuery.isPending}
              tags={tags}
              tagsLoading={tagsQuery.isPending}
              children={children}
              childrenLoading={childrenQuery.isPending}
              onAction={handleAction}
              actionLoading={actionLoading}
              onTierChange={handleTierChange}
              tierLoading={tierLoading}
            />
          </aside>
        </div>
      </div>
    </PageShell>
  )
}

