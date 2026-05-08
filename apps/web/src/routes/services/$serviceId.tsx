import { useCallback, useEffect, useState } from "react"

import { createFileRoute, useNavigate } from "@tanstack/react-router"

import { servicesApi } from "@/api/endpoints/services"
import { LifecycleActions } from "@/components/common/LifecycleActions"
import { StatusBadge } from "@/components/common/StatusBadge"
import { Button } from "@/components/ui/button"
import type { Service } from "@/types/entities"
import type { LifecycleAction } from "@/utils/lifecycleConfig"

export const Route = createFileRoute("/services/$serviceId")({
  component: ServiceDetailPage,
})

function ServiceDetailPage() {
  const { serviceId } = Route.useParams()
  const navigate = useNavigate()
  const [service, setService] = useState<Service | null>(null)
  const [loading, setLoading] = useState(true)
  const [actionLoading, setActionLoading] = useState(false)

  const fetchService = useCallback(async () => {
    try {
      setLoading(true)
      setService(await servicesApi.getById(serviceId))
    } catch {
      setService(null)
    } finally {
      setLoading(false)
    }
  }, [serviceId])

  useEffect(() => { fetchService() }, [fetchService])

  const handleAction = useCallback(async (id: string, action: LifecycleAction) => {
    setActionLoading(true)
    try {
      if (action === "activate") await servicesApi.activate(id)
      else if (action === "deactivate") await servicesApi.deactivate(id)
      else if (action === "archive") await servicesApi.archive(id)
      else if (action === "restore") await servicesApi.restore(id)
      await fetchService()
    } finally {
      setActionLoading(false)
    }
  }, [fetchService])

  if (loading) return <div className="p-8 text-fg">Loading…</div>
  if (!service) {
    return (
      <div className="p-8">
        <p className="text-fg">Service not found.</p>
        <Button variant="secondary" className="mt-4 rounded-none" onClick={() => navigate({ to: "/services" })}>Back to services</Button>
      </div>
    )
  }

  return (
    <div className="p-6 space-y-6">
      <Button variant="ghost" size="sm" className="rounded-none" onClick={() => navigate({ to: "/services" })}>← Services</Button>
      <div className="border border-fg/30 rounded-none p-6 bg-surface/30">
        <h1 className="text-xl font-semibold text-fg">{service.name}</h1>
        <dl className="mt-4 grid gap-2 sm:grid-cols-2">
          <div><dt className="text-sm text-fg/80">Status</dt><dd><StatusBadge status={service.status} /></dd></div>
          {service.description && <div><dt className="text-sm text-fg/80">Description</dt><dd>{service.description}</dd></div>}
        </dl>
        <div className="mt-6">
          <h2 className="text-sm font-medium text-fg mb-2">Actions</h2>
          <LifecycleActions entityId={service.id} currentStatus={service.status} kind="service" onAction={handleAction} loading={actionLoading} />
        </div>
      </div>
    </div>
  )
}
