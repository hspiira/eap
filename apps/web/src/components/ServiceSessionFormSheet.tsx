import { useState } from "react"

import { useQuery } from "@tanstack/react-query"
import { Controller } from "react-hook-form"
import { z } from "zod"

import { membersApi } from "@/api/endpoints/members"
import { serviceSessionsApi } from "@/api/endpoints/service-sessions"
import { servicesApi } from "@/api/endpoints/services"
import { DiagnosisSelector } from "@/components/common/DiagnosisSelector"
import { MemberPicker, ProviderPicker, ServicePicker } from "@/components/common/EntityPicker"
import { FormField } from "@/components/common/FormField"
import { FormSection } from "@/components/common/FormSection"
import { SheetForm } from "@/components/common/SheetForm"
import { CATEGORY_LABELS } from "@/components/ServiceFormSheet"
import { DeliveryContextField } from "@/components/sessions/DeliveryContextField"
import {
  EligibilityFailureNotice,
  eligibilityReasons,
} from "@/components/sessions/EligibilityFailureNotice"
import { StoredAttribution } from "@/components/sessions/SessionAttribution"
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
import { memberLabel, nameInitials } from "@/lib/display"
import { useEntityList } from "@/lib/queries"
import { cn } from "@/lib/utils"
import type { ErrorDetail } from "@/types/api"
import type { Member, Service, ServiceSession } from "@/types/entities"
import { ClientType, SessionCategory, SessionDeliveryContext, SessionType } from "@/types/enums"

const schema = z
  .object({
    service_id: z.string().trim().min(1, "Service is required"),
    member_id: z.string().trim().min(1, "Member is required"),
    service_provider_id: z.string().trim().min(1, "Practitioner is required"),
    delivery_context: z.enum([SessionDeliveryContext.DIRECT, SessionDeliveryContext.ORGANISATION], {
      message: "Choose direct or organisation delivery",
    }),
    provider_affiliation_id: z.string().optional(),
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
    (d) =>
      d.delivery_context !== SessionDeliveryContext.ORGANISATION ||
      Boolean(d.provider_affiliation_id?.trim()),
    {
      path: ["provider_affiliation_id"],
      message: "Choose the organisation this session is delivered through",
    },
  )
  .refine((d) => !d.is_backfill || new Date(d.scheduled_at).getTime() <= Date.now(), {
    path: ["scheduled_at"],
    message: "Backfilled sessions must be in the past",
  })
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
  member_id: "",
  service_provider_id: "",
  delivery_context: undefined as unknown as Values["delivery_context"],
  provider_affiliation_id: "",
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

/**
 * The create body plus the agreed delivery-context fields.
 *
 * `ServiceSessionCreate` is generated from `apps/api/schema/openapi.json`,
 * which does not carry these two fields yet. The extension is explicit so it
 * can be deleted in the same commit that regenerates the contract; the literal
 * values are guarded by `enums.contract.test.ts` once the API declares them.
 */
type SessionCreateBody = Parameters<typeof serviceSessionsApi.create>[0] & {
  delivery_context: SessionDeliveryContext
  provider_affiliation_id: string | null
}

interface ServiceSessionFormSheetProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  /** Pass a session to edit (sets initial values; otherwise create mode). */
  session?: ServiceSession | null
  /** When set, locks the service picker. */
  serviceId?: string
  /** When set, locks the member picker. */
  memberId?: string
  /** Pre-resolved service for the locked summary. */
  service?: Service | null
  /** Pre-resolved member for the locked summary. */
  member?: Member | null
  onSaved?: (session: ServiceSession) => void
}

