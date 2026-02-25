import { createFileRoute, useNavigate } from "@tanstack/react-router"
import { useCallback, useEffect, useState } from "react"
import { clientsApi } from "@/api/endpoints/clients"
import type { Client } from "@/types/entities"
import { ClientsPageHeader } from "@/components/ClientsPageHeader"
import { ClientDetailSkeleton } from "@/components/ClientsPageSkeletons"
import { LifecycleActions } from "@/components/common/LifecycleActions"
import { StatusBadge } from "@/components/common/StatusBadge"
import { Button } from "@/components/ui/button"
import type { LifecycleAction } from "@/utils/lifecycleConfig"

export const Route = createFileRoute("/clients/$clientId")({
  component: ClientDetailPage,
})

function ClientDetailPage() {
  const { clientId } = Route.useParams()
  const navigate = useNavigate()
  const [client, setClient] = useState<Client | null>(null)
  const [loading, setLoading] = useState(true)
  const [actionLoading, setActionLoading] = useState(false)

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
        <div className="border border-[#5A626A]/20 rounded-none bg-[#f5f5f5] p-8 text-center">
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

  return (
    <ClientsPageHeader breadcrumb={`Clients > ${client.name}`}>
      <div className="content-area-scroll flex-1 min-h-0 overflow-x-auto overflow-y-auto p-4">
        <div className="border border-[#5A626A]/30 rounded-none bg-white overflow-hidden">
          <div className="px-6 py-5 border-b border-[#5A626A]/20 bg-[#f5f5f5]">
            <h1 className="text-xl font-semibold text-[#5A626A]">{client.name}</h1>
            <p className="text-sm text-[#5A626A]/70 mt-0.5">{client.code}</p>
          </div>
          <dl className="grid gap-4 sm:grid-cols-2 px-6 py-5">
            <div>
              <dt className="text-xs font-medium uppercase tracking-wide text-[#5A626A]/70">Status</dt>
              <dd className="mt-1"><StatusBadge status={client.status} /></dd>
            </div>
            {client.contact_info?.email && (
              <div>
                <dt className="text-xs font-medium uppercase tracking-wide text-[#5A626A]/70">Email</dt>
                <dd className="mt-1 text-[#5A626A]">{client.contact_info.email}</dd>
              </div>
            )}
            {client.contact_info?.phone && (
              <div>
                <dt className="text-xs font-medium uppercase tracking-wide text-[#5A626A]/70">Phone</dt>
                <dd className="mt-1 text-[#5A626A]">{client.contact_info.phone}</dd>
              </div>
            )}
          </dl>
          <div className="px-6 py-5 border-t border-[#5A626A]/20 bg-[#f5f5f5]">
            <h2 className="text-sm font-medium text-[#5A626A] mb-3">Actions</h2>
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
    </ClientsPageHeader>
  )
}
