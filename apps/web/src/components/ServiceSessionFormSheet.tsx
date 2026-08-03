
import { Controller } from "react-hook-form"
import { z } from "zod"

import { personsApi } from "@/api/endpoints/persons"
import { providersApi } from "@/api/endpoints/providers"
import { serviceSessionsApi } from "@/api/endpoints/service-sessions"
import { servicesApi } from "@/api/endpoints/services"
import { DiagnosisSelector } from "@/components/common/DiagnosisSelector"
import { EntityPicker, PickerRow } from "@/components/common/EntityPicker"
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
import { displayName, personInitials } from "@/lib/display"
import { useEntityList } from "@/lib/queries"
import type { Person, Provider, Service, ServiceSession } from "@/types/entities"
import { ClientType, SessionCategory, SessionType } from "@/types/enums"

const schema = z
  .object({
    service_id: z.string().trim().min(1, "Service is required"),
    person_id: z.string().trim().min(1, "Person is required"),
    service_provider_id: z.string().optional(),
    scheduled_at: z
      .string()
      .min(1, "Scheduled time is required")
      .refine((s) => !Number.isNaN(Date.parse(s)), "Must be a valid date/time"),
    location: z.string().optional(),
    notes: z.string().optional(),
    category: z.nativeEnum(SessionCategory).optional(),
    session_type: z.nativeEnum(SessionType).optional(),
    client_type: z.nativeEnum(ClientType).optional(),
    headcount: z.string().optional(),
    issue_topic: z.string().optional(),
    partner_name: z.string().optional(),
    partner_relationship: z.string().optional(),
    rate_ugx: z.string().optional(),
    session_number: z.string().optional(),
    diagnosis_id: z.string().nullable().optional(),
    diagnosis_type_id: z.string().nullable().optional(),
    is_backfill: z.boolean().optional(),
    backfill_reason: z.string().optional(),
  })
  .refine(
    (d) => !d.is_backfill || new Date(d.scheduled_at).getTime() <= Date.now(),
    {
      path: ["scheduled_at"],
      message: "Backfilled sessions must be in the past",
    },
  )
  .refine((d) => !d.is_backfill || (d.backfill_reason?.trim().length ?? 0) > 0, {
    path: ["backfill_reason"],
    message: "Reason is required when logging a past session",
  })
  .refine(
    (d) =>
      d.category !== SessionCategory.GROUP ||
      (Number.isFinite(Number(d.headcount)) && Number(d.headcount) >= 2),
    {
      path: ["headcount"],
      message: "Group sessions need a headcount of at least 2",
    },
  )

type Values = z.infer<typeof schema>

const EMPTY: Values = {
  service_id: "",
  person_id: "",
  service_provider_id: "",
  scheduled_at: "",
  location: "",
  notes: "",
  category: undefined,
  session_type: undefined,
  client_type: undefined,
  headcount: "",
  issue_topic: "",
  partner_name: "",
  partner_relationship: "",
  rate_ugx: "",
  session_number: "",
  diagnosis_id: null,
  diagnosis_type_id: null,
  is_backfill: false,
  backfill_reason: "",
}

interface ServiceSessionFormSheetProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  /** Pass a session to edit (sets initial values; otherwise create mode). */
  session?: ServiceSession | null
  /** When set, locks the service picker. */
  serviceId?: string
  /** When set, locks the person picker. */
  personId?: string
  /** Pre-resolved service for the locked summary. */
  service?: Service | null
  /** Pre-resolved person for the locked summary. */
  person?: Person | null
  onSaved?: (session: ServiceSession) => void
}

