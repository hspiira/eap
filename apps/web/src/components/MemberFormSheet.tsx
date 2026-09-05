import { useQuery } from "@tanstack/react-query"
import { Controller } from "react-hook-form"
import { z } from "zod"

import { clientsApi } from "@/api/endpoints/clients"
import { type MemberListParams, membersApi } from "@/api/endpoints/members"
import { DatePicker } from "@/components/common/DatePicker"
import { ClientPicker, EntityPicker, PickerRow } from "@/components/common/EntityPicker"
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
import { useEntityFormSheet, type UseEntityFormSheetReturn } from "@/hooks/useEntityFormSheet"
import { nameInitials } from "@/lib/display"
import type { Client, Member } from "@/types/entities"
import { MemberGender, MemberRelation } from "@/types/enums"

const RELATIONS = [
  { value: MemberRelation.EMPLOYEE, label: "Employee" },
  { value: MemberRelation.SPOUSE, label: "Spouse" },
  { value: MemberRelation.CHILD, label: "Child" },
  { value: MemberRelation.DOMESTIC_PARTNER, label: "Domestic partner" },
  { value: MemberRelation.DEPENDENT_OTHER, label: "Other beneficiary" },
] as const

const RELATION_VALUES = RELATIONS.map(({ value }) => value) as [MemberRelation, ...MemberRelation[]]
const GENDERS = [
  { value: MemberGender.FEMALE, label: "Female" },
  { value: MemberGender.MALE, label: "Male" },
  { value: MemberGender.NON_BINARY, label: "Non-binary" },
  { value: MemberGender.PREFER_NOT_TO_SAY, label: "Prefer not to say" },
  { value: MemberGender.UNKNOWN, label: "Unknown" },
] as const
const GENDER_VALUES = GENDERS.map(({ value }) => value) as [MemberGender, ...MemberGender[]]
const optionalText = () => z.string().trim().optional()
const optionalEmail = () =>
  optionalText().refine(
    (value) => !value || /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(value),
    "Invalid email",
  )

const memberSchema = z
  .object({
    client_id: z.string().trim().min(1, "Client is required"),
    employer_member_id: optionalText(),
    relation: z.enum(RELATION_VALUES),
    primary_employee_member_id: optionalText(),
    work_email: optionalEmail(),
    personal_email: optionalEmail(),
    display_label: z.string().trim().min(1, "Name is required"),
    date_of_birth: optionalText(),
    gender: z.enum(GENDER_VALUES).optional(),
    phone: optionalText(),
    staff_number: optionalText(),
    national_id: optionalText(),
    passport_number: optionalText(),
  })
  .superRefine((value, ctx) => {
    if (value.relation !== MemberRelation.EMPLOYEE && !value.primary_employee_member_id?.trim()) {
      ctx.addIssue({
        code: "custom",
        path: ["primary_employee_member_id"],
        message: "Primary employee is required for a beneficiary",
      })
    }
  })

type MemberFormValues = z.infer<typeof memberSchema>

const EMPTY: MemberFormValues = {
  client_id: "",
  employer_member_id: "",
  relation: MemberRelation.EMPLOYEE,
  primary_employee_member_id: "",
  work_email: "",
  personal_email: "",
  display_label: "",
  date_of_birth: "",
  gender: undefined,
  phone: "",
  staff_number: "",
  national_id: "",
  passport_number: "",
}

interface MemberFormSheetProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  member?: Member | null
  clientId?: string
  client?: Client | null
  onSaved?: (member: Member) => void
}

export function MemberFormSheet({
  open,
  onOpenChange,
  member,
  clientId,
  client,
  onSaved,
}: MemberFormSheetProps) {
  const selectedClientId = client?.id ?? member?.client_id ?? clientId
  const clientQuery = useQuery({
    queryKey: ["clients", "detail", selectedClientId],
    queryFn: () => clientsApi.getById(selectedClientId!),
    enabled: open && Boolean(selectedClientId) && !client,
    staleTime: 5 * 60 * 1000,
  })
  const resolvedClient = client ?? clientQuery.data
  const initialValues: MemberFormValues = member
    ? toValues(member)
    : { ...EMPTY, client_id: selectedClientId ?? "" }
  const form = useEntityFormSheet<MemberFormValues, MemberFormValues, Member, Member>({
    resource: "members",
    schema: memberSchema,
    defaultValues: initialValues,
    open,
    onOpenChange,
    entity: member,
    toFormValues: toValues,
    parsePayload: (values) => values,
    save: async ({ payload, entity, isEdit }) => {
      const data = toRequest(payload)
      const saved =
        isEdit && entity
          ? await membersApi.update(entity.id, omitClientId(data))
          : await membersApi.create(data)
      return saved
    },
    successToast: { create: "Member added", update: "Member updated" },
    extraInvalidations: [{ queryKey: ["clients", "list"] }],
    onSaved,
  })

  return (
    <SheetForm
      open={open}
      onOpenChange={onOpenChange}
      title={member ? "Edit member" : "Add member"}
      description="Client-covered employee or beneficiary."
      size="lg"
      onSubmit={form.submit}
      isSubmitting={form.formState.isSubmitting}
      serverError={form.serverError}
      submitLabel={member ? "Save changes" : "Add member"}
    >
      <p className="text-xs text-fg-muted">Fields marked * are required.</p>
      <MemberIdentityFields form={form} member={member} resolvedClient={resolvedClient} />

      <MemberPersonalFields form={form} />

      <MemberIdentifierFields form={form} />

      <MemberContactFields form={form} />
    </SheetForm>
  )
}

