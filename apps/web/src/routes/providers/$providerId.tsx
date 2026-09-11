import { useState } from "react"

import { useQueryClient } from "@tanstack/react-query"
import { createFileRoute, useNavigate } from "@tanstack/react-router"
import { SquarePen, Stethoscope } from "lucide-react"

import { providersApi } from "@/api/endpoints/providers"
import {
  DetailCard,
  DetailGrid,
  DetailRow,
  RailSection,
} from "@/components/common/DetailPrimitives"
import { renderDetailState } from "@/components/common/DetailStates"
import { EntityActivityPanel } from "@/components/common/EntityActivityPanel"
import { PageShell } from "@/components/common/PageShell"
import { ProviderTierBadge } from "@/components/common/ProviderTierBadge"
import { StatusBadge } from "@/components/common/StatusBadge"
import { Tab, TabPanel, Tabs, TabsList } from "@/components/common/Tabs"
import { ProviderAccountCard } from "@/components/providers/ProviderAccountCard"
import { ProviderAliasesPanel } from "@/components/providers/ProviderAliasesPanel"
import { ProviderCommitmentsPanel } from "@/components/providers/ProviderCommitmentsPanel"
import { ProviderDeliveryPanel } from "@/components/providers/ProviderDeliveryPanel"
import { ProviderEngagementDocumentsCard } from "@/components/providers/ProviderEngagementDocumentsCard"
import { ProviderFormSheet } from "@/components/providers/ProviderFormSheet"
import { ProviderLifecyclePanel } from "@/components/providers/ProviderLifecyclePanel"
import { ProviderReadinessRail } from "@/components/providers/ProviderReadinessRail"
import { ProviderSpecialtiesPanel } from "@/components/providers/ProviderSpecialtiesPanel"
import { Button } from "@/components/ui/button"
import { useCanWrite } from "@/hooks/useCanWrite"
import { useTabSearchParam } from "@/hooks/useTabSearchParam"
import { formatDate } from "@/lib/format"
import { entityDetailKey, useEntityDetail } from "@/lib/queries"
import type { Provider } from "@/types/entities"
import { ProviderIdentityProvenance } from "@/types/enums"
import { getStatusLabel } from "@/utils/statusColors"

export const Route = createFileRoute("/providers/$providerId")({
  component: ProviderDetailPage,
})

const TAB_VALUES = ["overview", "commitments", "delivery", "activity"] as const
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
      trail={[{ label: "Providers", to: "/providers" }]}
      title={provider.formal_name || provider.display_name}
      actions={
        canWrite ? (
          <Button
            type="button"
            variant="outline"
            size="sm"
            className="h-7 gap-1.5 rounded-none px-2"
            onClick={() => setEditOpen(true)}
          >
            <SquarePen className="size-3.5" />
            Edit
          </Button>
        ) : null
      }
    >
      <div className="flex flex-wrap items-center gap-2 border-b border-fg/10 bg-surface px-3 py-2">
        <ProviderTierBadge tier={profile.tier} />
        <span className="text-xs text-fg/70">
          {profile.region ? getStatusLabel(profile.region) : "Region unassessed"}
        </span>
        <StatusBadge status={profile.panel_status} size="sm" />
        <StatusBadge status={profile.accreditation_status} size="sm" />
        <StatusBadge status={provider.status} size="sm" />
      </div>

      <ProviderFormSheet open={editOpen} onOpenChange={setEditOpen} provider={provider} />

      <div className="flex min-h-0 flex-1 overflow-y-auto bg-bg">
        <div className="grid w-full grid-cols-12 gap-5 px-5 py-5">
          <div className="col-span-12 min-w-0 lg:col-span-8">
            <Tabs value={tab} onValueChange={(value) => setTab(value as TabValue)}>
              <TabsList className="mb-5 px-0">
                <Tab value="overview">Overview</Tab>
                <Tab value="commitments">Commitments</Tab>
                <Tab value="delivery">Delivery record</Tab>
                <Tab value="activity">Activity</Tab>
              </TabsList>

              <TabPanel value="overview">
                <div className="grid gap-4 lg:grid-cols-2">
                  <DetailCard title="Practitioner">
                    <DetailGrid>
                      <DetailRow label="Title" value={profile.title ?? ""} />
                      <DetailRow label="Display name" value={provider.display_name} />
                      <DetailRow
                        label="Region"
                        value={profile.region ? getStatusLabel(profile.region) : "Unassessed"}
                      />
                      <DetailRow label="Contact email" value={provider.email ?? ""} />
                      <DetailRow label="Contact phone" value={provider.phone ?? ""} />
                      <DetailRow label="Bio" value={profile.bio ?? ""} fullWidth />
                    </DetailGrid>
                  </DetailCard>

                  <ProviderLifecyclePanel provider={provider} onChanged={refresh} />
                  <ProviderSpecialtiesPanel providerId={provider.id} />
                  <ProviderAliasesPanel
                    providerId={provider.id}
                    displayName={provider.display_name}
                  />
                  <ProviderEngagementDocumentsCard providerId={provider.id} />
                  <ProviderAccountCard provider={provider} onChanged={refresh} />

                  {provider.license_info ? (
                    <DetailCard title="Licence">
                      <DetailGrid>
                        <DetailRow label="Number" value={provider.license_info.number ?? ""} />
                        <DetailRow
                          label="Issuing authority"
                          value={provider.license_info.issuing_authority ?? ""}
                        />
                        <DetailRow
                          label="Expires"
                          value={provider.license_info.expiry_date ?? ""}
                        />
                      </DetailGrid>
                    </DetailCard>
                  ) : null}
                </div>
              </TabPanel>

              <TabPanel value="commitments">
                <ProviderCommitmentsPanel providerId={provider.id} />
              </TabPanel>

              <TabPanel value="delivery">
                <ProviderDeliveryPanel providerId={provider.id} />
              </TabPanel>

              <TabPanel value="activity">
                <EntityActivityPanel
                  resourceType="Provider"
                  resourceId={provider.id}
                  emptyDescription="Profile edits and lifecycle commands appear here once they happen."
                />
              </TabPanel>
            </Tabs>
          </div>

          <aside className="col-span-12 min-w-0 space-y-5 lg:sticky lg:top-3 lg:col-span-4 lg:max-h-[80vh] lg:overflow-y-auto lg:pt-14">
            <ProviderReadinessRail provider={provider} />
            <ProviderProvenanceSection provider={provider} />
          </aside>
        </div>
      </div>
    </PageShell>
  )
}

/**
 * Where this record came from. A practitioner backfilled from a user account
 * during migration is not the same as one somebody entered, and an imported
 * record's name is the source's spelling until a person confirms it.
 */
function ProviderProvenanceSection({ provider }: { provider: Provider }) {
  const backfilled =
    provider.identity_provenance === ProviderIdentityProvenance.BACKFILLED_FROM_USER
  return (
    <RailSection title="Record origin" className="border-t border-fg/10 pt-4">
      <DetailGrid>
        <DetailRow label="Identity" value={backfilled ? "Backfilled from a user" : "Entered"} />
        <DetailRow label="Created" value={formatDate(provider.created_at)} />
        <DetailRow label="Updated" value={formatDate(provider.updated_at)} />
      </DetailGrid>
      {backfilled ? (
        <p className="text-[11px] text-fg-muted">
          Taken from a linked account during migration rather than entered for the practitioner.
        </p>
      ) : null}
    </RailSection>
  )
}
