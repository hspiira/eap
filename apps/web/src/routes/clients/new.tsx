import { createFileRoute, useNavigate } from "@tanstack/react-router"
import { useState } from "react"
import { clientsApi } from "@/api/endpoints/clients"
import { ClientsPageHeader } from "@/components/ClientsPageHeader"
import { FormField } from "@/components/common/FormField"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"

export const Route = createFileRoute("/clients/new")({
  component: ClientCreatePage,
})

function ClientCreatePage() {
  const navigate = useNavigate()
  const [name, setName] = useState("")
  const [code, setCode] = useState("")
  const [email, setEmail] = useState("")
  const [phone, setPhone] = useState("")
  const [error, setError] = useState<string | null>(null)
  const [fieldErrors, setFieldErrors] = useState<Record<string, string>>({})
  const [loading, setLoading] = useState(false)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError(null)
    setFieldErrors({})
    setLoading(true)
    try {
      await clientsApi.create({
        name,
        code,
        contact_info: { email: email || undefined, phone: phone || undefined },
      })
      navigate({ to: "/clients" })
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to create client")
      if (err && typeof err === "object" && "fieldErrors" in err) {
        setFieldErrors((err as { fieldErrors?: Record<string, string> }).fieldErrors ?? {})
      }
    } finally {
      setLoading(false)
    }
  }

  return (
    <ClientsPageHeader breadcrumb="Clients > New">
      <div className="content-area-scroll flex-1 min-h-0 overflow-x-auto overflow-y-auto p-4">
        <div className="max-w-lg border border-[#5A626A]/30 rounded-none bg-white overflow-hidden">
          <div className="px-6 py-4 border-b border-[#5A626A]/20 bg-[#f5f5f5]">
            <h1 className="text-xl font-semibold text-[#5A626A]">Add client</h1>
            <p className="text-sm text-[#5A626A]/70 mt-0.5">Create a new client record.</p>
          </div>
          <form onSubmit={handleSubmit} className="p-6 space-y-4">
            {error && (
              <p className="text-sm text-[#5A626A] border border-[#5A626A]/30 bg-[#f5f5f5] px-3 py-2" role="alert">
                {error}
              </p>
            )}
            <FormField label="Name" required error={fieldErrors.name} htmlFor="name">
              <Input id="name" value={name} onChange={(e) => setName(e.target.value)} required className="rounded-none border-[#5A626A]/30" />
            </FormField>
            <FormField label="Code (3–5 chars)" required error={fieldErrors.code} htmlFor="code">
              <Input id="code" value={code} onChange={(e) => setCode(e.target.value)} required className="rounded-none border-[#5A626A]/30" />
            </FormField>
            <FormField label="Email" error={fieldErrors["contact_info.email"]} htmlFor="email">
              <Input id="email" type="email" value={email} onChange={(e) => setEmail(e.target.value)} className="rounded-none border-[#5A626A]/30" />
            </FormField>
            <FormField label="Phone" error={fieldErrors["contact_info.phone"]} htmlFor="phone">
              <Input id="phone" value={phone} onChange={(e) => setPhone(e.target.value)} className="rounded-none border-[#5A626A]/30" />
            </FormField>
            <div className="flex gap-2 pt-2">
              <Button type="submit" disabled={loading} className="rounded-none bg-natural text-white hover:bg-natural-dark">
                {loading ? "Creating…" : "Create client"}
              </Button>
              <Button
                type="button"
                variant="secondary"
                className="rounded-none border-[#5A626A]/30 text-[#5A626A]"
                onClick={() => navigate({ to: "/clients" })}
              >
                Cancel
              </Button>
            </div>
          </form>
        </div>
      </div>
    </ClientsPageHeader>
  )
}
