import { useState } from "react"

import { z } from "zod"
import { Controller } from "react-hook-form"

import { clientsApi } from "@/api/endpoints/clients"
import { personsApi } from "@/api/endpoints/persons"
import { FormField } from "@/components/common/FormField"
import { FormSection } from "@/components/common/FormSection"
import { SheetForm } from "@/components/common/SheetForm"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import { useDebouncedValue } from "@/hooks/useDebouncedValue"
import { useEntityFormSheet } from "@/hooks/useEntityFormSheet"
import { useEntityList } from "@/lib/queries"
import type { Client, Person } from "@/types/entities"
import { ContactMethod, PersonType, type RelationType, WorkStatus } from "@/types/enums"

const PERSON_TYPE_VALUES = [
  PersonType.CLIENT_EMPLOYEE,
  PersonType.DEPENDENT,
  PersonType.SERVICE_PROVIDER,
  PersonType.PLATFORM_STAFF,
] as const

const PERSON_TYPE_LABELS: Record<PersonType, string> = {
  [PersonType.CLIENT_EMPLOYEE]: "Client employee",
  [PersonType.DEPENDENT]: "Dependent",
  [PersonType.SERVICE_PROVIDER]: "Service provider",
  [PersonType.PLATFORM_STAFF]: "Platform staff",
}

const WORK_STATUS_VALUES = [
  WorkStatus.ACTIVE,
  WorkStatus.INACTIVE,
  WorkStatus.ON_LEAVE,
  WorkStatus.SUSPENDED,
  WorkStatus.RESIGNED,
  WorkStatus.TERMINATED,
] as const

const RELATION_VALUES: ReadonlyArray<RelationType> = [
  "Child",
  "Spouse",
  "Parent",
  "Sibling",
  "Grandparent",
  "Guardian",
  "Other",
]

const CONTACT_METHOD_VALUES = [
  ContactMethod.EMAIL,
  ContactMethod.PHONE,
  ContactMethod.SMS,
  ContactMethod.WHATSAPP,
  ContactMethod.WECHAT,
] as const

const personSchema = z
  .object({
    first_name: z.string().trim().min(1, "First name is required"),
    last_name: z.string().trim().min(1, "Last name is required"),
    middle_name: z.string().optional(),
    person_type: z.enum([
      PersonType.CLIENT_EMPLOYEE,
      PersonType.DEPENDENT,
      PersonType.SERVICE_PROVIDER,
      PersonType.PLATFORM_STAFF,
    ]),
    date_of_birth: z.string().optional(),
    gender: z.string().optional(),
    client_id: z.string().optional(),
    email: z
      .string()
      .trim()
      .optional()
      .refine((v) => !v || /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(v), "Invalid email"),
    phone: z.string().optional(),
    mobile: z.string().optional(),
    preferred_method: z.string().optional(),
    address_street: z.string().optional(),
    address_city: z.string().optional(),
    address_country: z.string().optional(),
    employee_code: z.string().optional(),
    department: z.string().optional(),
    role: z.string().optional(),
    employment_start: z.string().optional(),
    work_status: z.string().optional(),
    primary_employee_id: z.string().optional(),
    relationship: z.string().optional(),
    emergency_name: z.string().optional(),
    emergency_phone: z.string().optional(),
    emergency_email: z
      .string()
      .trim()
      .optional()
      .refine((v) => !v || /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(v), "Invalid email"),
  })
  .refine(
    (d) => d.person_type !== PersonType.CLIENT_EMPLOYEE || Boolean(d.client_id),
    { path: ["client_id"], message: "Client is required for employees" },
  )
  .refine(
    (d) => d.person_type !== PersonType.DEPENDENT || Boolean(d.primary_employee_id),
    {
      path: ["primary_employee_id"],
      message: "Primary employee is required for dependents",
    },
  )
  .refine(
    (d) => d.person_type !== PersonType.DEPENDENT || Boolean(d.relationship),
    { path: ["relationship"], message: "Relationship is required" },
  )