function toValues(member: Member): MemberFormValues {
  return {
    client_id: member.client_id,
    employer_member_id: member.employer_member_id,
    relation: member.relation,
    primary_employee_member_id: member.primary_employee_member_id ?? "",
    work_email: member.work_email ?? "",
    personal_email: member.personal_email ?? "",
    display_label: member.display_label ?? "",
    date_of_birth: member.date_of_birth ?? "",
    gender: member.gender ?? undefined,
    phone: member.phone ?? "",
    staff_number: member.staff_number ?? "",
    national_id: member.national_id ?? "",
    passport_number: member.passport_number ?? "",
  }
}

function toRequest(values: MemberFormValues) {
  return {
    client_id: values.client_id.trim(),
    employer_member_id: optionalValue(values.employer_member_id),
    relation: values.relation,
    primary_employee_member_id:
      values.relation === MemberRelation.EMPLOYEE
        ? null
        : optionalValue(values.primary_employee_member_id),
    work_email: optionalValue(values.work_email),
    personal_email: optionalValue(values.personal_email),
    display_label: values.display_label.trim(),
    date_of_birth: optionalValue(values.date_of_birth),
    gender: values.gender ?? null,
    phone: optionalValue(values.phone),
    staff_number: optionalValue(values.staff_number),
    national_id: optionalValue(values.national_id),
    passport_number: optionalValue(values.passport_number),
  }
}

function optionalValue(value: string | undefined) {
  const normalized = value?.trim()
  return normalized || null
}

function omitClientId({ client_id: _clientId, ...data }: ReturnType<typeof toRequest>) {
  return data
}

function PrimaryMemberPicker({
  clientId,
  value,
  onChange,
}: {
  clientId: string
  value: string
  onChange: (id: string) => void
}) {
  return (
    <EntityPicker<Member, MemberListParams>
      resource="members"
      listFn={membersApi.list}
      value={value}
      onChange={onChange}
      placeholder="Search primary employee…"
      emptyPrompt="Start typing to search employees."
      emptyNoMatch="No employees match."
      params={{ client_id: clientId, relation: MemberRelation.EMPLOYEE }}
      renderSelected={(item) => (
        <PickerRow
          initials={nameInitials(item.display_label ?? item.employer_member_id)}
          primary={item.display_label ?? item.employer_member_id}
          secondary={item.employer_member_id}
          size="md"
        />
      )}
      renderRow={(item) => (
        <PickerRow
          initials={nameInitials(item.display_label ?? item.employer_member_id)}
          primary={item.display_label ?? item.employer_member_id}
          secondary={item.employer_member_id}
        />
      )}
    />
  )
}

