import { useState } from "react"

import { createFileRoute, useNavigate } from "@tanstack/react-router"

import { contractsApi } from "@/api/endpoints/contracts"
import { FormField } from "@/components/common/FormField"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"

export const Route = createFileRoute("/contracts/new")({
  component: ContractCreatePage,
})

function ContractCreatePage() {
  const navigate = useNavigate()
  const [clientId, setClientId] = useState("")
  const [contractNumber, setContractNumber] = useState("")
  const [startDate, setStartDate] = useState("")
  const [endDate, setEndDate] = useState("")
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError(null)
    setLoading(true)
    try {
      await contractsApi.create({
        client_id: clientId,
        contract_number: contractNumber || undefined,
        start_date: startDate,
        end_date: endDate || undefined,
      })
      navigate({ to: "/contracts" })
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to create contract")
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="p-6 max-w-md">
      <h1 className="text-xl font-semibold text-[#5A626A]">Add contract</h1>
      <form onSubmit={handleSubmit} className="mt-6 space-y-4">
        {error && <p className="text-sm text-[#5A626A]" role="alert">{error}</p>}
        <FormField label="Client ID" required htmlFor="client_id">
          <Input id="client_id" value={clientId} onChange={(e) => setClientId(e.target.value)} required className="rounded-none" />
        </FormField>
        <FormField label="Contract number" htmlFor="contract_number">
          <Input id="contract_number" value={contractNumber} onChange={(e) => setContractNumber(e.target.value)} className="rounded-none" />
        </FormField>
        <FormField label="Start date" required htmlFor="start_date">
          <Input id="start_date" type="date" value={startDate} onChange={(e) => setStartDate(e.target.value)} required className="rounded-none" />
        </FormField>
        <FormField label="End date" htmlFor="end_date">
          <Input id="end_date" type="date" value={endDate} onChange={(e) => setEndDate(e.target.value)} className="rounded-none" />
        </FormField>
        <div className="flex gap-2">
          <Button type="submit" disabled={loading} className="rounded-none">{loading ? "Creating…" : "Create contract"}</Button>
          <Button type="button" variant="secondary" className="rounded-none" onClick={() => navigate({ to: "/contracts" })}>Cancel</Button>
        </div>
      </form>
    </div>
  )
}