export function ServiceSessionFormSheet({
  open,
  onOpenChange,
  session,
  serviceId,
  personId,
  service,
  person,
  onSaved,
}: ServiceSessionFormSheetProps) {
  const lockedServiceId = serviceId ?? session?.service_id
  const lockedPersonId = personId ?? session?.person_id

  const { register, control, formState, submit, serverError, setValue, watch, isEdit } =
    useEntityFormSheet<
      Values,
      Parameters<typeof serviceSessionsApi.create>[0] & {
        __isBackfill?: boolean
        __backfillReason?: string | null
        __notes?: string
      },
      ServiceSession,
      ServiceSession
    >({
      resource: "service-sessions",
      schema,
      defaultValues: { ...EMPTY, service_id: serviceId ?? "", person_id: personId ?? "" },
      open,
      onOpenChange,
      entity: session,
      toFormValues,
      // Backfill intent is FE-only: `__isBackfill` translates into a
      // `complete()` call after create; the typed reason becomes the
      // completion note. `notes` is edit-only (create has nowhere to put it).
      parsePayload: (values) => {
        const isBackfill = !session && Boolean(values.is_backfill)
        const num = (v: string | undefined) => {
          const n = Number(v)
          return v?.trim() && Number.isFinite(n) ? n : undefined
        }
        return {
          service_id: values.service_id,
          person_id: values.person_id,
          provider_id: values.service_provider_id || "",
          scheduled_at: new Date(values.scheduled_at).toISOString(),
          location: values.location?.trim() || null,
          category: values.category ?? undefined,
          session_type: values.session_type ?? undefined,
          client_type: values.client_type ?? undefined,
          headcount: num(values.headcount),
          issue_topic: values.issue_topic?.trim() || undefined,
          partner_name: values.partner_name?.trim() || undefined,
          partner_relationship: values.partner_relationship?.trim() || undefined,
          rate_ugx: num(values.rate_ugx),
          session_number: num(values.session_number),
          diagnosis_id: values.diagnosis_id ?? undefined,
          diagnosis_type_id: values.diagnosis_type_id ?? undefined,
          __isBackfill: isBackfill,
          __backfillReason: isBackfill ? (values.backfill_reason?.trim() || null) : null,
          __notes: values.notes?.trim() || undefined,
        }
      },
      save: async ({ payload, entity, isEdit }) => {
        const { __isBackfill, __backfillReason, __notes, ...body } = payload
        if (isEdit && entity) {
          // PATCH takes the clinical/admin fields (+ notes); scheduling is
          // immutable here — reschedule is its own transition on the detail page.
          const {
            service_id: _s,
            person_id: _p,
            provider_id: _pr,
            scheduled_at: _at,
            session_number: _sn,
            ...updatable
          } = body
          return serviceSessionsApi.update(entity.id, { ...updatable, notes: __notes })
        }
        let result = await serviceSessionsApi.create(body)
        if (__isBackfill && result?.id) {
          // A backfilled session is complete by definition. Duration comes
          // from the service's configured length; the reason becomes the note.
          const svc = await servicesApi.getById(body.service_id).catch(() => null)
          result = await serviceSessionsApi.complete(result.id, {
            duration: svc?.duration_minutes ?? 60,
            notes: __backfillReason ?? "Backfilled from manual entry",
          })
        }
        return result
      },
      successToast: { create: "Session created", update: "Session updated" },
      onSaved,
    })

  const watchedService = watch("service_id")
  const watchedPerson = watch("person_id")
  const watchedProvider = watch("service_provider_id")
  const watchedBackfill = !isEdit && Boolean(watch("is_backfill"))
  const watchedCategory = watch("category")
  const isGroup = watchedCategory === SessionCategory.GROUP
  const isPartnered =
    watchedCategory === SessionCategory.COUPLES ||
    watchedCategory === SessionCategory.FAMILY

  const errors = formState.errors

  return (
    <SheetForm
      open={open}
      onOpenChange={onOpenChange}
      title={
        isEdit
          ? "Edit session"
          : watchedBackfill
            ? "Log past session"
            : "Schedule session"
      }
      description={
        isEdit
          ? "Update the time, location, or notes for this session."
          : watchedBackfill
            ? "Record a session that already happened. Marked Completed and tagged in the audit trail."
            : "Schedule a session for a person against a service. Lifecycle changes (complete / cancel / no-show) happen later from the detail view."
      }
      size="lg"
      onSubmit={submit}
      isSubmitting={formState.isSubmitting}
      serverError={serverError}
      submitLabel={
        isEdit
          ? "Save changes"
          : watchedBackfill
            ? "Log session"
            : "Create session"
      }
      submittingLabel={isEdit ? "Saving…" : watchedBackfill ? "Logging…" : "Creating…"}
    >
      <FormSection title="Service">
        <FormField label="Service" required error={errors.service_id?.message}>
          {lockedServiceId ? (
            <LockedServiceSummary serviceId={lockedServiceId} service={service ?? null} />
          ) : (
            <ServicePicker
              value={watchedService ?? ""}
              onChange={(id) =>
                setValue("service_id", id, { shouldValidate: true, shouldDirty: true })
              }
            />
          )}
        </FormField>
        <Input type="hidden" {...register("service_id")} />
        <div className="grid grid-cols-2 gap-3">
          <FormField label="Category" optional error={errors.category?.message}>
            <Controller
              control={control}
              name="category"
              render={({ field }) => (
                <EnumSelect
                  value={field.value}
                  onChange={field.onChange}
                  options={Object.values(SessionCategory)}
                />
              )}
            />
          </FormField>
          <FormField label="Delivery" optional error={errors.session_type?.message}>
            <Controller
              control={control}
              name="session_type"
              render={({ field }) => (
                <EnumSelect
                  value={field.value}
                  onChange={field.onChange}
                  options={Object.values(SessionType)}
                />
              )}
            />
          </FormField>
        </div>
        {isGroup ? (
          <FormField
            label="Headcount"
            required
            description="Number of participants — group sessions need at least 2."
            error={errors.headcount?.message}
            htmlFor="ss-headcount"
          >
            <Input id="ss-headcount" type="number" min={2} {...register("headcount")} />
          </FormField>
        ) : null}
      </FormSection>

      <FormSection title="Subject">
        <FormField label="Person" required error={errors.person_id?.message}>
          {lockedPersonId ? (
            <LockedPersonSummary personId={lockedPersonId} person={person ?? null} />
          ) : (
            <PersonPicker
              value={watchedPerson ?? ""}
              onChange={(id) =>
                setValue("person_id", id, { shouldValidate: true, shouldDirty: true })
              }
            />
          )}
        </FormField>
        <Input type="hidden" {...register("person_id")} />
        <FormField label="Client type" optional error={errors.client_type?.message}>
          <Controller
            control={control}
            name="client_type"
            render={({ field }) => (
              <EnumSelect
                value={field.value}
                onChange={field.onChange}
                options={Object.values(ClientType)}
                placeholder="New or returning?"
              />
            )}
          />
        </FormField>
        {isPartnered ? (
          <div className="grid grid-cols-2 gap-3">
            <FormField
              label="Partner name"
              optional
              error={errors.partner_name?.message}
              htmlFor="ss-partner-name"
            >
              <Input id="ss-partner-name" {...register("partner_name")} />
            </FormField>
            <FormField
              label="Relationship"
              optional
              error={errors.partner_relationship?.message}
              htmlFor="ss-partner-rel"
            >
              <Input
                id="ss-partner-rel"
                placeholder="e.g. Spouse"
                {...register("partner_relationship")}
              />
            </FormField>
          </div>
        ) : null}
      </FormSection>

      <FormSection
        title="Provider"
        description="Optional. The counsellor or clinic delivering the session."
      >
        <FormField label="Provider" optional error={errors.service_provider_id?.message}>
          <ProviderPicker
            value={watchedProvider ?? ""}
            onChange={(id) =>
              setValue("service_provider_id", id, {
                shouldValidate: true,
                shouldDirty: true,
              })
            }
          />
        </FormField>
        <Input type="hidden" {...register("service_provider_id")} />
        <div className="grid grid-cols-2 gap-3">
          <FormField
            label="Rate (UGX)"
            optional
            error={errors.rate_ugx?.message}
            htmlFor="ss-rate"
          >
            <Input id="ss-rate" type="number" min={0} {...register("rate_ugx")} />
          </FormField>
          <FormField
            label="Session number"
            optional
            description="Position in the person's episode, e.g. 3 of 6."
            error={errors.session_number?.message}
            htmlFor="ss-session-no"
          >
            <Input id="ss-session-no" type="number" min={1} {...register("session_number")} />
          </FormField>
        </div>
      </FormSection>

      <FormSection title={watchedBackfill ? "When it happened" : "Schedule"}>
        {!isEdit ? (
          <div className="flex cursor-pointer items-start gap-2 rounded-sm border border-fg/10 bg-surface px-3 py-2.5">
            <Controller
              control={control}
              name="is_backfill"
              render={({ field }) => (
                <Checkbox
                  id="ss-backfill"
                  checked={field.value}
                  onCheckedChange={field.onChange}
                  className="mt-0.5"
                />
              )}
            />
            <label htmlFor="ss-backfill" className="cursor-pointer min-w-0 flex-1">
              <span className="block text-sm font-medium text-fg">
                This session already happened
              </span>
              <span className="block text-xs text-fg/55">
                Backfill a past session. It will be marked Completed and tagged with
                a logged-at timestamp + reason in the audit trail.
              </span>
            </label>
          </div>
        ) : null}
        <FormField
          label={watchedBackfill ? "Occurred at" : "Scheduled at"}
          required
          error={errors.scheduled_at?.message}
          htmlFor="ss-scheduled"
        >
          <Input id="ss-scheduled" type="datetime-local" {...register("scheduled_at")} />
        </FormField>
        {watchedBackfill ? (
          <FormField
            label="Reason for back-entry"
            required
            description="Why is this being logged after the fact? Visible in the audit log."
            error={errors.backfill_reason?.message}
            htmlFor="ss-backfill-reason"
          >
            <Input
              id="ss-backfill-reason"
              placeholder="e.g. Phone session — paper notes, entered next day"
              {...register("backfill_reason")}
            />
          </FormField>
        ) : null}
        <FormField
          label="Location"
          optional
          description="Physical address, video link, or 'Phone'."
          error={errors.location?.message}
          htmlFor="ss-location"
        >
          <Input
            id="ss-location"
            placeholder="e.g. Room 4 / Zoom / Phone"
            {...register("location")}
          />
        </FormField>
      </FormSection>

      <FormSection title="Clinical">
        <FormField
          label="Issue / topic"
          optional
          description="Presenting issue, in the taxonomy's terms."
          error={errors.issue_topic?.message}
          htmlFor="ss-issue"
        >
          <Input id="ss-issue" {...register("issue_topic")} />
        </FormField>
        <FormField label="Diagnosis" optional error={errors.diagnosis_id?.message}>
          <Controller
            control={control}
            name="diagnosis_id"
            render={({ field }) => (
              <DiagnosisSelector
                value={field.value ?? null}
                onChange={(id, diagnosis) => {
                  field.onChange(id ?? null)
                  setValue("diagnosis_type_id", diagnosis?.type_id ?? null, {
                    shouldDirty: true,
                  })
                }}
              />
            )}
          />
        </FormField>
        {isEdit ? (
          <FormField
            label="Notes"
            optional
            description="Internal notes — not shared with the subject."
            error={errors.notes?.message}
            htmlFor="ss-notes"
          >
            <Input id="ss-notes" {...register("notes")} />
          </FormField>
        ) : null}
      </FormSection>
    </SheetForm>
  )
}

