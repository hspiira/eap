import { Controller } from "react-hook-form"
import { z } from "zod"

import {
  type ProviderCreateRequest,
  type ProviderProfileInput,
  providersApi,
} from "@/api/endpoints/providers"
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
import { Textarea } from "@/components/ui/textarea"
import { useEntityFormSheet } from "@/hooks/useEntityFormSheet"
import type { Provider } from "@/types/entities"
import { ProviderTier, UgandaRegion } from "@/types/enums"
import { getStatusLabel } from "@/utils/statusColors"

const TIERS = Object.values(ProviderTier)
const REGIONS = Object.values(UgandaRegion)

const providerSchema = z.object({
  display_name: z.string().trim().min(1, "A practitioner needs a name"),
  email: z.union([z.literal(""), z.string().trim().email("Enter a valid email address")]),
  phone: z.string().trim(),
  tier: z.enum(ProviderTier),
  region: z.enum(UgandaRegion),
  bio: z.string(),
  specialties: z.string(),
})

type ProviderFormValues = z.infer<typeof providerSchema>

const DEFAULTS: ProviderFormValues = {
  display_name: "",
  email: "",
  phone: "",
  tier: ProviderTier.T2,
  region: UgandaRegion.CENTRAL,
  bio: "",
  specialties: "",
}

/** Empty input clears a nullable field; the API reads null as "clear". */
function nullable(value: string): string | null {
  const trimmed = value.trim()
  return trimmed ? trimmed : null
}

function parseSpecialties(value: string): string[] {
  return value
    .split(",")
    .map((entry) => entry.trim())
    .filter(Boolean)
}

/**
 * Ordinary fields only. Tier is absent on edit because the API rejects the key
 * outright: tier moves through the audited tier command, not general edit.
 */
function editPayload(values: ProviderFormValues): ProviderProfileInput {
  return {
    display_name: values.display_name.trim(),
    email: nullable(values.email),
    phone: nullable(values.phone),
    region: values.region,
    bio: nullable(values.bio),
    specialties: parseSpecialties(values.specialties),
  }
}

function createPayload(values: ProviderFormValues): ProviderCreateRequest {
  return {
    ...editPayload(values),
    display_name: values.display_name.trim(),
    tier: values.tier,
    region: values.region,
  }
}

interface ProviderFormSheetProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  provider?: Provider | null
  onSaved?: (provider: Provider) => void
}

export function ProviderFormSheet({
  open,
  onOpenChange,
  provider,
  onSaved,
}: ProviderFormSheetProps) {
  const { register, control, formState, submit, serverError, isEdit } = useEntityFormSheet<
    ProviderFormValues,
    ProviderFormValues,
    Provider,
    Provider
  >({
    resource: "providers",
    schema: providerSchema,
    defaultValues: DEFAULTS,
    open,
    onOpenChange,
    entity: provider,
    toFormValues: (p) => ({
      display_name: p.display_name,
      email: p.email ?? "",
      phone: p.phone ?? "",
      tier: p.provider_profile.tier,
      region: p.provider_profile.region,
      bio: p.provider_profile.bio ?? "",
      specialties: p.provider_profile.specialties.join(", "),
    }),
    parsePayload: (values) => values,
    save: ({ payload, entity, isEdit }) =>
      isEdit && entity
        ? providersApi.update(entity.id, editPayload(payload))
        : providersApi.create(createPayload(payload)),
    successToast: { create: "Practitioner created", update: "Practitioner updated" },
    onSaved,
  })

  const errors = formState.errors

  return (
    <SheetForm
      open={open}
      onOpenChange={onOpenChange}
      title={isEdit ? "Edit practitioner" : "New practitioner"}
      description={
        isEdit
          ? "Name, contact details and profile. Tier, panel status, accreditation and record status change through their own actions on the practitioner page."
          : "A practitioner does not need a login. Contact details are optional and can be added later."
      }
      size="lg"
      onSubmit={submit}
      isSubmitting={formState.isSubmitting}
      serverError={serverError}
      submitLabel={isEdit ? "Save changes" : "Create practitioner"}
      submittingLabel={isEdit ? "Saving…" : "Creating…"}
    >
      <FormSection title="Identity">
        <FormField
          label="Display name"
          required
          error={errors.display_name?.message}
          htmlFor="prv-name"
        >
          <Input id="prv-name" placeholder="e.g. Amina Okello" {...register("display_name")} />
        </FormField>

        <FormField
          label="Contact email"
          optional
          description="How to reach the practitioner. This is not a login, and linking an account does not change it."
          error={errors.email?.message}
          hint="Leave empty to clear."
          htmlFor="prv-email"
        >
          <Input
            id="prv-email"
            type="email"
            placeholder="name@example.com"
            {...register("email")}
          />
        </FormField>

        <FormField
          label="Contact phone"
          optional
          error={errors.phone?.message}
          hint="Leave empty to clear."
          htmlFor="prv-phone"
        >
          <Input id="prv-phone" type="tel" placeholder="+256…" {...register("phone")} />
        </FormField>
      </FormSection>

      <FormSection title="Profile">
        {isEdit ? null : (
          <FormField label="Tier" required error={errors.tier?.message} htmlFor="prv-tier">
            <Controller
              control={control}
              name="tier"
              render={({ field }) => (
                <Select value={field.value ?? ""} onValueChange={field.onChange}>
                  <SelectTrigger id="prv-tier">
                    <SelectValue placeholder="-" />
                  </SelectTrigger>
                  <SelectContent>
                    {TIERS.map((tier) => (
                      <SelectItem key={tier} value={tier}>
                        {tier}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              )}
            />
          </FormField>
        )}

        <FormField label="Region" required error={errors.region?.message} htmlFor="prv-region">
          <Controller
            control={control}
            name="region"
            render={({ field }) => (
              <Select value={field.value ?? ""} onValueChange={field.onChange}>
                <SelectTrigger id="prv-region">
                  <SelectValue placeholder="-" />
                </SelectTrigger>
                <SelectContent>
                  {REGIONS.map((region) => (
                    <SelectItem key={region} value={region}>
                      {getStatusLabel(region)}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            )}
          />
        </FormField>

        <FormField
          label="Specialties"
          optional
          description="Comma separated."
          error={errors.specialties?.message}
          htmlFor="prv-specialties"
        >
          <Input
            id="prv-specialties"
            placeholder="Trauma, Substance use"
            {...register("specialties")}
          />
        </FormField>

        <FormField label="Bio" optional error={errors.bio?.message} htmlFor="prv-bio">
          <Textarea id="prv-bio" rows={4} {...register("bio")} />
        </FormField>
      </FormSection>
    </SheetForm>
  )
}
