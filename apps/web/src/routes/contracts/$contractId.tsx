import { createFileRoute, useNavigate } from "@tanstack/react-router"
import { useCallback, useEffect, useState } from "react"
import { contractsApi } from "@/api/endpoints/contracts"
import type { Contract } from "@/types/entities"
import { LifecycleActions } from "@/components/common/LifecycleActions"
import { StatusBadge } from "@/components/common/StatusBadge"
import { Button } from "@/components/ui/button"
import type { LifecycleAction } from "@/utils/lifecycleConfig"

export const Route = createFileRoute("/contracts/$contractId")({
  component: ContractDetailPage,
})

function ContractDetailPage() {
  const { contractId } = Route.useParams()
  const navigate = useNavigate()
  const [contract, setContract] = useState<Contract | null>(null)
  const [loading, setLoading] = useState(true)
  const [actionLoading, setActionLoading] = useState(false)

  const fetchContract = useCallback(async () => {
    try {
      setLoading(true)
      setContract(await contractsApi.getById(contractId))
    } catch {
      setContract(null)
    } finally {
      setLoading(false)
    }
  }, [contractId])

  useEffect(() => { fetchContract() }, [fetchContract])

  const handleAction = useCallback(async (id: string, action: LifecycleAction) => {
    setActionLoading(true)
    try {
      if (action === "activate") await contractsApi.activate(id)
      else if (action === "terminate") await contractsApi.terminate(id, "Terminated from UI")
      else if (action === "renew") await contractsApi.renew(id, {})
      await fetchContract()
    } finally {
      setActionLoading(false)
    }
  }, [fetchContract])

  if (loading) return <div className="p-8 text-[#5A626A]">Loading…</div>
  if (!contract) {
    return (
      <div className="p-8">
        <p className="text-[#5A626A]">Contract not found.</p>
        <Button variant="secondary" className="mt-4 rounded-none" onClick={() => navigate({ to: "/contracts" })}>Back to contracts</Button>
      </div>
    )
  }

  return (
    <div className="p-6 space-y-6">
      <Button variant="ghost" size="sm" className="rounded-none" onClick={() => navigate({ to: "/contracts" })}>← Contracts</Button>
      <div className="border border-[#5A626A]/30 rounded-none p-6 bg-[#E6E0D7]/30">
        <h1 className="text-xl font-semibold text-[#5A626A]">{contract.contract_number ?? contract.id}</h1>
        <dl className="mt-4 grid gap-2 sm:grid-cols-2">
          <div><dt className="text-sm text-[#5A626A]/80">Status</dt><dd><StatusBadge status={contract.status} /></dd></div>
          <div><dt className="text-sm text-[#5A626A]/80">Client ID</dt><dd>{contract.client_id}</dd></div>
          <div><dt className="text-sm text-[#5A626A]/80">Start</dt><dd>{contract.start_date}</dd></div>
          <div><dt className="text-sm text-[#5A626A]/80">End</dt><dd>{contract.end_date ?? "—"}</dd></div>
        </dl>
        <div className="mt-6">
          <h2 className="text-sm font-medium text-[#5A626A] mb-2">Actions</h2>
          <LifecycleActions entityId={contract.id} currentStatus={contract.status} kind="contract" onAction={handleAction} loading={actionLoading} />
        </div>
      </div>
    </div>
  )
}
