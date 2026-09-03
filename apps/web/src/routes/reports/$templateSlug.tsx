
import { useQuery } from "@tanstack/react-query"
import { createFileRoute, Link } from "@tanstack/react-router"
import {
  ArrowLeft,
  PieChart,
  Printer,
} from "lucide-react"

import { careCallbacksApi } from "@/api/endpoints/care-callbacks"
import { EmptyState } from "@/components/common/EmptyState"
import { PageShell } from "@/components/common/PageShell"
import { WaveSummaryBody } from "@/components/reports/CareCallbackWaveSummary"
import { PerClientRenewalPack } from "@/components/reports/PerClientRenewalPack"
import { BackLink, UnknownTemplate } from "@/components/reports/ReportShared"
import { Button } from "@/components/ui/button"
import { cn } from "@/lib/utils"


export const Route = createFileRoute("/reports/$templateSlug")({
  component: ReportTemplatePage,
  validateSearch: (search: Record<string, unknown>) => {
    const out: { client_id?: string; campaign_id?: string } = {}
    if (typeof search.client_id === "string" && search.client_id.trim()) {
      out.client_id = search.client_id
    }
    if (typeof search.campaign_id === "string" && search.campaign_id.trim()) {
      out.campaign_id = search.campaign_id
    }
    return out
  },
})


function CareCallbackWaveSummary() {
  const search = Route.useSearch()
  const campaignId = search.campaign_id

  const aggregateQuery = useQuery({
    queryKey: ["care-callback-campaigns", "aggregate", campaignId ?? ""],
    queryFn: () => careCallbacksApi.getAggregate(campaignId as string),
    enabled: !!campaignId,
  })
  const campaignQuery = useQuery({
    queryKey: ["care-callback-campaigns", "detail", campaignId ?? ""],
    queryFn: () => careCallbacksApi.getCampaign(campaignId as string),
    enabled: !!campaignId,
  })

  const handlePrint = () => {
    if (typeof window !== "undefined") window.print()
  }

  if (!campaignId) {
    return (
      <PageShell icon={PieChart} breadcrumb="Reports · Wave summary">
        <EmptyState
          icon={PieChart}
          title="Pick a campaign"
          description="The wave summary is rendered for one campaign. Open it from the campaign detail page or pass a campaign_id query parameter."
          action={
            <Link
              to="/care-callbacks"
              className="inline-flex h-9 items-center gap-1.5 rounded-sm border border-fg/15 bg-surface px-3 text-sm font-medium text-fg hover:bg-surface-hover"
            >
              <ArrowLeft className="size-4" />
              Pick a campaign
            </Link>
          }
        />
      </PageShell>
    )
  }

  const aggregate = aggregateQuery.data
  const campaign = campaignQuery.data
  const loading = aggregateQuery.isPending || campaignQuery.isPending
  const breadcrumbName = campaign ? campaign.name : "…"

  return (
    <PageShell
      icon={PieChart}
      breadcrumb={`Reports · Wave summary · ${breadcrumbName}`}
      actions={
        <>
          <BackLink />
          <span className="mx-1 h-4 w-px bg-fg/15" aria-hidden />
          <Button
            type="button"
            size="sm"
            variant="outline"
            className="h-7 gap-1.5 px-2.5"
            onClick={handlePrint}
            disabled={loading || !campaign || !aggregate}
          >
            <Printer className="size-3.5" />
            Print
          </Button>
        </>
      }
    >
      <div className="min-h-0 flex-1 overflow-y-auto bg-bg print:overflow-visible">
        <div className="mx-auto max-w-4xl px-5 py-6 print:px-0 print:py-0">
          <article
            className={cn(
              "space-y-8 rounded-sm border border-fg/10 bg-surface p-8",
              "print:border-0 print:bg-white print:p-0 print:text-black",
            )}
          >
            {loading ? (
              <p className="text-sm text-fg/65">Loading wave aggregate…</p>
            ) : !aggregate || !campaign ? (
              <p className="text-sm text-fg/65">Aggregate unavailable for this campaign.</p>
            ) : (
              <WaveSummaryBody campaign={campaign} aggregate={aggregate} />
            )}
          </article>
        </div>
      </div>
    </PageShell>
  )
}

function ReportTemplatePage() {
  const { templateSlug } = Route.useParams()

  if (templateSlug === "per-client-renewal") return <PerClientRenewalPack />
  if (templateSlug === "care-callback-summary") return <CareCallbackWaveSummary />
  return <UnknownTemplate slug={templateSlug} />
}