function EnumSelect<T extends string>({
  value,
  onChange,
  options,
  placeholder = "Select…",
}: {
  value: T | undefined
  onChange: (v: T) => void
  options: readonly T[] | T[]
  placeholder?: string
}) {
  return (
    <Select value={value ?? ""} onValueChange={onChange}>
      <SelectTrigger>
        <SelectValue placeholder={placeholder} />
      </SelectTrigger>
      <SelectContent>
        {options.map((o) => (
          <SelectItem key={o} value={o}>
            {o}
          </SelectItem>
        ))}
      </SelectContent>
    </Select>
  )
}

function toFormValues(s: ServiceSession): Values {
  return {
    service_id: s.service_id,
    person_id: s.person_id,
    service_provider_id: s.provider_id ?? "",
    scheduled_at: toLocalDatetime(s.scheduled_at),
    location: s.location ?? "",
    notes: s.notes ?? "",
    category: s.category ?? undefined,
    session_type: s.session_type ?? undefined,
    client_type: s.client_type ?? undefined,
    headcount: s.headcount != null ? String(s.headcount) : "",
    issue_topic: s.issue_topic ?? "",
    partner_name: s.partner_name ?? "",
    partner_relationship: s.partner_relationship ?? "",
    rate_ugx: s.rate_ugx != null ? String(s.rate_ugx) : "",
    session_number: s.session_number != null ? String(s.session_number) : "",
    diagnosis_id: s.diagnosis_id ?? null,
    diagnosis_type_id: s.diagnosis_type_id ?? null,
    is_backfill: false,
    backfill_reason: "",
  }
}