export function ServiceSessionFormSheet({
  open,
  onOpenChange,
  session,
  serviceId,
  memberId,
  service,
  member,
  onSaved,
}: ServiceSessionFormSheetProps) {
  const lockedServiceId = serviceId ?? session?.service_id
  const lockedMemberId = memberId ?? session?.member_id
  const [ineligible, setIneligible] = useState<ErrorDetail[] | null>(null)

  const { register, control, formState, submit, serverError, setValue, watch, isEdit } =
    useEntityFormSheet<
      Values,
      SessionCreateBody & {
        __isBackfill?: boolean
        __backfillReason?: string | null
        __notes?: string
      },
      ServiceSession,
      ServiceSession
    >({
      resource: "service-sessions",
      schema,
      defaultValues: { ...EMPTY, service_id: serviceId ?? "", member_id: memberId ?? "" },
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
          member_id: values.member_id,
          provider_id: values.service_provider_id,
          delivery_context: values.delivery_context,
          provider_affiliation_id:
            values.delivery_context === SessionDeliveryContext.ORGANISATION
              ? (values.provider_affiliation_id?.trim() ?? null)
              : null,
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
          __backfillReason: isBackfill ? values.backfill_reason?.trim() || null : null,
          __notes: values.notes?.trim() || undefined,
        }
      },
      save: async ({ payload, entity, isEdit }) => {
        const { __isBackfill, __backfillReason, __notes, ...body } = payload
        if (isEdit && entity) {
          // PATCH takes the clinical/admin fields (+ notes); scheduling is
          // immutable here: reschedule is its own transition on the detail page.
          //
          // Attribution is stripped too: changing which practitioner or
          // affiliation delivered a session is a privileged, audited
          // correction, not a general edit.
          const {
            service_id: _s,
            member_id: _p,
            provider_id: _pr,
            delivery_context: _dc,
            provider_affiliation_id: _af,
            scheduled_at: _at,
            session_number: _sn,
            ...updatable
          } = body
          return serviceSessionsApi.update(entity.id, { ...updatable, notes: __notes })
        }
        setIneligible(null)
        let result = await serviceSessionsApi.create(body).catch((error: unknown) => {
          // Rendered as its own list rather than one message: the server sends
          // every reason, and the form-level banner shows only the last.
          setIneligible(eligibilityReasons(error))
          throw error
        })
        if (__isBackfill && result?.id) {
          // A backfilled session is complete by definition. Duration comes
          // from the service's configured length; the reason becomes the note.
          //
          // No case_id, deliberately: a backfill records history that already
          // happened, and spending a live authorization for it would double
          // count against an entitlement the past session never used.
          const svc = await servicesApi.getById(body.service_id).catch(() => null)
          const completed = await serviceSessionsApi.complete(result.id, {
            duration: svc?.duration_minutes ?? 60,
            notes: __backfillReason ?? "Backfilled from manual entry",
          })
          result = completed.session
        }
        return result
      },
      successToast: { create: "Session created", update: "Session updated" },
      onSaved,
    })

  const watchedService = watch("service_id")
  const watchedMember = watch("member_id")
  const watchedProvider = watch("service_provider_id")
  const watchedBackfill = !isEdit && Boolean(watch("is_backfill"))
  const watchedCategory = watch("category")
  const isGroup = watchedCategory === SessionCategory.GROUP
  const isPartnered =
    watchedCategory === SessionCategory.COUPLES || watchedCategory === SessionCategory.FAMILY

  const errors = formState.errors

  return (
    <SheetForm
      open={open}
      onOpenChange={onOpenChange}
      title={isEdit ? "Edit session" : watchedBackfill ? "Log past session" : "Schedule session"}
      description={
        isEdit
          ? "Update the time, location, or notes for this session."
          : watchedBackfill
            ? "Record a session that already happened. Marked Completed and tagged in the audit trail."
            : "Schedule a session for a member against a service. Lifecycle changes (complete / cancel / no-show) happen later from the detail view."
      }
      size="lg"
      onSubmit={submit}
      isSubmitting={formState.isSubmitting}
      serverError={serverError}
      submitLabel={isEdit ? "Save changes" : watchedBackfill ? "Log session" : "Create session"}
      submittingLabel={isEdit ? "Saving…" : watchedBackfill ? "Logging…" : "Creating…"}
    >
      {ineligible ? <EligibilityFailureNotice reasons={ineligible} /> : null}

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
            description="Number of participants: group sessions need at least 2."
            error={errors.headcount?.message}
            htmlFor="ss-headcount"
          >
            <Input id="ss-headcount" type="number" min={2} {...register("headcount")} />
          </FormField>
        ) : null}
      </FormSection>

      <FormSection title="Subject">
        <FormField label="Member" required error={errors.member_id?.message}>
          {lockedMemberId ? (
            <LockedMemberSummary memberId={lockedMemberId} member={member ?? null} />
          ) : (
            <MemberPicker
              value={watchedMember ?? ""}
              onChange={(id) =>
                setValue("member_id", id, { shouldValidate: true, shouldDirty: true })
              }
            />
          )}
        </FormField>
        <Input type="hidden" {...register("member_id")} />
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
        title="Practitioner"
        description="Who delivers the session, and whether they deliver it directly or for a supplier firm."
      >
        <FormField label="Practitioner" required error={errors.service_provider_id?.message}>
          <ProviderPicker
            value={watchedProvider ?? ""}
            onChange={(id) => {
              setValue("service_provider_id", id, { shouldValidate: true, shouldDirty: true })
              setValue("provider_affiliation_id", "", { shouldDirty: true })
            }}
          />
        </FormField>
        <Input type="hidden" {...register("service_provider_id")} />
        {isEdit ? (
          <StoredAttribution session={session ?? null} />
        ) : (
          <DeliveryContextField
            providerId={watchedProvider ?? ""}
            scheduledAt={watch("scheduled_at") ?? ""}
            context={watch("delivery_context")}
            affiliationId={watch("provider_affiliation_id") ?? ""}
            onContextChange={(value) => {
              setValue("delivery_context", value, { shouldValidate: true, shouldDirty: true })
              if (value !== SessionDeliveryContext.ORGANISATION) {
                setValue("provider_affiliation_id", "", { shouldDirty: true })
              }
            }}
            onAffiliationChange={(value) =>
              setValue("provider_affiliation_id", value, {
                shouldValidate: true,
                shouldDirty: true,
              })
            }
            contextError={errors.delivery_context?.message}
            affiliationError={errors.provider_affiliation_id?.message}
          />
        )}
        <div className="grid grid-cols-2 gap-3">
          <FormField label="Rate (UGX)" optional error={errors.rate_ugx?.message} htmlFor="ss-rate">
            <Input id="ss-rate" type="number" min={0} {...register("rate_ugx")} />
          </FormField>
          <FormField
            label="Session number"
            optional
            description="Position in the member's episode, e.g. 3 of 6."
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
              <span className="block text-xs text-fg-muted">
                Backfill a past session. It will be marked Completed and tagged with a logged-at
                timestamp + reason in the audit trail.
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
              placeholder="e.g. Phone session: paper notes, entered next day"
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
            description="Internal notes, not shared with the subject."
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
    member_id: s.member_id,
    service_provider_id: s.provider_id ?? "",
    delivery_context: deliveryContextForForm(s.delivery_context),
    provider_affiliation_id: s.provider_affiliation_id ?? "",
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

