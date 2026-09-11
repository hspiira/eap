import { useEffect, useState } from "react"

import { Controller } from "react-hook-form"
import { z } from "zod"

import { providerAliasesApi } from "@/api/endpoints/provider-aliases"
import {
  type ProviderCreateRequest,
  type ProviderProfileInput,
  providersApi,
} from "@/api/endpoints/providers"
import { FormField } from "@/components/common/FormField"
import { FormSection } from "@/components/common/FormSection"
import { SheetForm } from "@/components/common/SheetForm"
import { Checkbox } from "@/components/ui/checkbox"
import { Input } from "@/components/ui/input"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import { Textarea } from "@/components/ui/textarea"
import { useToast } from "@/contexts/ToastContext"
import { useCurrentRole } from "@/hooks/useCanWrite"
import { useEntityFormSheet } from "@/hooks/useEntityFormSheet"
import { useTenantStore } from "@/store/slices/tenantSlice"
import type { Provider } from "@/types/entities"
import {
  ProviderGender,
  ProviderTier,
  ProviderTitle,
  TenantRole,
  UgandaRegion,
} from "@/types/enums"
import { getStatusLabel } from "@/utils/statusColors"

/** The source system session import consults. Matches SessionImportDialog. */
const ACTIVITY_LOG = "activity-log-workbook"

const TIERS = Object.values(ProviderTier)
const REGIONS = Object.values(UgandaRegion)
const TITLE_VALUES = Object.values(ProviderTitle) as [ProviderTitle, ...ProviderTitle[]]
const GENDER_VALUES = Object.values(ProviderGender) as [ProviderGender, ...ProviderGender[]]
const GENDERS: ReadonlyArray<{ value: ProviderGender; label: string }> = [
  { value: ProviderGender.FEMALE, label: "Female" },
  { value: ProviderGender.MALE, label: "Male" },
]

const providerSchema = z.object({
  display_name: z.string().trim().min(1, "A practitioner needs a name"),
  email: z.union([z.literal(""), z.string().trim().email("Enter a valid email address")]),
  phone: z.string().trim(),
  tier: z.enum(ProviderTier),
  region: z.enum(UgandaRegion),
  gender: z.enum(GENDER_VALUES).optional(),
  title: z.enum(TITLE_VALUES).optional(),
  bio: z.string(),
})

type ProviderFormValues = z.infer<typeof providerSchema>

const DEFAULTS: ProviderFormValues = {
  display_name: "",
  email: "",
  phone: "",
  tier: ProviderTier.T2,
  region: UgandaRegion.CENTRAL,
  gender: undefined,
  title: undefined,
  bio: "",
}

/** Empty input clears a nullable field; the API reads null as "clear". */
function nullable(value: string): string | null {
  const trimmed = value.trim()
  return trimmed ? trimmed : null
}

/**
 * Ordinary fields only. Tier and specialties are absent because the API
 * rejects those keys outright: tier moves through the audited tier command,
 * and specialties are catalogue links managed on the practitioner page.
 */
