import { useState } from "react"

import { useQueryClient } from "@tanstack/react-query"
import { createFileRoute, useNavigate } from "@tanstack/react-router"
import { Pencil, Stethoscope } from "lucide-react"

import { providersApi } from "@/api/endpoints/providers"
import { DetailCard, DetailGrid, DetailRow } from "@/components/common/DetailPrimitives"
import { renderDetailState } from "@/components/common/DetailStates"
import { PageShell } from "@/components/common/PageShell"
import { ProviderTierBadge } from "@/components/common/ProviderTierBadge"
import { SessionHistory } from "@/components/common/SessionHistory"
import { StatusBadge } from "@/components/common/StatusBadge"
import { Tab, TabPanel, Tabs, TabsList } from "@/components/common/Tabs"
import { ProviderAccountCard } from "@/components/providers/ProviderAccountCard"
import { ProviderAffiliationsPanel } from "@/components/providers/ProviderAffiliationsPanel"
import { ProviderFormSheet } from "@/components/providers/ProviderFormSheet"
import { ProviderLifecyclePanel } from "@/components/providers/ProviderLifecyclePanel"
import { ProviderNonCompetePanel } from "@/components/providers/ProviderNonCompetePanel"
import { Button } from "@/components/ui/button"
import { useCanWrite } from "@/hooks/useCanWrite"
import { useTabSearchParam } from "@/hooks/useTabSearchParam"
import { entityDetailKey, useEntityDetail } from "@/lib/queries"
import type { Provider } from "@/types/entities"
import { getStatusLabel } from "@/utils/statusColors"

export const Route = createFileRoute("/providers/$providerId")({
  component: ProviderDetailPage,
})

const TAB_VALUES = ["overview", "affiliations", "non-compete", "sessions"] as const
type TabValue = (typeof TAB_VALUES)[number]

function ProviderDetailPage() {
  const { providerId } = Route.useParams()
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const canWrite = useCanWrite()
  const [tab, setTab] = useTabSearchParam<TabValue>(TAB_VALUES, "overview")
  const [editOpen, setEditOpen] = useState(false)

  const query = useEntityDetail<Provider>({
    resource: "providers",
    id: providerId,
    detailFn: providersApi.getById,
  })

  const back = () => void navigate({ to: "/providers" })
  const state = renderDetailState(query, {
    icon: Stethoscope,
    breadcrumb: "Practitioners",
    entity: "practitioner",
    backTo: back,
    backLabel: "Back to practitioners",
  })
  if (state) return state

  const provider = query.data as Provider
  const profile = provider.provider_profile

  const refresh = () => {
    void queryClient.invalidateQueries({ queryKey: entityDetailKey("providers", provider.id) })
    void queryClient.invalidateQueries({ queryKey: ["providers", "list"] })
  }

  return (
    <PageShell
      icon={Stethoscope}
      trail={[{ label: "Practitioners", to: "/providers" }]}
      title={provider.display_name}
      actions={
        canWrite ? (
          <Button
            type="button"
            variant="outline"
            size="sm"
            className="h-7 gap-1.5 rounded-none px-2"
            onClick={() => setEditOpen(true)}
          >
            <Pencil className="size-3.5" />
            Edit
          </Button>
        ) : null
      }
    >
      <div className="flex flex-wrap items-center gap-2 border-b border-fg/10 bg-surface px-3 py-2">
        <ProviderTierBadge tier={profile.tier} />
        <span className="text-xs text-fg/70">{getStatusLabel(profile.region)}</span>
        <StatusBadge status={profile.panel_status} size="sm" />
        <StatusBadge status={profile.accreditation_status} size="sm" />
        <StatusBadge status={provider.status} size="sm" />
      </div>

      <ProviderFormSheet open={editOpen} onOpenChange={setEditOpen} provider={provider} />

      <Tabs value={tab} onValueChange={(value) => setTab(value as TabValue)}>
        <TabsList>
          <Tab value="overview">Overview</Tab>
          <Tab value="affiliations">Affiliations</Tab>
          <Tab value="non-compete">Non-compete</Tab>
          <Tab value="sessions">Sessions</Tab>
        </TabsList>

        <TabPanel value="overview" className="overflow-auto p-5">
          <div className="mx-auto grid max-w-5xl gap-4 lg:grid-cols-2">
            <DetailCard title="Practitioner">
              <DetailGrid>
                <DetailRow label="Display name" value={provider.display_name} />
                <DetailRow label="Region" value={getStatusLabel(profile.region)} />
                <DetailRow label="Contact email" value={provider.email ?? ""} />
                <DetailRow label="Contact phone" value={provider.phone ?? ""} />
                <DetailRow label="Specialties" value={profile.specialties.join(", ")} fullWidth />
                <DetailRow label="Bio" value={profile.bio ?? ""} fullWidth />
              </DetailGrid>
            </DetailCard>

            <ProviderLifecyclePanel provider={provider} onChanged={refresh} />
            <ProviderAccountCard provider={provider} onChanged={refresh} />

            {provider.license_info ? (
              <DetailCard title="Licence">
                <DetailGrid>
                  <DetailRow label="Number" value={provider.license_info.number ?? ""} />
                  <DetailRow
                    label="Issuing authority"
                    value={provider.license_info.issuing_authority ?? ""}
                  />
                  <DetailRow label="Expires" value={provider.license_info.expiry_date ?? ""} />
                </DetailGrid>
              </DetailCard>
            ) : null}
          </div>
        </TabPanel>

        <TabPanel value="affiliations" className="overflow-auto p-5">
          <div className="mx-auto max-w-3xl">
            <ProviderAffiliationsPanel providerId={provider.id} />
          </div>
        </TabPanel>

        <TabPanel value="non-compete" className="overflow-auto p-5">
          <div className="mx-auto max-w-3xl">
            <ProviderNonCompetePanel providerId={provider.id} />
          </div>
        </TabPanel>

        <TabPanel value="sessions" className="overflow-auto p-5">
          <div className="mx-auto max-w-5xl">
            <SessionHistory providerId={provider.id} />
          </div>
        </TabPanel>
      </Tabs>
    </PageShell>
  )
}
