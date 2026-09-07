import { z } from "zod"

import {
  type ProviderOrganisationCreateRequest,
  providerOrganisationsApi,
} from "@/api/endpoints/provider-organisations"
import { FormField } from "@/components/common/FormField"
import { SheetForm } from "@/components/common/SheetForm"
import { Input } from "@/components/ui/input"
import { useEntityFormSheet } from "@/hooks/useEntityFormSheet"
import type { ProviderOrganisation } from "@/types/entities"

const organisationSchema = z.object({
  name: z.string().trim().min(1, "An organisation needs a name"),
  registration_number: z.string().trim(),
  contact_email: z.union([z.literal(""), z.string().trim().email("Enter a valid email address")]),
  contact_phone: z.string().trim(),
})

type OrganisationFormValues = z.infer<typeof organisationSchema>

const DEFAULTS: OrganisationFormValues = {
  name: "",
  registration_number: "",
  contact_email: "",
  contact_phone: "",
}

function nullable(value: string): string | null {
  const trimmed = value.trim()
  return trimmed ? trimmed : null
}

function payload(values: OrganisationFormValues): ProviderOrganisationCreateRequest {
  return {
    name: values.name.trim(),
    registration_number: nullable(values.registration_number),
    contact_email: nullable(values.contact_email),
    contact_phone: nullable(values.contact_phone),
  }
}

interface ProviderOrganisationFormSheetProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  organisation?: ProviderOrganisation | null
  onSaved?: (organisation: ProviderOrganisation) => void
}

export function ProviderOrganisationFormSheet({
  open,
  onOpenChange,
  organisation,
  onSaved,
}: ProviderOrganisationFormSheetProps) {
  const { register, formState, submit, serverError, isEdit } = useEntityFormSheet<
    OrganisationFormValues,
    ProviderOrganisationCreateRequest,
    ProviderOrganisation,
    ProviderOrganisation
  >({
    resource: "provider-organisations",
    schema: organisationSchema,
    defaultValues: DEFAULTS,
    open,
    onOpenChange,
    entity: organisation,
    toFormValues: (o) => ({
      name: o.name,
      registration_number: o.registration_number ?? "",
      contact_email: o.contact_email ?? "",
      contact_phone: o.contact_phone ?? "",
    }),
    parsePayload: payload,
    save: ({ payload: body, entity, isEdit }) =>
      isEdit && entity
        ? providerOrganisationsApi.update(entity.id, body)
        : providerOrganisationsApi.create(body),
    successToast: { create: "Organisation created", update: "Organisation updated" },
    onSaved,
  })

  const errors = formState.errors

  return (
    <SheetForm
      open={open}
      onOpenChange={onOpenChange}
      title={isEdit ? "Edit organisation" : "New organisation"}
      description={
        isEdit
          ? "Name and contact details. Supplier approval and active state change through their own actions."
          : "A supplier firm practitioners can deliver through. It starts unapproved and needs an explicit approval before it can take organisation-delivered sessions."
      }
      size="md"
      onSubmit={submit}
      isSubmitting={formState.isSubmitting}
      serverError={serverError}
      submitLabel={isEdit ? "Save changes" : "Create organisation"}
      submittingLabel={isEdit ? "Saving…" : "Creating…"}
    >
      <FormField label="Name" required error={errors.name?.message} htmlFor="org-name">
        <Input id="org-name" placeholder="e.g. Serenity Counselling Ltd" {...register("name")} />
      </FormField>

      <FormField
        label="Registration number"
        error={errors.registration_number?.message}
        hint="Leave empty to clear."
        htmlFor="org-registration"
      >
        <Input id="org-registration" {...register("registration_number")} />
      </FormField>

      <FormField
        label="Contact email"
        error={errors.contact_email?.message}
        hint="Leave empty to clear."
        htmlFor="org-email"
      >
        <Input id="org-email" type="email" {...register("contact_email")} />
      </FormField>

      <FormField
        label="Contact phone"
        error={errors.contact_phone?.message}
        hint="Leave empty to clear."
        htmlFor="org-phone"
      >
        <Input id="org-phone" type="tel" {...register("contact_phone")} />
      </FormField>
    </SheetForm>
  )
}