type PersonFormValues = z.infer<typeof personSchema>

const EMPTY: PersonFormValues = {
  first_name: "",
  last_name: "",
  middle_name: "",
  person_type: PersonType.CLIENT_EMPLOYEE,
  date_of_birth: "",
  gender: "",
  client_id: "",
  email: "",
  phone: "",
  mobile: "",
  preferred_method: "",
  address_street: "",
  address_city: "",
  address_country: "",
  employee_code: "",
  department: "",
  role: "",
  employment_start: "",
  work_status: "",
  primary_employee_id: "",
  relationship: "",
  emergency_name: "",
  emergency_phone: "",
  emergency_email: "",
}

interface PersonFormSheetProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  /** Pass a person to edit; omit/null to create a new one. */
  person?: Person | null
  /** When set, locks the client and prefills it (e.g. launched from client detail). */
  clientId?: string
  /** Pre-resolved client used for the locked summary. */
  client?: Client | null
  /** Restrict the type picker to a fixed value (e.g. force ClientEmployee from client detail). */
  lockType?: PersonType
  onSaved?: (person: Person) => void
}

export function PersonFormSheet({
  open,
  onOpenChange,
  person,
  clientId,
  client,
  lockType,
  onSaved,
}: PersonFormSheetProps) {
  const lockedClientId = clientId ?? person?.client_id

  const initialValues: PersonFormValues = person
    ? personToValues(person)
    : { ...EMPTY, client_id: clientId ?? "", person_type: lockType ?? EMPTY.person_type }

  const { register, control, formState, submit, serverError, setValue, watch, isEdit } =
    useEntityFormSheet<
      PersonFormValues,
      Parameters<typeof personsApi.create>[0],
      Person,
      Person
    >({
      resource: "persons",
      schema: personSchema,
      defaultValues: initialValues,
      open,
      onOpenChange,
      entity: person,
      toFormValues: personToValues,
      parsePayload: (values) => ({
        first_name: values.first_name,
        last_name: values.last_name,
        middle_name: values.middle_name?.trim() || undefined,
        person_type: values.person_type as PersonType,
        date_of_birth: values.date_of_birth || undefined,
        gender: values.gender?.trim() || undefined,
        client_id:
          values.person_type === PersonType.CLIENT_EMPLOYEE ||
          values.person_type === PersonType.DEPENDENT
            ? values.client_id || undefined
            : undefined,
        contact_info: hasContact(values)
          ? {
              email: values.email || null,
              phone: values.phone || null,
              mobile: values.mobile || null,
              preferred_method: values.preferred_method || null,
            }
          : undefined,
        address: hasAddress(values)
          ? {
              street: values.address_street || null,
              city: values.address_city || null,
              country: values.address_country || null,
            }
          : undefined,
        employment_info:
          values.person_type === PersonType.CLIENT_EMPLOYEE && hasEmployment(values)
            ? {
                client_id: values.client_id || null,
                employee_code: values.employee_code || null,
                department: values.department || null,
                role: values.role || null,
                start_date: values.employment_start || null,
                status: values.work_status ? (values.work_status as WorkStatus) : null,
              }
            : undefined,
        dependent_info:
          values.person_type === PersonType.DEPENDENT &&
          values.primary_employee_id &&
          values.relationship
            ? {
                primary_employee_id: values.primary_employee_id,
                relationship: values.relationship as RelationType,
              }
            : undefined,
        emergency_contact: hasEmergency(values)
          ? {
              name: values.emergency_name || null,
              phone: values.emergency_phone || null,
              email: values.emergency_email || null,
            }
          : undefined,
      }),
      save: ({ payload, entity, isEdit }) =>
        isEdit && entity ? personsApi.update(entity.id, payload) : personsApi.create(payload),
      successToast: { create: "Person created", update: "Person updated" },
      extraInvalidations: lockedClientId
        ? [{ queryKey: ["clients", "detail", lockedClientId] }]
        : undefined,
      onSaved,
    })

  const watchedType = watch("person_type")
  const watchedClientId = watch("client_id")
  const watchedPrimaryEmployee = watch("primary_employee_id")

  const errors = formState.errors
  const showClient =
    watchedType === PersonType.CLIENT_EMPLOYEE || watchedType === PersonType.DEPENDENT
  const showEmployment = watchedType === PersonType.CLIENT_EMPLOYEE
  const showDependent = watchedType === PersonType.DEPENDENT

  return (
    <SheetForm
      open={open}
      onOpenChange={onOpenChange}
      title={isEdit ? "Edit person" : "Add person"}
      description={
        isEdit
          ? "Update identity, employment, and contact details."
          : "Register an employee, dependent, service provider, or platform staff member."
      }
      size="lg"
      onSubmit={submit}
      isSubmitting={formState.isSubmitting}
      serverError={serverError}
      submitLabel={isEdit ? "Save changes" : "Create person"}
      submittingLabel={isEdit ? "Saving…" : "Creating…"}
    >
      <FormSection title="Identity">
        <div className="grid grid-cols-2 gap-3">
          <FormField
            label="First name"
            required
            error={errors.first_name?.message}
            htmlFor="ps-first"
          >
            <Input id="ps-first" placeholder="Ada" {...register("first_name")} />
          </FormField>
          <FormField
            label="Last name"
            required
            error={errors.last_name?.message}
            htmlFor="ps-last"
          >
            <Input id="ps-last" placeholder="Lovelace" {...register("last_name")} />
          </FormField>
        </div>
        <div className="grid grid-cols-2 gap-3">
          <FormField
            label="Middle name"
            optional
            error={errors.middle_name?.message}
            htmlFor="ps-middle"
          >
            <Input id="ps-middle" {...register("middle_name")} />
          </FormField>
          <FormField
            label="Date of birth"
            optional
            error={errors.date_of_birth?.message}
            htmlFor="ps-dob"
          >
            <Input id="ps-dob" type="date" {...register("date_of_birth")} />
          </FormField>
        </div>
        <FormField
          label="Gender"
          optional
          error={errors.gender?.message}
          htmlFor="ps-gender"
        >
          <Input id="ps-gender" placeholder="e.g. female / male / non-binary" {...register("gender")} />
        </FormField>
      </FormSection>

      <FormSection title="Role">
        <FormField
          label="Person type"
          required
          error={errors.person_type?.message}
          htmlFor="ps-type"
          description={
            lockType
              ? "Locked to this role for the current context."
              : "Determines which sections are required below."
          }
        >
          <Controller
            control={control}
            name="person_type"
            render={({ field }) => (
              <Select
                value={field.value}
                onValueChange={field.onChange}
                disabled={Boolean(lockType)}
              >
                <SelectTrigger id="ps-type">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {PERSON_TYPE_VALUES.map((t) => (
                    <SelectItem key={t} value={t}>
                      {PERSON_TYPE_LABELS[t]}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            )}
          />
        </FormField>
      </FormSection>

      {showClient ? (
        <FormSection title="Client">
          {lockedClientId ? (
            <LockedClientSummary clientId={lockedClientId} client={client ?? null} />
          ) : (
            <FormField
              label="Client"
              required
              error={errors.client_id?.message}
              description="Which corporate client this person belongs to."
            >
              <ClientPicker
                value={watchedClientId ?? ""}
                onChange={(id) =>
                  setValue("client_id", id, { shouldValidate: true, shouldDirty: true })
                }
              />
            </FormField>
          )}
          <input type="hidden" {...register("client_id")} />
        </FormSection>
      ) : null}

      {showEmployment ? (
        <FormSection
          title="Employment"
          description="Optional but recommended — used by reports and assignments."
        >
          <div className="grid grid-cols-2 gap-3">
            <FormField
              label="Employee code"
              optional
              error={errors.employee_code?.message}
              htmlFor="ps-empcode"
            >
              <Input
                id="ps-empcode"
                placeholder="MNT-014"
                className="font-mono"
                {...register("employee_code")}
              />
            </FormField>
            <FormField
              label="Department"
              optional
              error={errors.department?.message}
              htmlFor="ps-dept"
            >
              <Input id="ps-dept" placeholder="People Ops" {...register("department")} />
            </FormField>
          </div>
          <div className="grid grid-cols-2 gap-3">
            <FormField label="Role" optional error={errors.role?.message} htmlFor="ps-role">
              <Input id="ps-role" placeholder="Engineer" {...register("role")} />
            </FormField>
            <FormField
              label="Start date"
              optional
              error={errors.employment_start?.message}
              htmlFor="ps-empstart"
            >
              <Input id="ps-empstart" type="date" {...register("employment_start")} />
            </FormField>
          </div>
          <FormField
            label="Work status"
            optional
            error={errors.work_status?.message}
            htmlFor="ps-workstatus"
          >
            <Controller
              control={control}
              name="work_status"
              render={({ field }) => (
                <Select value={field.value ?? ""} onValueChange={field.onChange}>
                  <SelectTrigger id="ps-workstatus">
                    <SelectValue placeholder="Unset" />
                  </SelectTrigger>
                  <SelectContent>
                    {WORK_STATUS_VALUES.map((w) => (
                      <SelectItem key={w} value={w}>
                        {w}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              )}
            />
          </FormField>
        </FormSection>
      ) : null}

      {showDependent ? (
        <FormSection
          title="Dependent"
          description="Link this dependent to a primary employee."
        >
          <FormField
            label="Primary employee"
            required
            error={errors.primary_employee_id?.message}
            description="The employee this dependent is associated with."
          >
            <PrimaryEmployeePicker
              clientId={watchedClientId || lockedClientId || undefined}
              value={watchedPrimaryEmployee ?? ""}
              onChange={(id) =>
                setValue("primary_employee_id", id, {
                  shouldValidate: true,
                  shouldDirty: true,
                })
              }
            />
          </FormField>
          <input type="hidden" {...register("primary_employee_id")} />
          <FormField
            label="Relationship"
            required
            error={errors.relationship?.message}
            htmlFor="ps-relationship"
          >
            <Controller
              control={control}
              name="relationship"
              render={({ field }) => (
                <Select value={field.value ?? ""} onValueChange={field.onChange}>
                  <SelectTrigger id="ps-relationship">
                    <SelectValue placeholder="Select…" />
                  </SelectTrigger>
                  <SelectContent>
                    {RELATION_VALUES.map((r) => (
                      <SelectItem key={r} value={r}>
                        {r}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              )}
            />
          </FormField>
        </FormSection>
      ) : null}

      <FormSection title="Contact" description="Used for notifications and outreach.">
        <div className="grid grid-cols-2 gap-3">
          <FormField label="Email" optional error={errors.email?.message} htmlFor="ps-email">
            <Input
              id="ps-email"
              type="email"
              placeholder="ada@example.com"
              {...register("email")}
            />
          </FormField>
          <FormField
            label="Preferred method"
            optional
            error={errors.preferred_method?.message}
            htmlFor="ps-prefmethod"
          >
            <Controller
              control={control}
              name="preferred_method"
              render={({ field }) => (
                <Select value={field.value ?? ""} onValueChange={field.onChange}>
                  <SelectTrigger id="ps-prefmethod">
                    <SelectValue placeholder="Unset" />
                  </SelectTrigger>
                  <SelectContent>
                    {CONTACT_METHOD_VALUES.map((m) => (
                      <SelectItem key={m} value={m}>
                        {m}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              )}
            />
          </FormField>
        </div>
        <div className="grid grid-cols-2 gap-3">
          <FormField label="Phone" optional error={errors.phone?.message} htmlFor="ps-phone">
            <Input id="ps-phone" type="tel" {...register("phone")} />
          </FormField>
          <FormField label="Mobile" optional error={errors.mobile?.message} htmlFor="ps-mobile">
            <Input id="ps-mobile" type="tel" {...register("mobile")} />
          </FormField>
        </div>
      </FormSection>

      <FormSection title="Address" description="Optional. Used for in-person visits and shipping.">
        <FormField
          label="Street"
          optional
          error={errors.address_street?.message}
          htmlFor="ps-street"
        >
          <Input id="ps-street" {...register("address_street")} />
        </FormField>
        <div className="grid grid-cols-2 gap-3">
          <FormField
            label="City"
            optional
            error={errors.address_city?.message}
            htmlFor="ps-city"
          >
            <Input id="ps-city" {...register("address_city")} />
          </FormField>
          <FormField
            label="Country"
            optional
            error={errors.address_country?.message}
            htmlFor="ps-country"
          >
            <Input id="ps-country" placeholder="Uganda" {...register("address_country")} />
          </FormField>
        </div>
      </FormSection>

      <FormSection
        title="Emergency contact"
        description="Optional. Recommended for employees and dependents."
      >
        <FormField
          label="Name"
          optional
          error={errors.emergency_name?.message}
          htmlFor="ps-ename"
        >
          <Input id="ps-ename" {...register("emergency_name")} />
        </FormField>
        <div className="grid grid-cols-2 gap-3">
          <FormField
            label="Phone"
            optional
            error={errors.emergency_phone?.message}
            htmlFor="ps-ephone"
          >
            <Input id="ps-ephone" type="tel" {...register("emergency_phone")} />
          </FormField>
          <FormField
            label="Email"
            optional
            error={errors.emergency_email?.message}
            htmlFor="ps-eemail"
          >
            <Input
              id="ps-eemail"
              type="email"
              {...register("emergency_email")}
            />
          </FormField>
        </div>
      </FormSection>
    </SheetForm>
  )
}

function hasContact(v: PersonFormValues): boolean {
  return Boolean(
    v.email?.trim() ||
      v.phone?.trim() ||
      v.mobile?.trim() ||
      v.preferred_method?.trim(),
  )
}

function hasAddress(v: PersonFormValues): boolean {
  return Boolean(
    v.address_street?.trim() ||
      v.address_city?.trim() ||
      v.address_country?.trim(),
  )
}

function hasEmployment(v: PersonFormValues): boolean {
  return Boolean(
    v.employee_code?.trim() ||
      v.department?.trim() ||
      v.role?.trim() ||
      v.employment_start?.trim() ||
      v.work_status?.trim(),
  )
}

function hasEmergency(v: PersonFormValues): boolean {
  return Boolean(
    v.emergency_name?.trim() ||
      v.emergency_phone?.trim() ||
      v.emergency_email?.trim(),
  )
}

function LockedClientSummary({
  clientId,
  client,
}: {
  clientId: string
  client: Client | null
}) {
  const enabled = !client && Boolean(clientId)
  const detail = useEntityList<Client>({
    resource: "clients",
    params: { page: 1, limit: 1, search: clientId },
    listFn: clientsApi.list,
    enabled,
  })
  const resolved =
    client ?? (detail.data?.items ?? []).find((c) => c.id === clientId) ?? null
  return (
    <div className="flex items-center gap-2.5 rounded-sm border border-fg/15 bg-surface px-3 py-2">
      <span
        aria-hidden
        className="grid size-7 shrink-0 place-items-center bg-primary/10 font-mono text-[10px] font-semibold text-primary"
      >
        {resolved ? clientInitial(resolved.name) : "··"}
      </span>
      <div className="min-w-0 flex-1">
        <p className="truncate text-sm font-medium text-fg">
          {resolved?.name ?? "Selected client"}
        </p>
        <p className="truncate font-mono text-[11px] text-fg/55">
          {resolved?.code ?? clientId}
        </p>
      </div>
      <span className="shrink-0 rounded-sm border border-fg/15 bg-bg px-1.5 py-0.5 text-[10px] font-medium tracking-wide text-fg/55">
        Locked
      </span>
    </div>
  )
}

function ClientPicker({
  value,
  onChange,
}: {
  value: string
  onChange: (clientId: string) => void
}) {
  const [query, setQuery] = useState("")
  const debounced = useDebouncedValue(query.trim(), 250)
  const list = useEntityList<Client>({
    resource: "clients",
    params: { page: 1, limit: 8, search: debounced || undefined },
    listFn: clientsApi.list,
  })
  const items = list.data?.items ?? []
  const selected = items.find((c) => c.id === value)

  if (selected) {
    return (
      <div className="flex items-center gap-2.5 rounded-sm border border-fg/15 bg-surface px-3 py-2">
        <span
          aria-hidden
          className="grid size-7 shrink-0 place-items-center bg-primary/10 font-mono text-[10px] font-semibold text-primary"
        >
          {clientInitial(selected.name)}
        </span>
        <div className="min-w-0 flex-1">
          <p className="truncate text-sm font-medium text-fg">{selected.name}</p>
          <p className="truncate font-mono text-[11px] text-fg/55">{selected.code}</p>
        </div>
        <Button
          type="button"
          variant="ghost"
          size="sm"
          onClick={() => onChange("")}
          className="shrink-0 text-xs text-fg/65"
        >
          Change
        </Button>
      </div>
    )
  }

  return (
    <div className="space-y-1.5">
      <Input
        placeholder="Search clients by name or code…"
        value={query}
        onChange={(e) => setQuery(e.target.value)}
      />
      <div className="max-h-48 overflow-y-auto rounded-sm border border-fg/15 bg-bg">
        {list.isPending ? (
          <p className="px-3 py-2 text-xs text-fg/55">Loading…</p>
        ) : items.length === 0 ? (
          <p className="px-3 py-2 text-xs text-fg/55">
            {debounced ? "No clients match." : "Start typing to search clients."}
          </p>
        ) : (
          <ul className="divide-y divide-fg/8">
            {items.map((c) => (
              <li key={c.id}>
                <Button
                  type="button"
                  variant="ghost"
                  onClick={() => onChange(c.id)}
                  className="flex h-auto w-full items-center gap-2.5 px-3 py-2 text-left"
                >
                  <span
                    aria-hidden
                    className="grid size-6 shrink-0 place-items-center bg-primary/10 font-mono text-[10px] font-semibold text-primary"
                  >
                    {clientInitial(c.name)}
                  </span>
                  <span className="min-w-0 flex-1">
                    <span className="block truncate text-sm font-medium text-fg">
                      {c.name}
                    </span>
                    <span className="block truncate font-mono text-[11px] text-fg/55">
                      {c.code}
                    </span>
                  </span>
                </Button>
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  )
}

function PrimaryEmployeePicker({
  clientId,
  value,
  onChange,
}: {
  clientId?: string
  value: string
  onChange: (id: string) => void
}) {
  const [query, setQuery] = useState("")
  const debounced = useDebouncedValue(query.trim(), 250)
  const list = useEntityList<Person>({
    resource: "persons",
    params: {
      page: 1,
      limit: 8,
      search: debounced || undefined,
      ...(clientId ? ({ client_id: clientId } as Record<string, unknown>) : {}),
      ...({ person_type: PersonType.CLIENT_EMPLOYEE } as Record<string, unknown>),
    },
    listFn: personsApi.list,
    enabled: Boolean(clientId),
  })
  const items = (list.data?.items ?? []).filter(
    (p) => p.person_type === PersonType.CLIENT_EMPLOYEE,
  )
  const selected = items.find((p) => p.id === value)

  if (!clientId) {
    return (
      <p className="rounded-sm border border-dashed border-fg/15 bg-bg px-3 py-2 text-xs text-fg/55">
        Select a client first to choose a primary employee.
      </p>
    )
  }

  if (selected) {
    return (
      <div className="flex items-center gap-2.5 rounded-sm border border-fg/15 bg-surface px-3 py-2">
        <span
          aria-hidden
          className="grid size-7 shrink-0 place-items-center bg-primary/10 font-mono text-[10px] font-semibold text-primary"
        >
          {personInitial(selected)}
        </span>
        <div className="min-w-0 flex-1">
          <p className="truncate text-sm font-medium text-fg">
            {selected.first_name} {selected.last_name}
          </p>
          <p className="truncate font-mono text-[11px] text-fg/55">
            {selected.employment_info?.employee_code ?? selected.id.slice(0, 8)}
          </p>
        </div>
        <Button
          type="button"
          variant="ghost"
          size="sm"
          onClick={() => onChange("")}
          className="shrink-0 text-xs text-fg/65"
        >
          Change
        </Button>
      </div>
    )
  }

  return (
    <div className="space-y-1.5">
      <Input
        placeholder="Search employees…"
        value={query}
        onChange={(e) => setQuery(e.target.value)}
      />
      <div className="max-h-48 overflow-y-auto rounded-sm border border-fg/15 bg-bg">
        {list.isPending ? (
          <p className="px-3 py-2 text-xs text-fg/55">Loading…</p>
        ) : items.length === 0 ? (
          <p className="px-3 py-2 text-xs text-fg/55">
            {debounced ? "No employees match." : "Start typing to search employees."}
          </p>
        ) : (
          <ul className="divide-y divide-fg/8">
            {items.map((p) => (
              <li key={p.id}>
                <Button
                  type="button"
                  variant="ghost"
                  onClick={() => onChange(p.id)}
                  className="flex h-auto w-full items-center gap-2.5 px-3 py-2 text-left"
                >
                  <span
                    aria-hidden
                    className="grid size-6 shrink-0 place-items-center bg-primary/10 font-mono text-[10px] font-semibold text-primary"
                  >
                    {personInitial(p)}
                  </span>
                  <span className="min-w-0 flex-1">
                    <span className="block truncate text-sm font-medium text-fg">
                      {p.first_name} {p.last_name}
                    </span>
                    <span className="block truncate font-mono text-[11px] text-fg/55">
                      {p.employment_info?.employee_code ?? p.id.slice(0, 8)}
                    </span>
                  </span>
                </Button>
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  )
}

function clientInitial(name: string): string {
  const trimmed = name.trim()
  if (!trimmed) return "·"
  const parts = trimmed.split(/\s+/)
  if (parts.length >= 2) return (parts[0][0] + parts[1][0]).toUpperCase()
  return trimmed.slice(0, 2).toUpperCase()
}

function personInitial(p: Person): string {
  const f = p.first_name?.[0] ?? ""
  const l = p.last_name?.[0] ?? ""
  return (f + l).toUpperCase() || "·"
}

function personToValues(person: Person): PersonFormValues {
  return {
    first_name: person.first_name,
    last_name: person.last_name,
    middle_name: person.middle_name ?? "",
    person_type: person.person_type,
    date_of_birth: person.date_of_birth ?? "",
    gender: person.gender ?? "",
    client_id: person.client_id ?? "",
    email: person.contact_info?.email ?? "",
    phone: person.contact_info?.phone ?? "",
    mobile: person.contact_info?.mobile ?? "",
    preferred_method: person.contact_info?.preferred_method ?? "",
    address_street: person.address?.street ?? "",
    address_city: person.address?.city ?? "",
    address_country: person.address?.country ?? "",
    employee_code: person.employment_info?.employee_code ?? "",
    department: person.employment_info?.department ?? "",
    role: person.employment_info?.role ?? "",
    employment_start: person.employment_info?.start_date ?? "",
    work_status: person.employment_info?.status ?? "",
    primary_employee_id: person.dependent_info?.primary_employee_id ?? "",
    relationship: person.dependent_info?.relationship ?? "",
    emergency_name: person.emergency_contact?.name ?? "",
    emergency_phone: person.emergency_contact?.phone ?? "",
    emergency_email: person.emergency_contact?.email ?? "",
  }
}

export { PERSON_TYPE_LABELS }