/**
 * The form offers only direct and organisation delivery. A stored `Unknown`
 * has no form value: it is a historical record whose source does not say, and
 * defaulting it to direct would invent evidence.
 */
function deliveryContextForForm(
  stored: SessionDeliveryContext | null | undefined,
): Values["delivery_context"] {
  return stored === SessionDeliveryContext.DIRECT || stored === SessionDeliveryContext.ORGANISATION
    ? stored
    : (undefined as unknown as Values["delivery_context"])
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
  const resolved = service ?? (detail.data?.items ?? []).find((s) => s.id === serviceId) ?? null
  const categoryLabel = resolved?.category ? CATEGORY_LABELS[resolved.category] : null
  return (
    <div className="flex items-center gap-2.5 rounded-sm border border-fg/15 bg-surface px-3 py-2">
      <span
        aria-hidden
        className="grid size-7 shrink-0 place-items-center bg-primary/10 text-[10px] font-semibold text-primary"
      >
        SV
      </span>
      <div className="min-w-0 flex-1">
        <p className="truncate text-sm font-medium text-fg">
          {resolved?.name ?? "Selected service"}
        </p>
        <p className={cn("truncate text-[11px] text-fg-muted", !categoryLabel && "font-mono")}>
          {categoryLabel ?? serviceId.slice(0, 8)}
        </p>
      </div>
      <span className="shrink-0 rounded-sm border border-fg/15 bg-bg px-1.5 py-0.5 text-[10px] font-medium tracking-wide text-fg-muted">
        Locked
      </span>
    </div>
  )
}

function LockedMemberSummary({ memberId, member }: { memberId: string; member: Member | null }) {
  const enabled = !member && Boolean(memberId)
  const detail = useQuery({
    queryKey: ["members", "detail", memberId],
    queryFn: () => membersApi.getById(memberId),
    enabled,
  })
  const resolved = member ?? detail.data ?? null
  return (
    <div className="flex items-center gap-2.5 rounded-sm border border-fg/15 bg-surface px-3 py-2">
      <span
        aria-hidden
        className="grid size-7 shrink-0 place-items-center bg-primary/10 text-[10px] font-semibold text-primary"
      >
        {resolved ? nameInitials(memberLabel(resolved)) : "··"}
      </span>
      <div className="min-w-0 flex-1">
        <p className="truncate text-sm font-medium text-fg">
          {resolved ? memberLabel(resolved) : "Selected member"}
        </p>
        <p className={cn("truncate text-[11px] text-fg-muted", !resolved?.relation && "font-mono")}>
          {resolved?.relation ?? "Member"}
        </p>
      </div>
      <span className="shrink-0 rounded-sm border border-fg/15 bg-bg px-1.5 py-0.5 text-[10px] font-medium tracking-wide text-fg-muted">
        Locked
      </span>
    </div>
  )
}
