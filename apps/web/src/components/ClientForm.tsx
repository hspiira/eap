import { z } from "zod"

import { clientsApi } from "@/api/endpoints/clients"
import { FormField } from "@/components/common/FormField"
import { FormSection } from "@/components/common/FormSection"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { useApiForm } from "@/hooks/useApiForm"
import { useEntityMutation } from "@/lib/queries"
import { ClientTier } from "@/types/enums"

export interface ClientFormProps {
  onSuccess?: () => void
  onCancel?: () => void
  submitLabel?: string
}

const TIER_VALUES = [ClientTier.A, ClientTier.B, ClientTier.C] as const

const clientCreateSchema = z.object({
  name: z.string().trim().min(1, "Name is required"),
  code: z
    .string()
    .trim()
    .min(3, "Code must be 3–5 characters")
    .max(5, "Code must be 3–5 characters"),
  tier: z.enum(["", ...TIER_VALUES] as readonly [string, ...string[]]).optional(),
  email: z
    .string()
    .trim()
    .optional()
    .refine((v) => !v || /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(v), "Invalid email"),
  phone: z.string().optional(),
})

const SELECT_CLASS =
  "flex h-9 w-full rounded-sm border border-fg/20 bg-bg px-3 text-sm text-fg shadow-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 focus-visible:ring-offset-bg"

export function ClientForm({
  onSuccess,
  onCancel,
  submitLabel = "Create client",
}: ClientFormProps) {
  const createClient = useEntityMutation({
    resource: "clients",
    mutationFn: clientsApi.create,
  })

  const { register, formState, submit, serverError } = useApiForm<
    z.infer<typeof clientCreateSchema>
  >({
    schema: clientCreateSchema,
    defaultValues: { name: "", code: "", tier: "", email: "", phone: "" },
    successToast: "Client created",
    onSubmit: async (values) => {
      await createClient.mutateAsync({
        name: values.name,
        code: values.code,
        tier: values.tier ? (values.tier as ClientTier) : undefined,
        contact_info: {
          email: values.email || undefined,
          phone: values.phone || undefined,
        },
      })
      onSuccess?.()
    },
  })

  const errors = formState.errors as Record<string, { message?: string }>

  return (
    <form onSubmit={submit} className="space-y-6" noValidate>
      {serverError ? (
        <div
          role="alert"
          className="rounded-sm border border-danger/30 bg-danger-soft px-3 py-2 text-sm text-danger-fg"
        >
          {serverError}
        </div>
      ) : null}

      <FormSection title="Identity">
        <FormField
          label="Name"
          required
          error={errors.name?.message}
          htmlFor="client-name"
        >
          <Input id="client-name" placeholder="e.g. Acme Corp" {...register("name")} />
        </FormField>
        <FormField
          label="Code"
          description="3–5 character code used in employee references."
          required
          error={errors.code?.message}
          htmlFor="client-code"
        >
          <Input
            id="client-code"
            placeholder="ACME"
            maxLength={5}
            className="font-mono"
            {...register("code")}
          />
        </FormField>
      </FormSection>

      <FormSection title="Tiering">
        <FormField
          label="Tier"
          optional
          error={errors.tier?.message}
          htmlFor="client-tier"
        >
          <select id="client-tier" className={SELECT_CLASS} {...register("tier")}>
            <option value="">Unassigned</option>
            {TIER_VALUES.map((t) => (
              <option key={t} value={t}>
                Tier {t}
              </option>
            ))}
          </select>
        </FormField>
      </FormSection>

      <FormSection
        title="Primary contact"
        description="Used for billing and account communications."
      >
        <FormField
          label="Email"
          optional
          error={(errors["contact_info.email"]?.message ?? errors.email?.message) as string | undefined}
          htmlFor="client-email"
        >
          <Input
            id="client-email"
            type="email"
            placeholder="contact@acme.com"
            {...register("email")}
          />
        </FormField>
        <FormField
          label="Phone"
          optional
          error={(errors["contact_info.phone"]?.message ?? errors.phone?.message) as string | undefined}
          htmlFor="client-phone"
        >
          <Input id="client-phone" type="tel" placeholder="+254 …" {...register("phone")} />
        </FormField>
      </FormSection>

      <div className="flex gap-2 pt-2">
        <Button type="submit" disabled={formState.isSubmitting}>
          {formState.isSubmitting ? "Creating…" : submitLabel}
        </Button>
        {onCancel ? (
          <Button type="button" variant="outline" onClick={onCancel}>
            Cancel
          </Button>
        ) : null}
      </div>
    </form>
  )
}