function editPayload(values: ProviderFormValues): ProviderProfileInput {
  return {
    display_name: values.display_name.trim(),
    email: nullable(values.email),
    phone: nullable(values.phone),
    region: values.region,
    gender: values.gender ?? null,
    title: values.title ?? null,
    bio: nullable(values.bio),
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
  const tenantId = useTenantStore((state) => state.currentTenantId)
  const isAdmin = useCurrentRole() === TenantRole.ADMIN
  const toast = useToast()
  // Not part of the practitioner payload: it names a separate, audited alias
  // decision, so it stays out of the schema the API receives.
  const [matchInImports, setMatchInImports] = useState(false)

  useEffect(() => {
    if (open) setMatchInImports(false)
  }, [open])

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
      // Empty, not a default: the form requires both, so editing an
      // unassessed import forces a person to choose rather than having a
      // suggestion silently become the assessment.
      tier: p.provider_profile.tier ?? ("" as unknown as ProviderTier),
      region: p.provider_profile.region ?? ("" as unknown as UgandaRegion),
      gender: p.provider_profile.gender ?? undefined,
      title: p.provider_profile.title ?? undefined,
      bio: p.provider_profile.bio ?? "",
    }),
    parsePayload: (values) => values,
    save: async ({ payload, entity, isEdit }) => {
      if (isEdit && entity) return providersApi.update(entity.id, editPayload(payload))
      const created = await providersApi.create(createPayload(payload))
      await claimImportName(created)
      return created
    },
    successToast: { create: "Practitioner created", update: "Practitioner updated" },
    onSaved,
  })

  /**
   * Name this practitioner for the spelling just typed, when asked to.
   *
   * Deliberately after the practitioner exists and never fatal: the record is
   * already written, so a failure here is reported and left for the aliases
   * page rather than rolled back into a misleading form error.
   */
  async function claimImportName(created: Provider) {
    if (!matchInImports || !tenantId) return
    try {
      const { claimed } = await providerAliasesApi.adopt(
        tenantId,
        ACTIVITY_LOG,
        created.display_name,
        created.id,
      )
      toast.showSuccess(
        claimed
          ? `Imports naming ${created.display_name} now resolve to this practitioner`
          : `${created.display_name} is already resolved to another practitioner; left as it is`,
      )
    } catch {
      toast.showError(
        `Practitioner created, but ${created.display_name} could not be matched for imports. Do it on the Name aliases page.`,
      )
    }
  }

  const errors = formState.errors

  return (
    <SheetForm
      open={open}
      onOpenChange={onOpenChange}
      title={isEdit ? "Edit practitioner" : "New practitioner"}
      description={
        isEdit
          ? "Name, contact details and profile. Tier, panel status, accreditation, record status and specialties change through their own actions on the practitioner page."
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
          label="Title"
          description="Kept apart from the name, so the name stays matchable when an import writes it as DR. AMINA OKELLO."
          error={errors.title?.message}
          htmlFor="prv-title"
        >
          <Controller
            control={control}
            name="title"
            render={({ field }) => (
              <Select
                value={field.value ?? "unset"}
                onValueChange={(value) => field.onChange(value === "unset" ? undefined : value)}
              >
                <SelectTrigger id="prv-title">
                  <SelectValue placeholder="No title" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="unset">No title</SelectItem>
                  {TITLE_VALUES.map((value) => (
                    <SelectItem key={value} value={value}>
                      {value}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            )}
          />
        </FormField>

        <FormField
          label="Display name"
          required
          description="The name alone. A title typed here would be stripped back out whenever an import matches on it."
          error={errors.display_name?.message}
          htmlFor="prv-name"
        >
          <Input id="prv-name" placeholder="e.g. Amina Okello" {...register("display_name")} />
        </FormField>

        <FormField
          label="Contact email"
          description="How to reach the practitioner. This is not a login, and linking an account does not change it."
          error={errors.email?.message}
          htmlFor="prv-email"
        >
          <Input
            id="prv-email"
            type="email"
            placeholder="name@example.com"
            {...register("email")}
          />
        </FormField>

        <FormField label="Contact phone" error={errors.phone?.message} htmlFor="prv-phone">
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

        <FormField label="Gender" error={errors.gender?.message} htmlFor="prv-gender">
          <Controller
            control={control}
            name="gender"
            render={({ field }) => (
              <Select
                value={field.value ?? "unset"}
                onValueChange={(value) => field.onChange(value === "unset" ? undefined : value)}
              >
                <SelectTrigger id="prv-gender">
                  <SelectValue placeholder="Select gender" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="unset">Not recorded</SelectItem>
                  {GENDERS.map((option) => (
                    <SelectItem key={option.value} value={option.value}>
                      {option.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            )}
          />
        </FormField>

        <FormField label="Bio" error={errors.bio?.message} htmlFor="prv-bio">
          <Textarea id="prv-bio" rows={4} {...register("bio")} />
        </FormField>
      </FormSection>

      {!isEdit && isAdmin ? (
        <FormSection title="Historical imports">
          <label className="flex items-start gap-2.5" htmlFor="prv-match-imports">
            <Checkbox
              id="prv-match-imports"
              checked={matchInImports}
              onCheckedChange={(checked) => setMatchInImports(checked === true)}
              className="mt-0.5"
            />
            <span className="text-sm text-fg">
              Match this name in imported activity logs
              <span className="mt-0.5 block text-xs text-fg-muted">
                Records that the name above is this practitioner, so import rows spelling it that
                way resolve instead of stalling. Audited as your decision. A spelling already
                resolved to somebody else is left alone. Other spellings are still yours to map on
                the Name aliases page.
              </span>
            </span>
          </label>
        </FormSection>
      ) : null}
    </SheetForm>
  )
}
