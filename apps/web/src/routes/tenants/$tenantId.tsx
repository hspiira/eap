import { useState } from "react"

import { useQuery } from "@tanstack/react-query"
import { createFileRoute } from "@tanstack/react-router"
import { ShieldCheck, SquarePen } from "lucide-react"

import { tenantsApi } from "@/api/endpoints/tenants"
import { AppLayout } from "@/components/AppLayout"
import { PageShell } from "@/components/common/PageShell"
import { DetailSkeleton } from "@/components/common/PageSkeletons"
import { RequirePlatformAdmin } from "@/components/common/RequirePlatformAdmin"
import { TenantFormSheet } from "@/components/TenantFormSheet"
import {
  AzureSsoCard,
  ErrorBanner,
  LifecycleCard,
  OverviewCard,
  SubscriptionAndQuotasCard,
} from "@/components/tenants/TenantDetailWidgets"
import { Button } from "@/components/ui/button"
import { normalizeErrorMessage } from "@/lib/errors"

export const Route = createFileRoute("/tenants/$tenantId")({
  component: TenantDetailPage,
})

function TenantDetailPage() {
  return (
    <RequirePlatformAdmin>
      <TenantDetailBody />
    </RequirePlatformAdmin>
  )
}

function TenantDetailBody() {
  const { tenantId } = Route.useParams()
  const [editOpen, setEditOpen] = useState(false)

  const {
    data: tenant,
    isLoading,
    isError,
    error,
    refetch,
  } = useQuery({
    queryKey: ["tenants", "detail", tenantId],
    queryFn: () => tenantsApi.getById(tenantId),
  })

  return (
    <AppLayout>
      <PageShell
        icon={ShieldCheck}
        trail={[
          {
            label: "Tenants",
            to: "/tenants",
            search: { new: undefined, search: undefined, status: undefined },
          },
        ]}
        title={tenant?.name ?? tenantId}
        actions={
          tenant ? (
            <Button type="button" variant="outline" size="sm" onClick={() => setEditOpen(true)}>
              <SquarePen className="size-3.5" /> Edit name
            </Button>
          ) : null
        }
      >
        <div className="flex flex-1 flex-col gap-6 p-6">
          {isError ? (
            <ErrorBanner
              message={normalizeErrorMessage(error, "Could not load tenant")}
              onRetry={() => refetch()}
            />
          ) : isLoading || !tenant ? (
            <DetailSkeleton />
          ) : (
            <>
              <OverviewCard tenant={tenant} />
              <SubscriptionAndQuotasCard tenant={tenant} />
              <AzureSsoCard tenant={tenant} />
              <LifecycleCard tenant={tenant} />
            </>
          )}
        </div>
      </PageShell>

      {tenant ? (
        <TenantFormSheet
          open={editOpen}
          onOpenChange={setEditOpen}
          tenant={tenant}
          onSaved={() => setEditOpen(false)}
        />
      ) : null}
    </AppLayout>
  )
}
