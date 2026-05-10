/**
 * Person create / edit sheet. **BE-canonical 2-step flow.**
 *
 * Create:
 *   1. POST /users   → returns user_id
 *   2. POST /persons → with {person_type, user_id, tenant_id, employment_info? | dependent_info?, family_id?}
 *
 * Edit (mirrors the BE PATCH surface):
 *   - CLIENT_EMPLOYEE → PATCH /persons/{id}/employment-info
 *   - DEPENDENT       → PATCH /persons/{id}/dependent-info
 *
 * Demographic fields (first/last name, dob, gender, contact info, address)
 * are NOT collected — BE doesn't carry them. Display is derived via
 * `displayName(person, user)` from the linked User's email.
 */

import { useState } from "react"

import { Controller } from "react-hook-form"
import { z } from "zod"

import { clientsApi } from "@/api/endpoints/clients"
import { personsApi } from "@/api/endpoints/persons"
import { usersApi } from "@/api/endpoints/users"
import type { EmploymentInfoCreateSchema } from "@/api/generated"
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
import { useTenantStore } from "@/store/slices/tenantSlice"
import type { Client, Person } from "@/types/entities"
import { PersonType, type RelationType, WorkStatus } from "@/types/enums"

const PERSON_TYPE_VALUES = [PersonType.CLIENT_EMPLOYEE, PersonType.DEPENDENT] as const

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

const personSchema = z
  .object({
    email: z.email("Invalid email"),
    password: z
      .string()
      .optional()
      .refine((v) => !v || v.length >= 8, "Min 8 characters"),
    person_type: z.enum([PersonType.CLIENT_EMPLOYEE, PersonType.DEPENDENT]),
    family_id: z.string().optional(),
    client_id: z.string().optional(),
    role: z.string().optional(),
    department: z.string().optional(),
    employee_id: z.string().optional(),
    /** Optional per UX. Defaulted to today's date on submit if blank. */
    employment_start: z.string().optional(),
    employment_end: z.string().optional(),
    work_status: z.string().optional(),
    primary_employee_id: z.string().optional(),
    relationship: z.string().optional(),
    guardian_id: z.string().optional(),
  })
  .superRefine((d, ctx) => {
    if (d.person_type === PersonType.CLIENT_EMPLOYEE) {
      if (!d.client_id?.trim())
        ctx.addIssue({ code: "custom", path: ["client_id"], message: "Required" })
      if (!d.role?.trim())
        ctx.addIssue({ code: "custom", path: ["role"], message: "Required" })
    }
    if (d.person_type === PersonType.DEPENDENT) {
      if (!d.primary_employee_id?.trim())
        ctx.addIssue({ code: "custom", path: ["primary_employee_id"], message: "Required" })
      if (!d.relationship?.trim())
        ctx.addIssue({ code: "custom", path: ["relationship"], message: "Required" })
    }
  })

type PersonFormValues = z.infer<typeof personSchema>

const EMPTY: PersonFormValues = {
  email: "",
  password: "",
  person_type: PersonType.CLIENT_EMPLOYEE,
  family_id: "",
  client_id: "",
  role: "",
  department: "",
  employee_id: "",
  employment_start: "",
  employment_end: "",
  work_status: "",
  primary_employee_id: "",
  relationship: "",
  guardian_id: "",
}

