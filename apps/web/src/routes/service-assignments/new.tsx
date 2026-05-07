import { useState } from "react"

import { createFileRoute, useNavigate } from "@tanstack/react-router"

import { serviceAssignmentsApi } from "@/api/endpoints/service-assignments"
import { FormField } from "@/components/common/FormField"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"

export const Route = createFileRoute("/service-assignments/new")({
  component: ServiceAssignmentCreatePage,
})

function ServiceAssignmentCreatePage() {
  const navigate = useNavigate()
  const [contractId, setContractId] = useState("")
  const [serviceId, setServiceId] = useState("")
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError(null)
    setLoading(true)
    try {
      await serviceAssignmentsApi.create({ contract_id: contractId, service_id: serviceId })
      navigate({ to: "/service-assignments" })
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to create assignment")
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="p-6 max-w-md">
      <h1 className="text-xl font-semibold text-[#5A626A]">Add service assignment</h1>
      <form onSubmit={handleSubmit} className="mt-6 space-y-4">
        {error && <p className="text-sm text-[#5A626A]" role="alert">{error}</p>}
        <FormField label="Contract ID" required htmlFor="contract_id">
          <Input id="contract_id" value={contractId} onChange={(e) => setContractId(e.target.value)} required className="rounded-none" />
        </FormField>
        <FormField label="Service ID" required htmlFor="service_id">
          <Input id="service_id" value={serviceId} onChange={(e) => setServiceId(e.target.value)} required className="rounded-none" />
        </FormField>
        <div className="flex gap-2">
          <Button type="submit" disabled={loading} className="rounded-none">{loading ? "Creating…" : "Create"}</Button>
          <Button type="button" variant="secondary" className="rounded-none" onClick={() => navigate({ to: "/service-assignments" })}>Cancel</Button>
        </div>
      </form>
    </div>
  )
}
