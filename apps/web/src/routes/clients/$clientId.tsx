import { useCallback, useEffect, useMemo, useState } from "react"

import { useQuery, useQueryClient } from "@tanstack/react-query"
import { createFileRoute, useNavigate } from "@tanstack/react-router"
import { Building2, Pencil } from "lucide-react"

import { clientsApi } from "@/api/endpoints/clients"
import { contactsApi } from "@/api/endpoints/contacts"
import { contractsApi } from "@/api/endpoints/contracts"
import { personsApi } from "@/api/endpoints/persons"
import { ClientActivityCard } from "@/components/clients/ClientActivityCard"
import type { ClientAlert } from "@/components/clients/ClientAlertsCard"
import { ClientAlertsCard } from "@/components/clients/ClientAlertsCard"
import { ContractsPanel, DetailRail, Hero } from "@/components/clients/ClientDetailWidgets"
import { ClientFormSheet } from "@/components/clients/ClientFormSheet"
import {
  ClientContactsPanel,
  ClientDocumentsPanel,
  ClientHealthCard,
  ClientRosterPanel,
  ClientServicesPanel,
  ClientUtilisationPanel,
} from "@/components/clients/ClientManagementPanels"
import type { ClientOnboardingStep } from "@/components/clients/ClientOnboardingCard"
import { ClientOnboardingCard } from "@/components/clients/ClientOnboardingCard"
import type { ClientTodaysTodoItem } from "@/components/clients/ClientTodaysTodoCard"
import { ClientTodaysTodoCard } from "@/components/clients/ClientTodaysTodoCard"
import type { ClientUpcomingItem } from "@/components/clients/ClientUpcomingCard"
import { ClientUpcomingCard } from "@/components/clients/ClientUpcomingCard"
import { renderDetailState } from "@/components/common/DetailStates"
import { PageShell } from "@/components/common/PageShell"
import { Tab, TabPanel, Tabs, TabsList } from "@/components/common/Tabs"
import { ContractFormSheet } from "@/components/ContractFormSheet"
import { PersonFormSheet } from "@/components/PersonFormSheet"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { useToast } from "@/contexts/ToastContext"
import { useTabSearchParam } from "@/hooks/useTabSearchParam"
import { normalizeErrorMessage } from "@/lib/errors"
import { addDaysToDay, daysBetweenDays, formatDay, todayDayKey, toDayKey } from "@/lib/format"
import { entityDetailKey, entityListKey, useEntityDetail } from "@/lib/queries"
import { useAuthStore } from "@/store/slices/authSlice"
import type { Client } from "@/types/entities"
import type { ClientTier } from "@/types/enums"
import { PersonType } from "@/types/enums"
import type { LifecycleAction } from "@/utils/lifecycleConfig"

export const Route = createFileRoute("/clients/$clientId")({
  component: ClientDetailPage,
})

type TabValue =
  "overview" | "activity" | "contracts" | "staff" | "services" | "documents" | "utilisation"
const TAB_VALUES: ReadonlyArray<TabValue> = [
  "overview",
  "activity",
  "contracts",
  "staff",
  "services",
  "documents",
  "utilisation",
]

const CLIENTS_LIST_SEARCH = {
  page: undefined,
  limit: undefined,
  search: undefined,
  sort: undefined,
  tier: undefined,
} as const

const CONTRACTS_PAGE = 10
const UPCOMING_DAYS = 90
const ALERT_DAYS = 30
/** The list endpoint caps limit at 100. Past that the window is reported as partial. */
const WINDOW_PAGE = 100

