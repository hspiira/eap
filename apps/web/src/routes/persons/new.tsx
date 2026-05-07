import { useState } from "react"

import { createFileRoute, useNavigate } from "@tanstack/react-router"

import { personsApi } from "@/api/endpoints/persons"
import { FormField } from "@/components/common/FormField"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { PersonType } from "@/types/enums"

export const Route = createFileRoute("/persons/new")({
  component: PersonCreatePage,
})

function PersonCreatePage() {
  const navigate = useNavigate()
  const [firstName, setFirstName] = useState("")
  const [lastName, setLastName] = useState("")
  const [personType, setPersonType] = useState<PersonType>(PersonType.CLIENT_EMPLOYEE)
  const [clientId, setClientId] = useState("")
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError(null)
    setLoading(true)
    try {
      await personsApi.create({
        first_name: firstName,
        last_name: lastName,
        person_type: personType,
        client_id: clientId || undefined,
      })
      navigate({ to: "/persons" })
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to create person")
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="p-6 max-w-md">
      <h1 className="text-xl font-semibold text-[#5A626A]">Add person</h1>
      <form onSubmit={handleSubmit} className="mt-6 space-y-4">
        {error && <p className="text-sm text-[#5A626A]" role="alert">{error}</p>}
        <FormField label="First name" required htmlFor="first_name">
          <Input id="first_name" value={firstName} onChange={(e) => setFirstName(e.target.value)} required className="rounded-none" />
        </FormField>
        <FormField label="Last name" required htmlFor="last_name">
          <Input id="last_name" value={lastName} onChange={(e) => setLastName(e.target.value)} required className="rounded-none" />
        </FormField>
        <FormField label="Type" required htmlFor="person_type">
          <select
            id="person_type"
            value={personType}
            onChange={(e) => setPersonType(e.target.value as PersonType)}
            className="flex h-9 w-full border border-[#5A626A]/30 bg-[#E6E0D7] px-3 py-2 rounded-none"
          >
            <option value={PersonType.CLIENT_EMPLOYEE}>Client Employee</option>
            <option value={PersonType.DEPENDENT}>Dependent</option>
            <option value={PersonType.SERVICE_PROVIDER}>Service Provider</option>
            <option value={PersonType.PLATFORM_STAFF}>Platform Staff</option>
          </select>
        </FormField>
        <FormField label="Client ID (optional)" htmlFor="client_id">
          <Input id="client_id" value={clientId} onChange={(e) => setClientId(e.target.value)} className="rounded-none" />
        </FormField>
        <div className="flex gap-2">
          <Button type="submit" disabled={loading} className="rounded-none">{loading ? "Creating…" : "Create person"}</Button>
          <Button type="button" variant="secondary" className="rounded-none" onClick={() => navigate({ to: "/persons" })}>Cancel</Button>
        </div>
      </form>
    </div>
  )
}
