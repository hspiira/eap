import { Controller } from "react-hook-form"
import { z } from "zod"

import { type MemberNextOfKinRequest, membersApi } from "@/api/endpoints/members"
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
import { useEntityFormSheet } from "@/hooks/useEntityFormSheet"
import type { MemberNextOfKin } from "@/types/entities"
import { NextOfKinRelationship } from "@/types/enums"

const RELATIONSHIPS = [
  { value: NextOfKinRelationship.SPOUSE, label: "Spouse" },
  { value: NextOfKinRelationship.CHILD, label: "Child" },
  { value: NextOfKinRelationship.PARENT, label: "Parent" },
  { value: NextOfKinRelationship.SIBLING, label: "Sibling" },
  { value: NextOfKinRelationship.GUARDIAN, label: "Guardian" },
  { value: NextOfKinRelationship.PARTNER, label: "Partner" },
  { value: NextOfKinRelationship.OTHER, label: "Other" },
] as const
const RELATIONSHIP_VALUES = RELATIONSHIPS.map(({ value }) => value) as [
  NextOfKinRelationship,
  ...NextOfKinRelationship[],
]
const optionalText = () => z.string().trim().optional()
const optionalEmail = () =>
  optionalText().refine(
    (value) => !value || /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(value),
    "Invalid email",
  )

const schema = z
  .object({
    name: z.string().trim().min(1, "Name is required"),
    relationship: z.enum(RELATIONSHIP_VALUES),
    phone: optionalText(),
    email: optionalEmail(),
    is_primary: z.boolean(),
  })
  .superRefine((value, ctx) => {
    if (!value.phone && !value.email) {
      ctx.addIssue({
        code: "custom",
        path: ["phone"],
        message: "Phone or email is required",
      })
    }
  })

type FormValues = z.infer<typeof schema>

const EMPTY: FormValues = {
  name: "",
  relationship: NextOfKinRelationship.OTHER,
  phone: "",
  email: "",
  is_primary: false,
}

export function MemberNextOfKinFormSheet({
  open,
  onOpenChange,
  memberId,
  contact,
  onSaved,
}: {
  open: boolean
  onOpenChange: (open: boolean) => void
  memberId: string
  contact?: MemberNextOfKin | null
  onSaved?: (contact: MemberNextOfKin) => void
}) {
  const form = useEntityFormSheet<FormValues, FormValues, MemberNextOfKin, MemberNextOfKin>({
    resource: "member-next-of-kin",
    schema,
    defaultValues: contact ? toValues(contact) : EMPTY,
    open,
    onOpenChange,
    entity: contact,
    toFormValues: toValues,
    parsePayload: (values) => values,
    save: async ({ payload, entity, isEdit }) => {
      const data = toRequest(payload)
      return isEdit && entity
        ? membersApi.updateNextOfKin(memberId, entity.id, data)
        : membersApi.createNextOfKin(memberId, data)
    },
    successToast: { create: "Next-of-kin contact added", update: "Next-of-kin contact updated" },
    onSaved,
  })
  const errors = form.formState.errors

  return (
    <SheetForm
      open={open}
      onOpenChange={onOpenChange}
      title={contact ? "Edit next-of-kin" : "Add next-of-kin"}
      onSubmit={form.submit}
      isSubmitting={form.formState.isSubmitting}
      serverError={form.serverError}
      submitLabel={contact ? "Save changes" : "Add contact"}
    >
      <FormSection title="Contact details">
        <FormField label="Name" htmlFor="kin-name" required error={errors.name?.message}>
          <Input id="kin-name" {...form.register("name")} />
        </FormField>
        <FormField
          label="Relationship"
          htmlFor="kin-relationship"
          required
          error={errors.relationship?.message}
        >
          <Controller
            control={form.control}
            name="relationship"
            render={({ field }) => (
              <Select value={field.value} onValueChange={field.onChange}>
                <SelectTrigger id="kin-relationship" className="rounded-none">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent className="rounded-none">
                  {RELATIONSHIPS.map((option) => (
                    <SelectItem key={option.value} value={option.value} className="rounded-none">
                      {option.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            )}
          />
        </FormField>
        <FormField label="Phone" htmlFor="kin-phone" error={errors.phone?.message}>
          <Input id="kin-phone" type="tel" {...form.register("phone")} />
        </FormField>
        <FormField label="Email" htmlFor="kin-email" error={errors.email?.message}>
          <Input id="kin-email" type="email" {...form.register("email")} />
        </FormField>
        <label className="flex items-center gap-2 text-xs text-fg/80">
          <Controller
            control={form.control}
            name="is_primary"
            render={({ field }) => (
              <Checkbox
                checked={field.value}
                onCheckedChange={(checked) => field.onChange(checked)}
              />
            )}
          />
          Primary contact
        </label>
      </FormSection>
    </SheetForm>
  )
}

function toValues(contact: MemberNextOfKin): FormValues {
  return {
    name: contact.name,
    relationship: contact.relationship,
    phone: contact.phone ?? "",
    email: contact.email ?? "",
    is_primary: contact.is_primary,
  }
}

function toRequest(values: FormValues): MemberNextOfKinRequest {
  return {
    name: values.name.trim(),
    relationship: values.relationship,
    phone: optionalValue(values.phone),
    email: optionalValue(values.email),
    is_primary: values.is_primary,
  }
}

function optionalValue(value: string | undefined) {
  const normalized = value?.trim()
  return normalized || null
}