function ClientDetailPage() {
  const { clientId } = Route.useParams()
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const [actionLoading, setActionLoading] = useState(false)
  const toast = useToast()
  const userId = useAuthStore((s) => s.user_id)
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
    queryKey: entityListKey("contracts", { client_id: clientId, limit: CONTRACTS_PAGE }),
    queryFn: () => contractsApi.list({ limit: CONTRACTS_PAGE, client_id: clientId }),
    enabled,
  })
  const contracts = contractsQuery.data?.items ?? []
  const contractsTotal = contractsQuery.data?.total ?? 0

  const contactsQuery = useQuery({
    queryKey: entityListKey("contacts", { client_id: clientId }),
    queryFn: () => contactsApi.byClient(clientId),
    enabled,
  })
  const contacts = contactsQuery.data ?? []
  const rosterQuery = useQuery({
    queryKey: entityListKey("persons", { client_id: clientId, limit: 100 }),
    queryFn: () => personsApi.list({ client_id: clientId, limit: 100 }),
    enabled,
  })
  const rosterCount = rosterQuery.data?.total ?? rosterQuery.data?.items.length ?? 0

  // Alerts and the upcoming list need every contract ending in the window, not
  // the first page of all of them. Anchored to the day so the key is stable.
  const endWindow = useMemo(() => {
    const from = todayDayKey()
    return { ends_from: from, ends_to: addDaysToDay(from, UPCOMING_DAYS) }
  }, [])

  const endingQuery = useQuery({
    queryKey: entityListKey("contracts", {
      client_id: clientId,
      ...endWindow,
      limit: WINDOW_PAGE,
    }),
    queryFn: () => contractsApi.list({ client_id: clientId, ...endWindow, limit: WINDOW_PAGE }),
    enabled,
  })
  const ending = endingQuery.data?.items ?? []
  const endingTotal = endingQuery.data?.total ?? 0
  const endingTruncated = endingTotal > ending.length

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
        toast.showError(normalizeErrorMessage(err, "Action failed: please try again"))
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

  const handleVerify = useCallback(async () => {
    if (!userId) {
      toast.showError("Your user identity is not available")
      return
    }
    setActionLoading(true)
    try {
      const updated = await clientsApi.verify(clientId, userId)
      queryClient.setQueryData(entityDetailKey("clients", clientId), updated)
      await queryClient.invalidateQueries({ queryKey: ["clients", "stats", clientId] })
      toast.showSuccess("Client verified")
    } catch (err) {
      toast.showError(normalizeErrorMessage(err, "Verification failed"))
    } finally {
      setActionLoading(false)
    }
  }, [clientId, queryClient, toast, userId])

  const hasSeparateBilling = client
    ? !!(
        client.billing_address &&
        (client.billing_address.street ||
          client.billing_address.city ||
          client.billing_address.postal_code ||
          client.billing_address.country)
      )
    : false
  const hasBilling = hasSeparateBilling || !!client?.contact_info?.address

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
    const today = todayDayKey()
    ending.forEach((c) => {
      const untilEnd = daysBetweenDays(today, c.period.end_date)
      if (untilEnd != null && untilEnd >= 0 && untilEnd <= ALERT_DAYS) {
        list.push({
          id: `contract-expiring-${c.id}`,
          title: `Contract ending soon: ${c.id.slice(0, 8)}`,
          description: `End date: ${formatDay(c.period.end_date)}`,
          severity: "high",
          link: `/contracts/${c.id}`,
          linkLabel: "View contract",
        })
      }
    })
    if (endingTruncated) {
      list.push({
        id: "contracts-truncated",
        title: "Too many contracts to check",
        description: `${endingTotal} contracts end in the next ${UPCOMING_DAYS} days. Only the first ${WINDOW_PAGE} were checked.`,
        severity: "medium",
        link: "/contracts",
        linkLabel: "View all contracts",
      })
    }
    return list
  }, [client, isVerified, hasBilling, ending, endingTruncated, endingTotal])

  const upcomingItems = useMemo((): ClientUpcomingItem[] => {
    const list: ClientUpcomingItem[] = []
    const today = todayDayKey()
    ending.forEach((c) => {
      // One item per contract: the term end is either a renewal or an ending,
      // decided by is_auto_renew. This used to branch on a renewal_date field the
      // BE has never sent, so neither branch ever fired.
      {
        const untilEnd = daysBetweenDays(today, c.period.end_date)
        if (untilEnd != null && untilEnd >= 0 && untilEnd <= UPCOMING_DAYS) {
          list.push({
            id: `${c.is_auto_renew ? "renewal" : "end"}-${c.id}`,
            title: `${c.is_auto_renew ? "Contract renewal" : "Contract ends"}: ${c.id.slice(0, 8)}`,
            date: toDayKey(c.period.end_date),
            context: c.is_auto_renew ? "Renewal" : "End date",
            link: `/contracts/${c.id}`,
            linkLabel: "View",
          })
        }
      }
    })
    return list.slice(0, 5).sort((a, b) => a.date.localeCompare(b.date))
  }, [ending])

  const onboardingSteps = useMemo((): ClientOnboardingStep[] => {
    if (!client) return []
    const hasContact = !!(client.contact_info?.email || client.contact_info?.phone)
    const hasContract = contractsTotal > 0
    return [
      { id: "contact", label: "Contact info added", done: hasContact },
      { id: "contract", label: "At least one contract", done: hasContract },
      { id: "billing", label: "Billing address set", done: hasBilling },
      { id: "verified", label: "Client verified", done: isVerified },
    ]
  }, [client, isVerified, contractsTotal, hasBilling])

  const todaysTodoItems = useMemo((): ClientTodaysTodoItem[] => {
    const today = todayDayKey()
    return upcomingItems
      .filter((u) => toDayKey(u.date) === today)
      .map((u) => ({
        id: u.id,
        title: u.title,
        time: u.time ?? null,
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
      trail={[
        { label: "Organization & Clients" },
        { label: "Clients", to: "/clients", search: CLIENTS_LIST_SEARCH },
      ]}
      title={client.name}
      actions={
        <Button
          size="sm"
          variant="outline"
          className="h-7 gap-1.5 px-2.5"
          onClick={() => setEditOpen(true)}
        >
          <Pencil className="size-3.5" />
          Edit
        </Button>
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
        <div className="grid grid-cols-12 gap-5 px-5 pb-5">
          <div className="col-span-12 min-w-0 lg:col-span-8">
            <Tabs value={tab} onValueChange={(v) => setTab(v as TabValue)}>
              <div className="sticky top-0 z-20 -mx-3 mb-4 bg-bg/95 px-3 backdrop-blur">
                <TabsList className="px-0">
                  <Tab value="overview">Overview</Tab>
                  <Tab value="activity">Activity</Tab>
                  <Tab value="contracts" count={contractsTotal}>
                    Contracts
                  </Tab>
                  <Tab value="staff">Staff</Tab>
                  <Tab value="services">Services</Tab>
                  <Tab value="documents">Documents</Tab>
                  <Tab value="utilisation">Usage</Tab>
                </TabsList>
              </div>

              <TabPanel value="overview">
                <div className="grid grid-cols-1 items-start gap-4 lg:grid-cols-2">
                  <div className="space-y-4">
                    <ClientHealthCard
                      client={client}
                      stats={stats}
                      contacts={contacts}
                      staffCount={rosterCount}
                      contracts={contracts}
                    />
                    <ClientAlertsCard alerts={alerts} />
                    <ClientOnboardingCard steps={onboardingSteps} />
                    <ClientAliasesCard
                      client={client}
                      onSaved={(updated) =>
                        queryClient.setQueryData(entityDetailKey("clients", updated.id), updated)
                      }
                    />
                  </div>
                  <div className="space-y-4">
                    <ClientContactsPanel clientId={clientId} client={client} contacts={contacts} />
                    <ClientUpcomingCard items={upcomingItems} />
                    <ClientTodaysTodoCard items={todaysTodoItems} />
                  </div>
                </div>
              </TabPanel>

              <TabPanel value="activity">
                <ClientActivityCard clientId={clientId} limit={20} />
              </TabPanel>

              <TabPanel value="contracts">
                <ContractsPanel
                  contracts={contracts}
                  total={contractsTotal}
                  loading={contractsQuery.isPending}
                  clientId={clientId}
                  onAdd={() => setAddContractOpen(true)}
                />
              </TabPanel>

              <TabPanel value="staff">
                <ClientRosterPanel clientId={clientId} onAdd={() => setAddPersonOpen(true)} />
              </TabPanel>

              <TabPanel value="services">
                <ClientServicesPanel contracts={contracts} />
              </TabPanel>

              <TabPanel value="documents">
                <ClientDocumentsPanel clientId={clientId} />
              </TabPanel>

              <TabPanel value="utilisation">
                <ClientUtilisationPanel contracts={contracts} />
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
              onVerify={handleVerify}
            />
          </aside>
        </div>
      </div>
    </PageShell>
  )
}

function ClientAliasesCard({
  client,
  onSaved,
}: {
  client: Client
  onSaved: (client: Client) => void
}) {
  const [draft, setDraft] = useState((client.aliases ?? []).join(", "))
  const [sourceClientId, setSourceClientId] = useState("")
  const [sourceSearch, setSourceSearch] = useState("")
  const [saving, setSaving] = useState(false)
  const [manageOpen, setManageOpen] = useState(false)
  const toast = useToast()
  const sourceQuery = useQuery({
    queryKey: ["clients", "alias-merge-search", sourceSearch],
    queryFn: () => clientsApi.list({ search: sourceSearch.trim(), limit: 8 }),
    enabled: manageOpen && sourceSearch.trim().length >= 2 && !sourceClientId,
  })

  useEffect(() => setDraft((client.aliases ?? []).join(", ")), [client.aliases])

  const save = async () => {
    setSaving(true)
    try {
      const updated = await clientsApi.updateAliases(
        client.id,
        draft
          .split(",")
          .map((alias) => alias.trim())
          .filter(Boolean),
      )
      onSaved(updated)
      setManageOpen(false)
      toast.showSuccess("Aliases updated")
    } catch (error) {
      toast.showError(normalizeErrorMessage(error, "Could not update aliases"))
    } finally {
      setSaving(false)
    }
  }

  const merge = async () => {
    const source = sourceClientId.trim()
    if (!source) return
    setSaving(true)
    try {
      const updated = await clientsApi.mergeAliases(client.id, source)
      onSaved(updated)
      setSourceClientId("")
      setSourceSearch("")
      setManageOpen(false)
      toast.showSuccess("Aliases merged")
    } catch (error) {
      toast.showError(normalizeErrorMessage(error, "Could not merge aliases"))
    } finally {
      setSaving(false)
    }
  }

  const aliases = client.aliases ?? []

  return (
    <section className="space-y-3 border border-fg/10 bg-surface p-4">
      <div className="flex items-start justify-between gap-3">
        <h2 className="text-sm font-semibold text-fg">Alternate names</h2>
        <Button
          type="button"
          size="sm"
          variant="outline"
          className="h-7 shrink-0"
          onClick={() => setManageOpen((open) => !open)}
        >
          {manageOpen ? "Done" : "Manage names"}
        </Button>
      </div>
      <p className="text-xs text-fg-muted">
        {aliases.length === 0
          ? "No alternate names added."
          : `${aliases.length} alternate name${aliases.length === 1 ? "" : "s"}`}
      </p>
      {aliases.length > 0 ? (
        <div className="flex flex-wrap gap-1.5">
          {aliases.map((alias) => (
            <span
              key={alias}
              className="rounded-sm border border-fg/10 bg-bg px-2 py-1 text-xs text-fg"
            >
              {alias}
            </span>
          ))}
        </div>
      ) : null}
      {manageOpen ? (
        <div className="space-y-3 border-t border-fg/8 pt-3">
          <div className="flex gap-2">
            <Input
              value={draft}
              onChange={(event) => setDraft(event.target.value)}
              placeholder="Separate aliases with commas"
              aria-label="Client aliases"
              className="h-8 text-xs"
            />
            <Button
              type="button"
              size="sm"
              className="h-8 shrink-0"
              disabled={saving}
              onClick={() => void save()}
            >
              {saving ? "Saving…" : "Save"}
            </Button>
          </div>
          <div className="relative border-t border-fg/8 pt-3">
            <div className="flex gap-2">
              <Input
                value={sourceSearch}
                onChange={(event) => {
                  setSourceSearch(event.target.value)
                  setSourceClientId("")
                }}
                placeholder="Find another client to merge aliases from"
                aria-label="Find client for alias merge"
                className="h-8 text-xs"
              />
              <Button
                type="button"
                variant="outline"
                size="sm"
                className="h-8 shrink-0"
                disabled={saving || !sourceClientId}
                onClick={() => void merge()}
              >
                Merge aliases
              </Button>
            </div>
            {sourceQuery.data?.items.length && !sourceClientId ? (
              <div className="absolute inset-x-0 top-12 z-10 border border-fg/15 bg-surface p-1 shadow-lg">
                {sourceQuery.data.items.map((candidate) => (
                  <Button
                    key={candidate.id}
                    type="button"
                    variant="ghost"
                    className="block h-auto w-full justify-start rounded-none px-2 py-1.5 text-left text-xs font-normal text-fg"
                    onClick={() => {
                      setSourceClientId(candidate.id)
                      setSourceSearch(candidate.name)
                    }}
                  >
                    {candidate.name} <span className="text-fg-muted">{candidate.code}</span>
                  </Button>
                ))}
              </div>
            ) : null}
          </div>
        </div>
      ) : null}
    </section>
  )
}
