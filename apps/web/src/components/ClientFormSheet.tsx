import { useEffect } from "react"

import { useQueryClient } from "@tanstack/react-query"
import { z } from "zod"

import { clientsApi } from "@/api/endpoints/clients"
import { FormField } from "@/components/common/FormField"
import { FormSection } from "@/components/common/FormSection"
import { SheetForm } from "@/components/common/SheetForm"
import { Input } from "@/components/ui/input"
import { useApiForm } from "@/hooks/useApiForm"
import type { Client } from "@/types/entities"
import { ClientTier } from "@/types/enums"

const TIER_VALUES = [ClientTier.A, ClientTier.B, ClientTier.C] as const

const clientSchema = z.object({
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
  address: z.string().optional(),
  billing_street: z.string().optional(),
  billing_city: z.string().optional(),
  billing_postal: z.string().optional(),
  billing_country: z.string().optional(),
})

type ClientFormValues = z.infer<typeof clientSchema>

const SELECT_CLASS =
  "flex h-9 w-full rounded-sm border border-fg/20 bg-bg px-3 text-sm text-fg shadow-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 focus-visible:ring-offset-bg"

const EMPTY: ClientFormValues = {
  name: "",
  code: "",
  tier: "",
  email: "",
  phone: "",
  address: "",
  billing_street: "",
  billing_city: "",
  billing_postal: "",
  billing_country: "",
}

interface ClientFormSheetProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  /** Pass a client to edit; omit/null to create a new one. */
  client?: Client | null
  onSaved?: (client: Client) => void
}

export function ClientFormSheet({
  open,
  onOpenChange,
  client,
  onSaved,
}: ClientFormSheetProps) {
  const isEdit = Boolean(client)
  const queryClient = useQueryClient()

  const { register, reset, formState, submit, serverError } = useApiForm<ClientFormValues>({
    schema: clientSchema,
    defaultValues: EMPTY,
    successToast: isEdit ? "Client updated" : "Client created",
    onSubmit: async (values) => {
      const payload = {
        name: values.name,
        code: values.code,
        tier: values.tier ? (values.tier as ClientTier) : null,
        contact_info: {
          email: values.email || null,
          phone: values.phone || null,
          address: values.address || null,
        },
        billing_address: hasBillingFields(values)
          ? {
              street: values.billing_street || null,
              city: values.billing_city || null,
              postal_code: values.billing_postal || null,
              country: values.billing_country || null,
            }
          : null,
      }
      const result = client
        ? await clientsApi.update(client.id, payload)
        : await clientsApi.create(payload as Parameters<typeof clientsApi.create>[0])
      await queryClient.invalidateQueries({ queryKey: ["clients", "list"] })
      if (client) {
        await queryClient.invalidateQueries({ queryKey: ["clients", "detail", client.id] })
      }
      onSaved?.(result)
      onOpenChange(false)
      reset(EMPTY)
    },
  })

  useEffect(() => {
    if (!open) return
    if (client) {
      reset({
        name: client.name,
        code: client.code,
        tier: client.tier ?? "",
        email: client.contact_info?.email ?? "",
        phone: client.contact_info?.phone ?? "",
        address: client.contact_info?.address ?? "",
        billing_street: client.billing_address?.street ?? "",
        billing_city: client.billing_address?.city ?? "",
        billing_postal: client.billing_address?.postal_code ?? "",
        billing_country: client.billing_address?.country ?? "",
      })
    } else {
      reset(EMPTY)
    }
  }, [open, client, reset])

  const errors = formState.errors as Record<string, { message?: string }>

  return (
    <SheetForm
      open={open}
      onOpenChange={onOpenChange}
      title={isEdit ? "Edit client" : "Add client"}
      description={
        isEdit
          ? "Update identity, tiering, and contact details."
          : "Create a new corporate client. You can link contracts, services, and staff after saving."
      }
      size="md"
      onSubmit={submit}
      isSubmitting={formState.isSubmitting}
      serverError={serverError}
      submitLabel={isEdit ? "Save changes" : "Create client"}
      submittingLabel={isEdit ? "Saving…" : "Creating…"}
    >
      <FormSection title="Identity">
        <FormField
          label="Name"
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
            className="font-mono"
            {...register("code")}
          />
        </FormField>
      </FormSection>

      <FormSection title="Tiering">
        <FormField label="Tier" optional error={errors.tier?.message} htmlFor="cs-tier">
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
          <Input id="cs-email" type="email" placeholder="contact@acme.com" {...register("email")} />
        </FormField>
        <FormField
          label="Phone"
          optional
          error={(errors["contact_info.phone"]?.message ?? errors.phone?.message) as string | undefined}
          htmlFor="cs-phone"
        >
          <Input id="cs-phone" type="tel" placeholder="+256 …" {...register("phone")} />
        </FormField>
        <FormField
          label="Address"
          optional
          error={errors.address?.message}
          htmlFor="cs-address"
        >
          <Input id="cs-address" placeholder="Street, city" {...register("address")} />
        </FormField>
      </FormSection>

      <FormSection
        title="Billing address"
        description="Where invoices are sent. Leave blank if same as contact address."
      >
        <FormField
          label="Street"
          optional
          error={errors.billing_street?.message}
          htmlFor="cs-billing-street"
        >
          <Input id="cs-billing-street" {...register("billing_street")} />
        </FormField>
        <div className="grid grid-cols-2 gap-3">
          <FormField
            label="City"
            optional
            error={errors.billing_city?.message}
            htmlFor="cs-billing-city"
          >
            <Input id="cs-billing-city" {...register("billing_city")} />
          </FormField>
          <FormField
            label="Postal code"
            optional
            error={errors.billing_postal?.message}
            htmlFor="cs-billing-postal"
          >
            <Input id="cs-billing-postal" {...register("billing_postal")} />
          </FormField>
        </div>
        <FormField
          label="Country"
          optional
          error={errors.billing_country?.message}
          htmlFor="cs-billing-country"
        >
          <Input id="cs-billing-country" placeholder="Uganda" {...register("billing_country")} />
        </FormField>
      </FormSection>
    </SheetForm>
  )
}

function hasBillingFields(v: ClientFormValues): boolean {
  return Boolean(
    v.billing_street?.trim() ||
      v.billing_city?.trim() ||
      v.billing_postal?.trim() ||
      v.billing_country?.trim(),
  )
}
