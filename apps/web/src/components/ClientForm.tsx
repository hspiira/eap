import { useState } from "react"
import { clientsApi } from "@/api/endpoints/clients"
import { FormField } from "@/components/common/FormField"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"

export interface ClientFormProps {
  onSuccess?: () => void
  onCancel?: () => void
  submitLabel?: string
}

export function ClientForm({
  onSuccess,
  onCancel,
  submitLabel = "Create client",
}: ClientFormProps) {
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
      onSuccess?.()
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
    <form onSubmit={handleSubmit} className="space-y-4">
      {error && (
        <p
          className="text-sm text-[#5A626A] border border-[#5A626A]/30 bg-[#f5f5f5] px-3 py-2 rounded-none"
          role="alert"
        >
          {error}
        </p>
      )}
      <FormField label="Name" required error={fieldErrors.name} htmlFor="client-name">
        <Input
          id="client-name"
          value={name}
          onChange={(e) => setName(e.target.value)}
          required
          className="rounded-none border-[#5A626A]/30"
        />
      </FormField>
      <FormField label="Code (3–5 chars)" required error={fieldErrors.code} htmlFor="client-code">
        <Input
          id="client-code"
          value={code}
          onChange={(e) => setCode(e.target.value)}
          required
          className="rounded-none border-[#5A626A]/30"
        />
      </FormField>
      <FormField label="Email" error={fieldErrors["contact_info.email"]} htmlFor="client-email">
        <Input
          id="client-email"
          type="email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          className="rounded-none border-[#5A626A]/30"
        />
      </FormField>
      <FormField label="Phone" error={fieldErrors["contact_info.phone"]} htmlFor="client-phone">
        <Input
          id="client-phone"
          value={phone}
          onChange={(e) => setPhone(e.target.value)}
          className="rounded-none border-[#5A626A]/30"
        />
      </FormField>
      <div className="flex gap-2 pt-2">
        <Button
          type="submit"
          disabled={loading}
          className="rounded-none bg-natural text-white hover:bg-natural-dark"
        >
          {loading ? "Creating…" : submitLabel}
        </Button>
        {onCancel && (
          <Button
            type="button"
            variant="secondary"
            className="rounded-none border-[#5A626A]/30 text-[#5A626A]"
            onClick={onCancel}
          >
            Cancel
          </Button>
        )}
      </div>
    </form>
  )
}
