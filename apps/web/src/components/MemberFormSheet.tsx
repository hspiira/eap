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
import { useEntityFormSheet } from "@/hooks/useEntityFormSheet"
import { nameInitials } from "@/lib/display"
import type { Client, Member } from "@/types/entities"
import { MemberRelation } from "@/types/enums"

const RELATIONS = [
  { value: MemberRelation.EMPLOYEE, label: "Employee" },
  { value: MemberRelation.SPOUSE, label: "Spouse" },
  { value: MemberRelation.CHILD, label: "Child" },
  { value: MemberRelation.DOMESTIC_PARTNER, label: "Domestic partner" },
  { value: MemberRelation.DEPENDENT_OTHER, label: "Other beneficiary" },
] as const

const RELATION_VALUES = RELATIONS.map(({ value }) => value) as [MemberRelation, ...MemberRelation[]]
const optionalText = () => z.string().trim().optional()
const optionalEmail = () =>
  optionalText().refine(
    (value) => !value || /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(value),
    "Invalid email",
  )

const memberSchema = z
  .object({
    client_id: z.string().trim().min(1, "Client is required"),
    employer_member_id: z.string().trim().min(1, "Member ID is required"),
    relation: z.enum(RELATION_VALUES),
    primary_employee_member_id: optionalText(),
    coverage_start: optionalText(),
    coverage_end: optionalText(),
    work_email: optionalEmail(),
    personal_email: optionalEmail(),
    display_label: z.string().trim().min(1, "Name is required"),
  })
  .superRefine((value, ctx) => {
    if (value.relation !== MemberRelation.EMPLOYEE && !value.primary_employee_member_id?.trim()) {
      ctx.addIssue({
        code: "custom",
        path: ["primary_employee_member_id"],
        message: "Primary employee is required for a beneficiary",
      })
    }
    if (value.coverage_start && value.coverage_end && value.coverage_end < value.coverage_start) {
      ctx.addIssue({ code: "custom", path: ["coverage_end"], message: "Must be after start date" })
    }
  })

type MemberFormValues = z.infer<typeof memberSchema>

const EMPTY: MemberFormValues = {
  client_id: "",
  employer_member_id: "",
  relation: MemberRelation.EMPLOYEE,
  primary_employee_member_id: "",
  coverage_start: "",
  coverage_end: "",
  work_email: "",
  personal_email: "",
  display_label: "",
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
    : { ...EMPTY, client_id: clientId ?? "" }
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
    onSaved,
  })
  const watchedRelation = form.watch("relation")
  const errors = form.formState.errors

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
      <FormSection title="Member identity">
        {!member ? (
          <FormField label="Client" required error={errors.client_id?.message}>
            <Controller
              control={form.control}
              name="client_id"
              render={({ field }) => (
                <ClientPicker
                  value={field.value}
                  onChange={field.onChange}
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
        <FormField label="Member ID" required error={errors.employer_member_id?.message}>
          <Input {...form.register("employer_member_id")} placeholder="e.g. EMP-1042" />
        </FormField>
        <FormField label="Name" required error={errors.display_label?.message}>
          <Input {...form.register("display_label")} placeholder="Name or privacy-safe label" />
        </FormField>
        <FormField label="Relationship" required error={errors.relation?.message}>
          <Controller
            control={form.control}
            name="relation"
            render={({ field }) => (
              <Select value={field.value} onValueChange={field.onChange}>
                <SelectTrigger className="rounded-none">
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
                  clientId={form.watch("client_id")}
                  value={field.value ?? ""}
                  onChange={field.onChange}
                />
              )}
            />
          </FormField>
        ) : null}
      </FormSection>

      <FormSection title="Coverage">
        <div className="grid gap-4 sm:grid-cols-2">
          <FormField label="Coverage starts" error={errors.coverage_start?.message}>
            <Controller
              control={form.control}
              name="coverage_start"
              render={({ field }) => (
                <DatePicker
                  id="member-coverage-start"
                  aria-label="Coverage starts"
                  value={field.value}
                  onChange={field.onChange}
                  placeholder="No start date"
                />
              )}
            />
          </FormField>
          <FormField label="Coverage ends" error={errors.coverage_end?.message}>
            <Controller
              control={form.control}
              name="coverage_end"
              render={({ field }) => (
                <DatePicker
                  id="member-coverage-end"
                  aria-label="Coverage ends"
                  value={field.value}
                  onChange={field.onChange}
                  placeholder="No end date"
                />
              )}
            />
          </FormField>
        </div>
      </FormSection>

      <FormSection title="Contact">
        <FormField label="Work email" error={errors.work_email?.message}>
          <Input type="email" {...form.register("work_email")} />
        </FormField>
        <FormField label="Personal email" error={errors.personal_email?.message}>
          <Input type="email" {...form.register("personal_email")} />
        </FormField>
      </FormSection>
    </SheetForm>
  )
}

function toValues(member: Member): MemberFormValues {
  return {
    client_id: member.client_id,
    employer_member_id: member.employer_member_id,
    relation: member.relation,
    primary_employee_member_id: member.primary_employee_member_id ?? "",
    coverage_start: member.coverage_start ?? "",
    coverage_end: member.coverage_end ?? "",
    work_email: member.work_email ?? "",
    personal_email: member.personal_email ?? "",
    display_label: member.display_label ?? "",
  }
}

function toRequest(values: MemberFormValues) {
  return {
    client_id: values.client_id.trim(),
    employer_member_id: values.employer_member_id.trim(),
    relation: values.relation,
    primary_employee_member_id:
      values.relation === MemberRelation.EMPLOYEE
        ? null
        : optionalValue(values.primary_employee_member_id),
    coverage_start: optionalValue(values.coverage_start),
    coverage_end: optionalValue(values.coverage_end),
    work_email: optionalValue(values.work_email),
    personal_email: optionalValue(values.personal_email),
    display_label: optionalValue(values.display_label),
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
