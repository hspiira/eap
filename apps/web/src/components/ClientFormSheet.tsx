import { Controller } from "react-hook-form"
import { z } from "zod"

import { clientsApi } from "@/api/endpoints/clients"
import type { ClientCreate, ClientUpdate } from "@/api/generated"
import { FormField } from "@/components/common/FormField"
import { FormSection } from "@/components/common/FormSection"
import { SheetForm } from "@/components/common/SheetForm"
import { Input } from "@/components/ui/input"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import { useEntityFormSheet } from "@/hooks/useEntityFormSheet"
import type { Client } from "@/types/entities"
import { ClientTier } from "@/types/enums"

const TIER_VALUES = [ClientTier.A, ClientTier.B, ClientTier.C] as const

const clientSchema = z
  .object({
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
    // BE `AddressCreate` requires street/city/country; postal_code is optional.
    // If ANY billing field is set, the user must fill the required trio.
    billing_street: z.string().optional(),
    billing_city: z.string().optional(),
    billing_postal: z.string().optional(),
    billing_country: z.string().optional(),
  })
  .superRefine((d, ctx) => {
    const anyBilling =
      d.billing_street || d.billing_city || d.billing_postal || d.billing_country
    if (!anyBilling) return
    for (const f of ["billing_street", "billing_city", "billing_country"] as const) {
      if (!d[f]?.trim()) {
        ctx.addIssue({
          code: "custom",
          path: [f],
          message: "Required when any billing field is set",
        })
      }
    }
  })

type ClientFormValues = z.infer<typeof clientSchema>

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
  const { register, control, formState, submit, serverError, isEdit } = useEntityFormSheet<
    ClientFormValues,
    ClientCreate & { __tier?: ClientTier | null },
    Client,
    Client
  >({
    resource: "clients",
    schema: clientSchema,
    defaultValues: EMPTY,
    open,
    onOpenChange,
    entity: client,
    toFormValues: (c) => ({
      name: c.name,
      code: c.code,
      tier: c.tier ?? "",
      email: c.contact_info?.email ?? "",
      phone: c.contact_info?.phone ?? "",
      address: c.contact_info?.address ?? "",
      billing_street: c.billing_address?.street ?? "",
      billing_city: c.billing_address?.city ?? "",
      billing_postal: c.billing_address?.postal_code ?? "",
      billing_country: c.billing_address?.country ?? "",
    }),
    parsePayload: (values) => ({
      name: values.name,
      code: values.code,
      contact_info: {
        email: values.email || null,
        phone: values.phone || null,
        address: values.address || null,
      },
      billing_address:
        values.billing_street && values.billing_city && values.billing_country
          ? {
              street: values.billing_street,
              city: values.billing_city,
              country: values.billing_country,
              postal_code: values.billing_postal || null,
            }
          : null,
      // Carried out-of-band so create payload matches BE strict shape.
      __tier: values.tier ? (values.tier as ClientTier) : null,
    }),
    save: async ({ payload, entity, isEdit }) => {
      const { __tier, ...createPayload } = payload
      let saved: Client
      if (isEdit && entity) {
        // BE `ClientUpdate` only accepts `{name?, preferred_contact_method?, tier?}`.
        // Send name in the basic update; tier goes through the dedicated route.
        const update: ClientUpdate = { name: createPayload.name }
        saved = await clientsApi.update(entity.id, update)
        if (__tier !== (entity.tier ?? null)) {
          saved = await clientsApi.setTier(entity.id, __tier ?? null)
        }
      } else {
        saved = await clientsApi.create(createPayload)
        if (__tier) {
          saved = await clientsApi.setTier(saved.id, __tier)
        }
      }
      return saved
    },
    successToast: { create: "Client created", update: "Client updated" },
    onSaved,
  })

  const errors = formState.errors

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
          <Controller
            control={control}
            name="tier"
            render={({ field }) => (
              <Select value={field.value ?? ""} onValueChange={field.onChange}>
                <SelectTrigger id="cs-tier">
                  <SelectValue placeholder="Unassigned" />
                </SelectTrigger>
                <SelectContent>
                  {TIER_VALUES.map((t) => (
                    <SelectItem key={t} value={t}>
                      Tier {t}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            )}
          />
        </FormField>
      </FormSection>

      <FormSection
        title="Primary contact"
        description="Used for billing and account notifications."
      >
        <FormField
          label="Email"
          optional
          error={errors.email?.message}
          htmlFor="cs-email"
        >
          <Input id="cs-email" type="email" placeholder="contact@acme.com" {...register("email")} />
        </FormField>
        <FormField
          label="Phone"
          optional
          error={errors.phone?.message}
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