interface PersonFormSheetProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  /** Pass a person to edit; omit/null to create. */
  person?: Person | null
  /** When set, locks the client picker (e.g. launched from client detail). */
  clientId?: string
  /** Pre-resolved client used for the locked summary. */
  client?: Client | null
  /** Restrict the type picker to a fixed value. */
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
  const tenantId = useTenantStore((s) => s.currentTenantId)
  const lockedClientId = clientId ?? person?.employment_info?.client_id ?? person?.client_id

  // For create: build a fresh form with defaults. For edit: hydrate from the
  // existing employment_info / dependent_info — email/password aren't editable
  // here (those go through the dedicated user routes).
  const initialValues: PersonFormValues = person
    ? personToValues(person)
    : {
        ...EMPTY,
        client_id: clientId ?? "",
        person_type: lockType && lockType !== PersonType.CLIENT_EMPLOYEE && lockType !== PersonType.DEPENDENT
          ? PersonType.CLIENT_EMPLOYEE
          : (lockType ?? EMPTY.person_type),
      }

  const { register, control, formState, submit, serverError, setValue, watch, isEdit } =
    useEntityFormSheet<PersonFormValues, PersonFormValues, Person, Person>({
      resource: "persons",
      schema: personSchema,
      defaultValues: initialValues,
      open,
      onOpenChange,
      entity: person,
      toFormValues: personToValues,
      // Carry the validated form values through unchanged; the save handler
      // does the BE-shape mapping (and the 2-step user-then-person call).
      parsePayload: (values) => values,
      save: async ({ payload, entity, isEdit }) => {
        if (isEdit && entity) {
          // BE has no top-level Person update; route to the sub-PATCH that
          // matches the role of the existing person.
          if (entity.person_type === PersonType.CLIENT_EMPLOYEE) {
            const employmentInfo = buildEmploymentInfo(payload, entity.user_id)
            return personsApi.updateEmploymentInfo(entity.id, employmentInfo)
          }
          if (entity.person_type === PersonType.DEPENDENT) {
            return personsApi.updateDependentInfo(entity.id, {
              primary_employee_id: payload.primary_employee_id ?? "",
              relationship: payload.relationship as RelationType,
              ...(payload.guardian_id ? { guardian_id: payload.guardian_id } : {}),
            })
          }
          // Other person types aren't editable through this sheet today.
          return entity
        }

        // 2-step create.
        if (!tenantId) {
          throw new Error("No active tenant — sign in first.")
        }
        const user = await usersApi.create({
          email: payload.email,
          ...(payload.password ? { password: payload.password } : {}),
        })

        const personType = payload.person_type as PersonType
        return personsApi.create({
          person_type: personType,
          user_id: user.id,
          tenant_id: tenantId,
          ...(payload.family_id ? { family_id: payload.family_id } : {}),
          ...(personType === PersonType.CLIENT_EMPLOYEE
            ? { employment_info: buildEmploymentInfo(payload, user.id) }
            : {}),
          ...(personType === PersonType.DEPENDENT
            ? {
                dependent_info: {
                  primary_employee_id: payload.primary_employee_id ?? "",
                  relationship: payload.relationship as RelationType,
                  ...(payload.guardian_id ? { guardian_id: payload.guardian_id } : {}),
                },
              }
            : {}),
        })
      },
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
  const showEmployment = watchedType === PersonType.CLIENT_EMPLOYEE
  const showDependent = watchedType === PersonType.DEPENDENT

  return (
    <SheetForm
      open={open}
      onOpenChange={onOpenChange}
      title={isEdit ? "Edit person" : "Add person"}
      size="lg"
      onSubmit={submit}
      isSubmitting={formState.isSubmitting}
      serverError={serverError}
      submitLabel={isEdit ? "Save" : "Create"}
      submittingLabel={isEdit ? "Saving…" : "Creating…"}
    >
      {!isEdit ? (
        <FormSection title="Account">
          <div className="grid grid-cols-2 gap-3">
            <FormField label="Email" required error={errors.email?.message} htmlFor="ps-email">
              <Input id="ps-email" type="email" placeholder="ada@acme.com" {...register("email")} />
            </FormField>
            <FormField label="Password" optional error={errors.password?.message} htmlFor="ps-password">
              <Input
                id="ps-password"
                type="password"
                autoComplete="new-password"
                placeholder="Optional"
                {...register("password")}
              />
            </FormField>
          </div>
        </FormSection>
      ) : null}

      <FormSection title="Role">
        <FormField label="Type" required error={errors.person_type?.message} htmlFor="ps-type">
          <Controller
            control={control}
            name="person_type"
            render={({ field }) => (
              <Select
                value={field.value}
                onValueChange={field.onChange}
                disabled={Boolean(lockType) || isEdit}
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

      {showEmployment ? (
        <FormSection title="Employment">
          {lockedClientId ? (
            <LockedClientSummary clientId={lockedClientId} client={client ?? null} />
          ) : (
            <FormField label="Client" required error={errors.client_id?.message}>
              <ClientPicker
                value={watchedClientId ?? ""}
                onChange={(id) =>
                  setValue("client_id", id, { shouldValidate: true, shouldDirty: true })
                }
              />
            </FormField>
          )}
          <Input type="hidden" {...register("client_id")} />
          <div className="grid grid-cols-2 gap-3">
            <FormField label="Role" required error={errors.role?.message} htmlFor="ps-role">
              <Input id="ps-role" placeholder="Counsellor" {...register("role")} />
            </FormField>
            <FormField label="Department" optional error={errors.department?.message} htmlFor="ps-dept">
              <Input id="ps-dept" placeholder="People Ops" {...register("department")} />
            </FormField>
          </div>
          <div className="grid grid-cols-2 gap-3">
            <FormField label="Employee ID" optional error={errors.employee_id?.message} htmlFor="ps-empid">
              <Input
                id="ps-empid"
                placeholder="MNT-014"
                className="font-mono"
                {...register("employee_id")}
              />
            </FormField>
            <FormField label="Family ID" optional error={errors.family_id?.message} htmlFor="ps-family">
              <Input id="ps-family" className="font-mono" {...register("family_id")} />
            </FormField>
          </div>
          <div className="grid grid-cols-2 gap-3">
            <FormField label="Start date" optional error={errors.employment_start?.message} htmlFor="ps-empstart">
              <Input id="ps-empstart" type="date" {...register("employment_start")} />
            </FormField>
            <FormField label="End date" optional error={errors.employment_end?.message} htmlFor="ps-empend">
              <Input id="ps-empend" type="date" {...register("employment_end")} />
            </FormField>
          </div>
          {isEdit ? (
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
                      <SelectValue placeholder="—" />
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
          ) : null}
        </FormSection>
      ) : null}

      {showDependent ? (
        <FormSection title="Dependent">
          <FormField label="Primary employee" required error={errors.primary_employee_id?.message}>
            <PrimaryEmployeePicker
              value={watchedPrimaryEmployee ?? ""}
              onChange={(id) =>
                setValue("primary_employee_id", id, { shouldValidate: true, shouldDirty: true })
              }
            />
          </FormField>
          <Input type="hidden" {...register("primary_employee_id")} />
          <div className="grid grid-cols-2 gap-3">
            <FormField label="Relationship" required error={errors.relationship?.message} htmlFor="ps-relationship">
              <Controller
                control={control}
                name="relationship"
                render={({ field }) => (
                  <Select value={field.value ?? ""} onValueChange={field.onChange}>
                    <SelectTrigger id="ps-relationship">
                      <SelectValue placeholder="—" />
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
            <FormField label="Guardian user ID" optional error={errors.guardian_id?.message} htmlFor="ps-guardian">
              <Input id="ps-guardian" className="font-mono" {...register("guardian_id")} />
            </FormField>
          </div>
        </FormSection>
      ) : null}
    </SheetForm>
  )
}

function buildEmploymentInfo(
  values: PersonFormValues,
  _userId: string,
): EmploymentInfoCreateSchema {
  // BE requires `start_date` and `status` on employment_info. The UX leaves
  // start_date optional ("we don't ask when they joined"); default to today.
  const today = new Date().toISOString().slice(0, 10)
  return {
    client_id: values.client_id ?? "",
    role: values.role ?? "",
    start_date: values.employment_start?.trim() || today,
    status: (values.work_status as WorkStatus) || WorkStatus.ACTIVE,
    ...(values.department ? { department: values.department } : {}),
    ...(values.employee_id ? { employee_id: values.employee_id } : {}),
    ...(values.employment_end ? { end_date: values.employment_end } : {}),
  }
}

function personToValues(person: Person): PersonFormValues {
  return {
    email: "", // not editable here; would come from linked User
    password: "",
    person_type:
      person.person_type === PersonType.CLIENT_EMPLOYEE ||
      person.person_type === PersonType.DEPENDENT
        ? person.person_type
        : PersonType.CLIENT_EMPLOYEE,
    family_id: person.family_id ?? "",
    client_id: person.employment_info?.client_id ?? person.client_id ?? "",
    role: person.employment_info?.role ?? "",
    department: person.employment_info?.department ?? "",
    employee_id:
      (person.employment_info as { employee_id?: string | null } | undefined)?.employee_id ?? "",
    employment_start: person.employment_info?.start_date ?? "",
    employment_end:
      (person.employment_info as { end_date?: string | null } | undefined)?.end_date ?? "",
    work_status: person.employment_info?.status ?? "",
    primary_employee_id: person.dependent_info?.primary_employee_id ?? "",
    relationship: person.dependent_info?.relationship ?? "",
    guardian_id:
      (person.dependent_info as { guardian_id?: string | null } | undefined)?.guardian_id ?? "",
  }
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
  value,
  onChange,
}: {
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
    } as Record<string, unknown>,
    listFn: personsApi.list,
  })
  const items = (list.data?.items ?? []).filter(
    (p) => p.person_type === PersonType.CLIENT_EMPLOYEE,
  )
  const selected = items.find((p) => p.id === value)

  if (selected) {
    return (
      <div className="flex items-center gap-2.5 rounded-sm border border-fg/15 bg-surface px-3 py-2">
        <span
          aria-hidden
          className="grid size-7 shrink-0 place-items-center bg-primary/10 font-mono text-[10px] font-semibold text-primary"
        >
          {employeeShortLabel(selected).slice(0, 2).toUpperCase()}
        </span>
        <div className="min-w-0 flex-1">
          <p className="truncate text-sm font-medium text-fg">{employeeShortLabel(selected)}</p>
          <p className="truncate font-mono text-[11px] text-fg/55">
            {selected.id.slice(0, 8)}
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
        placeholder="Search employees by ID or role…"
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
                    {employeeShortLabel(p).slice(0, 2).toUpperCase()}
                  </span>
                  <span className="min-w-0 flex-1">
                    <span className="block truncate text-sm font-medium text-fg">
                      {employeeShortLabel(p)}
                    </span>
                    <span className="block truncate font-mono text-[11px] text-fg/55">
                      {p.id.slice(0, 8)}
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

function employeeShortLabel(p: Person): string {
  const role = p.employment_info?.role
  const dept = p.employment_info?.department
  if (role && dept) return `${role} · ${dept}`
  if (role) return role
  return p.id.slice(0, 8)
}

export { PERSON_TYPE_LABELS }
