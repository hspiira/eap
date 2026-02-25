import { createFileRoute, useNavigate } from "@tanstack/react-router"
import { useState } from "react"
import { usersApi } from "@/api/endpoints/users"
import { FormField } from "@/components/common/FormField"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"

export const Route = createFileRoute("/users/new")({
  component: UserCreatePage,
})

function UserCreatePage() {
  const navigate = useNavigate()
  const [email, setEmail] = useState("")
  const [password, setPassword] = useState("")
  const [error, setError] = useState<string | null>(null)
  const [fieldErrors, setFieldErrors] = useState<Record<string, string>>({})
  const [loading, setLoading] = useState(false)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError(null)
    setFieldErrors({})
    setLoading(true)
    try {
      await usersApi.create({ email, password: password || undefined })
      navigate({ to: "/users" })
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : "Failed to create user"
      setError(message)
      if (err && typeof err === "object" && "fieldErrors" in err) {
        setFieldErrors((err as { fieldErrors?: Record<string, string> }).fieldErrors ?? {})
      }
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="p-6 max-w-md">
      <h1 className="text-xl font-semibold text-[#5A626A]">Add user</h1>
      <form onSubmit={handleSubmit} className="mt-6 space-y-4">
        {error && (
          <p className="text-sm text-[#5A626A]" role="alert">
            {error}
          </p>
        )}
        <FormField label="Email" required error={fieldErrors.email} htmlFor="email">
          <Input
            id="email"
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
            className="rounded-none"
          />
        </FormField>
        <FormField label="Password (optional)" error={fieldErrors.password} htmlFor="password">
          <Input
            id="password"
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            className="rounded-none"
          />
        </FormField>
        <div className="flex gap-2">
          <Button type="submit" disabled={loading} className="rounded-none">
            {loading ? "Creating…" : "Create user"}
          </Button>
          <Button
            type="button"
            variant="secondary"
            className="rounded-none"
            onClick={() => navigate({ to: "/users" })}
          >
            Cancel
          </Button>
        </div>
      </form>
    </div>
  )
}
