import { useEffect, useState } from "react"

import { useQueryClient } from "@tanstack/react-query"
import { Controller } from "react-hook-form"
import { z } from "zod"

import { personsApi } from "@/api/endpoints/persons"
import { providersApi } from "@/api/endpoints/providers"
import { serviceSessionsApi } from "@/api/endpoints/service-sessions"
import { servicesApi } from "@/api/endpoints/services"
import { DiagnosisSelector } from "@/components/common/DiagnosisSelector"
import { FormField } from "@/components/common/FormField"
import { FormSection } from "@/components/common/FormSection"
import { SheetForm } from "@/components/common/SheetForm"
import { Input } from "@/components/ui/input"
import { useApiForm } from "@/hooks/useApiForm"
import { useDebouncedValue } from "@/hooks/useDebouncedValue"
import { useEntityList } from "@/lib/queries"
import type { Person, Provider, Service, ServiceSession } from "@/types/entities"

const FREETEXT_FALLBACK_ENABLED =
  typeof import.meta !== "undefined" &&
  import.meta.env?.VITE_DIAGNOSIS_FREETEXT_FALLBACK === "true"

const schema = z.object({
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
  diagnosis_text: z.string().optional(),
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
  diagnosis_text: "",
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
  const isEdit = Boolean(session)
  const queryClient = useQueryClient()
  const lockedServiceId = serviceId ?? session?.service_id
  const lockedPersonId = personId ?? session?.person_id

  const initial: Values = session ? toValues(session) : { ...EMPTY, service_id: serviceId ?? "", person_id: personId ?? "" }

  const { register, control, reset, formState, submit, serverError, setValue, watch } =
    useApiForm<Values>({
      schema,
      defaultValues: initial,
      successToast: isEdit ? "Session updated" : "Session created",
      onSubmit: async (values) => {
        const payload = {
          service_id: values.service_id,
          person_id: values.person_id,
          service_provider_id: values.service_provider_id || null,
          contract_id: values.contract_id || null,
          scheduled_at: new Date(values.scheduled_at).toISOString(),
          location: values.location?.trim() || null,
          notes: values.notes?.trim() || null,
          diagnosis_id: values.diagnosis_id || null,
          diagnosis_text: FREETEXT_FALLBACK_ENABLED
            ? values.diagnosis_text?.trim() || null
            : null,
        }
        const result = session
          ? await serviceSessionsApi.update(session.id, payload)
          : await serviceSessionsApi.create(
              payload as Parameters<typeof serviceSessionsApi.create>[0],
            )
        await queryClient.invalidateQueries({ queryKey: ["service-sessions", "list"] })
        if (session) {
          await queryClient.invalidateQueries({
            queryKey: ["service-sessions", "detail", session.id],
          })
        }
        onSaved?.(result)
        onOpenChange(false)
        reset(EMPTY)
      },
    })

  const watchedService = watch("service_id")
  const watchedPerson = watch("person_id")
  const watchedProvider = watch("service_provider_id")

  useEffect(() => {
    if (!open) return
    if (session) reset(toValues(session))
  }, [open, session, reset])

  const errors = formState.errors as Record<string, { message?: string }>

  return (
    <SheetForm
      open={open}
      onOpenChange={onOpenChange}
      title={isEdit ? "Edit session" : "Schedule session"}
      description={
        isEdit
          ? "Update the time, location, or notes for this session."
          : "Schedule a session for a person against a service. Lifecycle changes (complete / cancel / no-show) happen later from the detail view."
      }
      size="lg"
      onSubmit={submit}
      isSubmitting={formState.isSubmitting}
      serverError={serverError}
      submitLabel={isEdit ? "Save changes" : "Create session"}
      submittingLabel={isEdit ? "Saving…" : "Creating…"}
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
        <input type="hidden" {...register("service_id")} />
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
        <input type="hidden" {...register("person_id")} />
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
        <input type="hidden" {...register("service_provider_id")} />
      </FormSection>

      <FormSection title="Schedule">
        <FormField
          label="Scheduled at"
          required
          error={errors.scheduled_at?.message}
          htmlFor="ss-scheduled"
        >
          <Input id="ss-scheduled" type="datetime-local" {...register("scheduled_at")} />
        </FormField>
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
        {FREETEXT_FALLBACK_ENABLED ? (
          <FormField
            label="Diagnosis (free text — legacy)"
            optional
            description="Only use if no taxonomy match exists."
            error={errors.diagnosis_text?.message}
            htmlFor="ss-diag-text"
          >
            <Input id="ss-diag-text" {...register("diagnosis_text")} />
          </FormField>
        ) : null}
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

function toValues(s: ServiceSession): Values {
  return {
    service_id: s.service_id,
    person_id: s.person_id,
    service_provider_id: s.service_provider_id ?? "",
    contract_id: s.contract_id ?? "",
    scheduled_at: toLocalDatetime(s.scheduled_at),
    location: s.location ?? "",
    notes: s.notes ?? "",
    diagnosis_id: s.diagnosis_id ?? null,
    diagnosis_text: s.diagnosis_text ?? "",
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
        {resolved ? personInitial(resolved) : "··"}
      </span>
      <div className="min-w-0 flex-1">
        <p className="truncate text-sm font-medium text-fg">
          {resolved
            ? `${resolved.first_name} ${resolved.last_name}`
            : "Selected person"}
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

function ServicePicker({
  value,
  onChange,
}: {
  value: string
  onChange: (id: string) => void
}) {
  const [query, setQuery] = useState("")
  const debounced = useDebouncedValue(query.trim(), 250)
  const list = useEntityList<Service>({
    resource: "services",
    params: { page: 1, limit: 8, search: debounced || undefined },
    listFn: servicesApi.list,
  })
  const items = list.data?.items ?? []
  const selected = items.find((s) => s.id === value)

  if (selected) {
    return (
      <div className="flex items-center gap-2.5 rounded-sm border border-fg/15 bg-surface px-3 py-2">
        <span
          aria-hidden
          className="grid size-7 shrink-0 place-items-center bg-primary/10 font-mono text-[10px] font-semibold text-primary"
        >
          SV
        </span>
        <div className="min-w-0 flex-1">
          <p className="truncate text-sm font-medium text-fg">{selected.name}</p>
          <p className="truncate text-[11px] text-fg/55">
            {selected.service_type ?? "—"}
          </p>
        </div>
        <ChangeButton onClick={() => onChange("")} />
      </div>
    )
  }
  return (
    <PickerShell
      query={query}
      onQueryChange={setQuery}
      placeholder="Search services…"
      empty={debounced ? "No services match." : "Start typing to search services."}
      loading={list.isPending}
      items={items}
      renderItem={(s) => (
        <button
          type="button"
          onClick={() => onChange(s.id)}
          className="flex w-full items-center gap-2.5 px-3 py-2 text-left transition-colors hover:bg-surface-hover focus-visible:bg-surface-hover focus-visible:outline-none"
        >
          <span
            aria-hidden
            className="grid size-6 shrink-0 place-items-center bg-primary/10 font-mono text-[10px] font-semibold text-primary"
          >
            SV
          </span>
          <span className="min-w-0 flex-1">
            <span className="block truncate text-sm font-medium text-fg">{s.name}</span>
            <span className="block truncate text-[11px] text-fg/55">
              {s.service_type ?? "—"}
            </span>
          </span>
        </button>
      )}
    />
  )
}

function PersonPicker({
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
    params: { page: 1, limit: 8, search: debounced || undefined },
    listFn: personsApi.list,
  })
  const items = list.data?.items ?? []
  const selected = items.find((p) => p.id === value)

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
          <p className="truncate text-[11px] text-fg/55">{selected.person_type}</p>
        </div>
        <ChangeButton onClick={() => onChange("")} />
      </div>
    )
  }
  return (
    <PickerShell
      query={query}
      onQueryChange={setQuery}
      placeholder="Search persons…"
      empty={debounced ? "No persons match." : "Start typing to search persons."}
      loading={list.isPending}
      items={items}
      renderItem={(p) => (
        <button
          type="button"
          onClick={() => onChange(p.id)}
          className="flex w-full items-center gap-2.5 px-3 py-2 text-left transition-colors hover:bg-surface-hover focus-visible:bg-surface-hover focus-visible:outline-none"
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
            <span className="block truncate text-[11px] text-fg/55">{p.person_type}</span>
          </span>
        </button>
      )}
    />
  )
}

function ProviderPicker({
  value,
  onChange,
}: {
  value: string
  onChange: (id: string) => void
}) {
  const [query, setQuery] = useState("")
  const debounced = useDebouncedValue(query.trim(), 250)
  const list = useEntityList<Provider>({
    resource: "providers",
    params: { page: 1, limit: 8, search: debounced || undefined },
    listFn: providersApi.list,
  })
  const items = list.data?.items ?? []
  const selected = items.find((p) => p.id === value)

  if (selected) {
    return (
      <div className="flex items-center gap-2.5 rounded-sm border border-fg/15 bg-surface px-3 py-2">
        <span
          aria-hidden
          className="grid size-7 shrink-0 place-items-center bg-primary/10 font-mono text-[10px] font-semibold text-primary"
        >
          PR
        </span>
        <div className="min-w-0 flex-1">
          <p className="truncate text-sm font-medium text-fg">{selected.name}</p>
          <p className="truncate text-[11px] text-fg/55">
            {selected.tier} · {selected.region}
          </p>
        </div>
        <ChangeButton onClick={() => onChange("")} />
      </div>
    )
  }
  return (
    <PickerShell
      query={query}
      onQueryChange={setQuery}
      placeholder="Search providers…"
      empty={debounced ? "No providers match." : "Start typing to search providers."}
      loading={list.isPending}
      items={items}
      renderItem={(p) => (
        <button
          type="button"
          onClick={() => onChange(p.id)}
          className="flex w-full items-center gap-2.5 px-3 py-2 text-left transition-colors hover:bg-surface-hover focus-visible:bg-surface-hover focus-visible:outline-none"
        >
          <span
            aria-hidden
            className="grid size-6 shrink-0 place-items-center bg-primary/10 font-mono text-[10px] font-semibold text-primary"
          >
            PR
          </span>
          <span className="min-w-0 flex-1">
            <span className="block truncate text-sm font-medium text-fg">{p.name}</span>
            <span className="block truncate text-[11px] text-fg/55">
              {p.tier} · {p.region}
            </span>
          </span>
        </button>
      )}
    />
  )
}

function PickerShell<T extends { id: string }>({
  query,
  onQueryChange,
  placeholder,
  empty,
  loading,
  items,
  renderItem,
}: {
  query: string
  onQueryChange: (v: string) => void
  placeholder: string
  empty: string
  loading: boolean
  items: T[]
  renderItem: (item: T) => React.ReactNode
}) {
  return (
    <div className="space-y-1.5">
      <Input
        placeholder={placeholder}
        value={query}
        onChange={(e) => onQueryChange(e.target.value)}
      />
      <div className="max-h-48 overflow-y-auto rounded-sm border border-fg/15 bg-bg">
        {loading ? (
          <p className="px-3 py-2 text-xs text-fg/55">Loading…</p>
        ) : items.length === 0 ? (
          <p className="px-3 py-2 text-xs text-fg/55">{empty}</p>
        ) : (
          <ul className="divide-y divide-fg/8">
            {items.map((it) => (
              <li key={it.id}>{renderItem(it)}</li>
            ))}
          </ul>
        )}
      </div>
    </div>
  )
}

function ChangeButton({ onClick }: { onClick: () => void }) {
  return (
    <button
      type="button"
      onClick={onClick}
      className="shrink-0 rounded-sm px-2 py-1 text-xs font-medium text-fg/65 hover:bg-surface-hover hover:text-fg"
    >
      Change
    </button>
  )
}

function personInitial(p: Person): string {
  const f = p.first_name?.[0] ?? ""
  const l = p.last_name?.[0] ?? ""
  return (f + l).toUpperCase() || "·"
}