function toLocalDatetime(iso: string): string {
  if (!iso) return ""
  const d = new Date(iso)
  if (Number.isNaN(d.getTime())) return ""
  const pad = (n: number) => String(n).padStart(2, "0")
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}T${pad(d.getHours())}:${pad(d.getMinutes())}`
}

function LockedServiceSummary({
  serviceId,
  service,
}: {
  serviceId: string
  service: Service | null
}) {
  const enabled = !service && Boolean(serviceId)
  const detail = useEntityList<Service>({
    resource: "services",
    params: { page: 1, limit: 1, search: serviceId },
    listFn: servicesApi.list,
    enabled,
  })
  const resolved =
    service ?? (detail.data?.items ?? []).find((s) => s.id === serviceId) ?? null
  return (
    <div className="flex items-center gap-2.5 rounded-sm border border-fg/15 bg-surface px-3 py-2">
      <span
        aria-hidden
        className="grid size-7 shrink-0 place-items-center bg-primary/10 font-mono text-[10px] font-semibold text-primary"
      >
        SV
      </span>
      <div className="min-w-0 flex-1">
        <p className="truncate text-sm font-medium text-fg">
          {resolved?.name ?? "Selected service"}
        </p>
        <p className="truncate text-[11px] text-fg/55">
          {resolved?.service_type ?? serviceId.slice(0, 8)}
        </p>
      </div>
      <span className="shrink-0 rounded-sm border border-fg/15 bg-bg px-1.5 py-0.5 text-[10px] font-medium tracking-wide text-fg/55">
        Locked
      </span>
    </div>
  )
}

function LockedPersonSummary({
  personId,
  person,
}: {
  personId: string
  person: Person | null
}) {
  const enabled = !person && Boolean(personId)
  const detail = useEntityList<Person>({
    resource: "persons",
    params: { page: 1, limit: 1, search: personId },
    listFn: personsApi.list,
    enabled,
  })
  const resolved =
    person ?? (detail.data?.items ?? []).find((p) => p.id === personId) ?? null
  return (
    <div className="flex items-center gap-2.5 rounded-sm border border-fg/15 bg-surface px-3 py-2">
      <span
        aria-hidden
        className="grid size-7 shrink-0 place-items-center bg-primary/10 font-mono text-[10px] font-semibold text-primary"
      >
        {resolved ? personInitials(resolved) : "··"}
      </span>
      <div className="min-w-0 flex-1">
        <p className="truncate text-sm font-medium text-fg">
          {resolved ? displayName(resolved) : "Selected person"}
        </p>
        <p className="truncate text-[11px] text-fg/55">
          {resolved?.person_type ?? personId.slice(0, 8)}
        </p>
      </div>
      <span className="shrink-0 rounded-sm border border-fg/15 bg-bg px-1.5 py-0.5 text-[10px] font-medium tracking-wide text-fg/55">
        Locked
      </span>
    </div>
  )
}

function ServicePicker({ value, onChange }: { value: string; onChange: (id: string) => void }) {
  return (
    <EntityPicker<Service>
      resource="services"
      listFn={servicesApi.list}
      value={value}
      onChange={onChange}
      placeholder="Search services…"
      emptyPrompt="Start typing to search services."
      emptyNoMatch="No services match."
      renderSelected={(s) => (
        <PickerRow initials="SV" primary={s.name} secondary={s.service_type ?? "—"} size="md" />
      )}
      renderRow={(s) => (
        <PickerRow initials="SV" primary={s.name} secondary={s.service_type ?? "—"} />
      )}
    />
  )
}

function PersonPicker({ value, onChange }: { value: string; onChange: (id: string) => void }) {
  return (
    <EntityPicker<Person>
      resource="persons"
      listFn={personsApi.list}
      value={value}
      onChange={onChange}
      placeholder="Search persons…"
      emptyPrompt="Start typing to search persons."
      emptyNoMatch="No persons match."
      renderSelected={(p) => (
        <PickerRow
          initials={personInitials(p)}
          primary={displayName(p)}
          secondary={p.person_type}
          size="md"
        />
      )}
      renderRow={(p) => (
        <PickerRow initials={personInitials(p)} primary={displayName(p)} secondary={p.person_type} />
      )}
    />
  )
}

function ProviderPicker({ value, onChange }: { value: string; onChange: (id: string) => void }) {
  const row = (p: Provider) => (
    <PickerRow
      initials="PR"
      primary={p.id}
      secondary={`${p.provider_profile.tier} · ${p.provider_profile.region}`}
    />
  )
  return (
    <EntityPicker<Provider>
      resource="providers"
      listFn={providersApi.list}
      value={value}
      onChange={onChange}
      placeholder="Search providers…"
      emptyPrompt="Start typing to search providers."
      emptyNoMatch="No providers match."
      renderSelected={row}
      renderRow={row}
    />
  )
}