function MemberIdentityFields({
  form,
  member,
  resolvedClient,
}: {
  form: UseEntityFormSheetReturn<MemberFormValues>
  member?: Member | null
  resolvedClient?: Client | null
}) {
  const errors = form.formState.errors
  const watchedRelation = form.watch("relation")
  return (
    <FormSection title="Member identity">
      {!member ? (
        <FormField label="Client" required error={errors.client_id?.message}>
          <Controller
            control={form.control}
            name="client_id"
            render={({ field }) => (
              <ClientPicker
                value={field.value}
                onChange={(id) => {
                  field.onChange(id)
                  form.setValue("primary_employee_member_id", "")
                }}
                selected={resolvedClient}
              />
            )}
          />
        </FormField>
      ) : (
        <FormField
          label="Client"
          hint="Client reassignment is handled as a separate controlled workflow."
        >
          <div className="border border-fg/15 bg-surface px-3 py-2 text-sm text-fg">
            {resolvedClient?.name ?? member.client_id}
          </div>
        </FormField>
      )}
      <FormField
        label="Member code"
        htmlFor="member-code"
        hint={
          member
            ? "Changing this breaks references in exports already shared with the client."
            : `Leave blank to issue the next code automatically${
                resolvedClient ? ` (${resolvedClient.code}-001, -002, …)` : ""
              }.`
        }
        error={errors.employer_member_id?.message}
      >
        <Input
          id="member-code"
          {...form.register("employer_member_id")}
          placeholder={resolvedClient ? `${resolvedClient.code}-001` : "Auto-generated"}
        />
      </FormField>
      <FormField label="Name" htmlFor="member-name" required error={errors.display_label?.message}>
        <Input
          id="member-name"
          {...form.register("display_label")}
          placeholder="e.g. Amina Namukasa"
        />
      </FormField>
      <FormField
        label="Relationship"
        htmlFor="member-relation"
        required
        error={errors.relation?.message}
      >
        <Controller
          control={form.control}
          name="relation"
          render={({ field }) => (
            <Select value={field.value} onValueChange={field.onChange}>
              <SelectTrigger id="member-relation" className="rounded-none">
                <SelectValue />
              </SelectTrigger>
              <SelectContent className="rounded-none">
                {RELATIONS.map((option) => (
                  <SelectItem key={option.value} value={option.value} className="rounded-none">
                    {option.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          )}
        />
      </FormField>
      {watchedRelation !== MemberRelation.EMPLOYEE ? (
        <FormField
          label="Primary employee"
          required
          error={errors.primary_employee_member_id?.message}
        >
          <Controller
            control={form.control}
            name="primary_employee_member_id"
            render={({ field }) => (
              <PrimaryMemberPicker
                key={form.watch("client_id")}
                clientId={form.watch("client_id")}
                value={field.value ?? ""}
                onChange={field.onChange}
              />
            )}
          />
        </FormField>
      ) : null}
    </FormSection>
  )
}

function MemberPersonalFields({ form }: { form: UseEntityFormSheetReturn<MemberFormValues> }) {
  const errors = form.formState.errors
  return (
    <FormSection title="Personal details">
      <div className="grid gap-4 sm:grid-cols-2">
        <FormField label="Date of birth" error={errors.date_of_birth?.message}>
          <Controller
            control={form.control}
            name="date_of_birth"
            render={({ field }) => (
              <DatePicker
                id="member-date-of-birth"
                aria-label="Date of birth"
                value={field.value}
                onChange={field.onChange}
                placeholder="Select date"
              />
            )}
          />
        </FormField>
        <FormField label="Gender" htmlFor="member-gender" error={errors.gender?.message}>
          <Controller
            control={form.control}
            name="gender"
            render={({ field }) => (
              <Select
                value={field.value ?? "unset"}
                onValueChange={(value) => field.onChange(value === "unset" ? undefined : value)}
              >
                <SelectTrigger id="member-gender" className="rounded-none">
                  <SelectValue placeholder="Select gender" />
                </SelectTrigger>
                <SelectContent className="rounded-none">
                  <SelectItem value="unset" className="rounded-none">
                    Not recorded
                  </SelectItem>
                  {GENDERS.map((option) => (
                    <SelectItem key={option.value} value={option.value} className="rounded-none">
                      {option.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            )}
          />
        </FormField>
      </div>
    </FormSection>
  )
}

function MemberIdentifierFields({ form }: { form: UseEntityFormSheetReturn<MemberFormValues> }) {
  const errors = form.formState.errors
  return (
    <FormSection
      title="Identification"
      description="Optional. Recorded for verification; none of these is the member code."
    >
      <div className="grid gap-4 sm:grid-cols-3">
        <FormField
          label="Company ID number"
          htmlFor="member-staff-number"
          error={errors.staff_number?.message}
        >
          <Input id="member-staff-number" {...form.register("staff_number")} />
        </FormField>
        <FormField
          label="National ID (NIN)"
          htmlFor="member-national-id"
          error={errors.national_id?.message}
        >
          <Input id="member-national-id" {...form.register("national_id")} />
        </FormField>
        <FormField
          label="Passport number"
          htmlFor="member-passport-number"
          error={errors.passport_number?.message}
        >
          <Input id="member-passport-number" {...form.register("passport_number")} />
        </FormField>
      </div>
    </FormSection>
  )
}

function MemberContactFields({ form }: { form: UseEntityFormSheetReturn<MemberFormValues> }) {
  const errors = form.formState.errors
  return (
    <FormSection title="Contact">
      <FormField label="Phone" htmlFor="member-phone" error={errors.phone?.message}>
        <Input id="member-phone" type="tel" {...form.register("phone")} />
      </FormField>
      <FormField label="Work email" htmlFor="member-work-email" error={errors.work_email?.message}>
        <Input id="member-work-email" type="email" {...form.register("work_email")} />
      </FormField>
      <FormField
        label="Personal email"
        htmlFor="member-personal-email"
        error={errors.personal_email?.message}
      >
        <Input id="member-personal-email" type="email" {...form.register("personal_email")} />
      </FormField>
    </FormSection>
  )
}
