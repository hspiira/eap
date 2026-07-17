
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
import { useEntityFormSheet } from "@/hooks/useEntityFormSheet"
import { displayName, personInitials } from "@/lib/display"
import { useEntityList } from "@/lib/queries"
import type { Person, Provider, Service, ServiceSession } from "@/types/entities"

const schema = z
  .object({
    service_id: z.string().trim().min(1, "Service is required"),
    person_id: z.string().trim().min(1, "Person is required"),
    service_provider_id: z.string().optional(),
    contract_id: z.string().optional(),
    scheduled_at: z
      .string()
      .min(1, "Scheduled time is required")
      .refine((s) => !Number.isNaN(Date.parse(s)), "Must be a valid date/time"),
    location: z.string().optional(),
    notes: z.string().optional(),
    diagnosis_id: z.string().nullable().optional(),
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

type Values = z.infer<typeof schema>

const EMPTY: Values = {
  service_id: "",
  person_id: "",
  service_provider_id: "",
  contract_id: "",
  scheduled_at: "",
  location: "",
  notes: "",
  diagnosis_id: null,
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
      // BE `ServiceSessionCreate` only accepts `{service_id, provider_id,
      // person_id, scheduled_at, location?}`. `notes`, `diagnosis_*`, and
      // `metadata` are NOT accepted at create time — `notes` belongs on the
      // complete-request, diagnosis is set via a separate flow, backfill
      // intent is communicated by the FE via `__isBackfill` and translated
      // into a `complete()` call after create.
      parsePayload: (values) => {
        const isBackfill = !session && Boolean(values.is_backfill)
        return {
          service_id: values.service_id,
          person_id: values.person_id,
          provider_id: values.service_provider_id || "",
          scheduled_at: new Date(values.scheduled_at).toISOString(),
          location: values.location?.trim() || null,
          __isBackfill: isBackfill,
          __backfillReason: isBackfill ? (values.backfill_reason?.trim() || null) : null,
        }
      },
      save: async ({ payload, entity, isEdit }) => {
        const { __isBackfill, __backfillReason, ...body } = payload
        // BE `ServiceSessionUpdate` (PATCH) shape may differ from create —
        // for now we send the same body and the BE silently ignores extras
        // on update. Once openapi.json exposes ServiceSessionUpdate we can
        // tighten this.
        let result = isEdit && entity
          ? await serviceSessionsApi.update(entity.id, body)
          : await serviceSessionsApi.create(body)
        if (__isBackfill && result?.id) {
          // BE `ServiceSessionCompleteRequest` requires `{duration, notes}`.
          // Backfill defaults to the service's scheduled duration; the user-
          // typed reason becomes the completion note.
          result = await serviceSessionsApi.complete(result.id, {
            duration: 60, // TODO: read from selected Service.duration_minutes
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
        <FormField label="Diagnosis" optional error={errors.diagnosis_id?.message}>
          <Controller
            control={control}
            name="diagnosis_id"
            render={({ field }) => (
              <DiagnosisSelector
                value={field.value ?? null}
                onChange={(id) => field.onChange(id ?? null)}
              />
            )}
          />
        </FormField>
        <FormField
          label="Notes"
          optional
          description="Internal notes — not shared with the subject."
          error={errors.notes?.message}
          htmlFor="ss-notes"
        >
          <Input id="ss-notes" {...register("notes")} />
        </FormField>
      </FormSection>
    </SheetForm>
  )
}

function toFormValues(s: ServiceSession): Values {
  return {
    service_id: s.service_id,
    person_id: s.person_id,
    service_provider_id: s.service_provider_id ?? "",
    contract_id: s.contract_id ?? "",
    scheduled_at: toLocalDatetime(s.scheduled_at),
    location: s.location ?? "",
    notes: s.notes ?? "",
    diagnosis_id: s.diagnosis_id ?? null,
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



