import { useEffect } from "react"

import { z } from "zod"

import { clientsApi } from "@/api/endpoints/clients"
import { FormField } from "@/components/common/FormField"
import { FormSection } from "@/components/common/FormSection"
import { SheetForm } from "@/components/common/SheetForm"
import { Input } from "@/components/ui/input"
import { useApiForm } from "@/hooks/useApiForm"
import { useEntityMutation } from "@/lib/queries"
import { ClientTier } from "@/types/enums"

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

type ClientFormValues = z.infer<typeof clientCreateSchema>

const SELECT_CLASS =
  "flex h-9 w-full rounded-sm border border-fg/20 bg-bg px-3 text-sm text-fg shadow-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 focus-visible:ring-offset-bg"

interface ClientFormSheetProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  onCreated?: () => void
}

export function ClientFormSheet({ open, onOpenChange, onCreated }: ClientFormSheetProps) {
  const createClient = useEntityMutation({
    resource: "clients",
    mutationFn: clientsApi.create,
  })

  const { register, reset, formState, submit, serverError } = useApiForm<ClientFormValues>({
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
      onCreated?.()
      onOpenChange(false)
      reset()
    },
  })

  useEffect(() => {
    if (!open) {
      reset({ name: "", code: "", tier: "", email: "", phone: "" })
    }
  }, [open, reset])

  const errors = formState.errors as Record<string, { message?: string }>

  return (
    <SheetForm
      open={open}
      onOpenChange={onOpenChange}
      title="Add client"
      description="Create a new corporate client. You can link contracts, services, and staff after saving."
      size="md"
      onSubmit={submit}
      isSubmitting={formState.isSubmitting}
      serverError={serverError}
      submitLabel="Create client"
      submittingLabel="Creating…"
    >
      <FormSection title="Identity">
        <FormField
          label="Client name"
          required
          error={errors.name?.message}
          htmlFor="cs-name"
        >
          <Input id="cs-name" placeholder="e.g. Acme Corp" {...register("name")} />
        </FormField>
        <FormField
          label="Code"
          description="3–5 character code used in employee references."
          required
          error={errors.code?.message}
          htmlFor="cs-code"
        >
          <Input
            id="cs-code"
            placeholder="ACME"
            maxLength={5}
            className="font-mono uppercase"
            {...register("code")}
          />
        </FormField>
      </FormSection>

      <FormSection title="Tiering">
        <FormField
          label="Tier"
          optional
          error={errors.tier?.message}
          htmlFor="cs-tier"
        >
          <select id="cs-tier" className={SELECT_CLASS} {...register("tier")}>
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
        description="Used for billing and account notifications."
      >
        <FormField
          label="Email"
          optional
          error={(errors["contact_info.email"]?.message ?? errors.email?.message) as string | undefined}
          htmlFor="cs-email"
        >
          <Input
            id="cs-email"
            type="email"
            placeholder="contact@acme.com"
            {...register("email")}
          />
        </FormField>
        <FormField
          label="Phone"
          optional
          error={(errors["contact_info.phone"]?.message ?? errors.phone?.message) as string | undefined}
          htmlFor="cs-phone"
        >
          <Input id="cs-phone" type="tel" placeholder="+254 …" {...register("phone")} />
        </FormField>
      </FormSection>
    </SheetForm>
  )
}
