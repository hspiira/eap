import { useState } from "react"

import { X } from "lucide-react"
import { z } from "zod"

import { careCallbacksApi } from "@/api/endpoints/care-callbacks"
import { clientsApi } from "@/api/endpoints/clients"
import { usersApi } from "@/api/endpoints/users"
import { ClientPicker } from "@/components/common/EntityPicker"
import { FormField } from "@/components/common/FormField"
import { FormSection } from "@/components/common/FormSection"
import { SheetForm } from "@/components/common/SheetForm"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Textarea } from "@/components/ui/textarea"
import { useDebouncedValue } from "@/hooks/useDebouncedValue"
import { useEntityFormSheet } from "@/hooks/useEntityFormSheet"
import { nameInitials } from "@/lib/display"
import { useEntityList } from "@/lib/queries"
import type { CallbackCampaign, Client, User } from "@/types/entities"

const schema = z
  .object({
    client_id: z.string().trim().min(1, "Client is required"),
    name: z.string().trim().min(3, "Name must be at least 3 characters"),
    period_start: z.string().min(1, "Start date is required"),
    period_end: z.string().min(1, "End date is required"),
    target_count: z
      .string()
      .min(1, "Target count is required")
      .refine((v) => /^\d+$/.test(v) && Number(v) >= 0, "Must be a whole number"),
    counsellor_pool: z.array(z.string()).min(1, "Pick at least one counsellor"),
    sampling_notes: z.string().trim().optional(),
  })
  .refine((v) => Date.parse(v.period_end) >= Date.parse(v.period_start), {
    path: ["period_end"],
    message: "End date must be on or after start date",
  })

type Values = z.infer<typeof schema>

const EMPTY: Values = {
  client_id: "",
  name: "",
  period_start: "",
  period_end: "",
  target_count: "",
  counsellor_pool: [],
  sampling_notes: "",
}

interface CampaignFormSheetProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  /** When set, locks the client. */
  clientId?: string
  client?: Client | null
  onSaved?: (campaign: CallbackCampaign) => void
}

export function CampaignFormSheet({
  open,
  onOpenChange,
  clientId,
  client,
  onSaved,
}: CampaignFormSheetProps) {
  const lockedClientId = clientId

  const { register, formState, submit, serverError, setValue, watch } = useEntityFormSheet<
    Values,
    Parameters<typeof careCallbacksApi.createCampaign>[0],
    CallbackCampaign,
    CallbackCampaign
  >({
    resource: "care-callback-campaigns",
    schema,
    defaultValues: { ...EMPTY, client_id: clientId ?? "" },
    open,
    onOpenChange,
    parsePayload: (values) => ({
      client_id: values.client_id,
      name: values.name,
      period_start: values.period_start,
      period_end: values.period_end,
      target_count: Number(values.target_count),
      counsellor_pool: values.counsellor_pool,
      sampling_notes: values.sampling_notes?.trim() || null,
    }),
    save: ({ payload }) => careCallbacksApi.createCampaign(payload),
    successToast: { create: "Campaign created" },
    onSaved,
  })

  const watchedClient = watch("client_id")
  const watchedCounsellors = watch("counsellor_pool")

  const errors = formState.errors

  return (
    <SheetForm
      open={open}
      onOpenChange={onOpenChange}
      title="New care-callback campaign"
      description="Define the audience size and counsellor pool. Enrol persons and activate once ready — outreach records start Pending until a counsellor claims each one."
      size="lg"
      onSubmit={submit}
      isSubmitting={formState.isSubmitting}
      serverError={serverError}
      submitLabel="Create campaign"
      submittingLabel="Creating…"
    >
      <FormSection title="Client">
        <FormField label="Client" required error={errors.client_id?.message}>
          {lockedClientId ? (
            <LockedClientSummary clientId={lockedClientId} client={client ?? null} />
          ) : (
            <ClientPicker
              value={watchedClient ?? ""}
              onChange={(id) =>
                setValue("client_id", id, { shouldValidate: true, shouldDirty: true })
              }
            />
          )}
        </FormField>
        <Input type="hidden" {...register("client_id")} />
      </FormSection>

      <FormSection title="Identity">
        <FormField label="Name" required error={errors.name?.message} htmlFor="cf-name">
          <Input
            id="cf-name"
            placeholder="e.g. Q2 anxiety/depression follow-up wave"
            {...register("name")}
          />
        </FormField>
        <FormField
          label="Target count"
          required
          description="How many outreach records this wave targets."
          error={errors.target_count?.message}
          htmlFor="cf-target"
        >
          <Input
            id="cf-target"
            type="number"
            inputMode="numeric"
            min={0}
            placeholder="e.g. 60"
            className="font-mono"
            {...register("target_count")}
          />
        </FormField>
      </FormSection>

      <FormSection title="Outreach window">
        <div className="grid grid-cols-2 gap-3">
          <FormField
            label="Start date"
            required
            error={errors.period_start?.message}
            htmlFor="cf-start"
          >
            <Input id="cf-start" type="date" {...register("period_start")} />
          </FormField>
          <FormField
            label="End date"
            required
            description="Cases not completed by this date roll into the report as no-answer."
            error={errors.period_end?.message}
            htmlFor="cf-end"
          >
            <Input id="cf-end" type="date" {...register("period_end")} />
          </FormField>
        </div>
      </FormSection>

      <FormSection
        title="Counsellor pool"
        description="Counsellors who can claim outreach records once the campaign is active. Required to activate — a campaign can't go live with an empty pool."
      >
        <FormField
          label="Counsellors"
          required
          error={errors.counsellor_pool?.message}
        >
          <CounsellorMultiPicker
            value={watchedCounsellors ?? []}
            onChange={(ids) =>
              setValue("counsellor_pool", ids, {
                shouldValidate: true,
                shouldDirty: true,
              })
            }
          />
        </FormField>
      </FormSection>

      <FormSection title="Notes">
        <FormField
          label="Sampling notes"
          optional
          description="Internal notes on how the audience was selected — appears on the campaign detail."
          error={errors.sampling_notes?.message}
          htmlFor="cf-sampling-notes"
        >
          <Textarea id="cf-sampling-notes" rows={3} {...register("sampling_notes")} />
        </FormField>
      </FormSection>
    </SheetForm>
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
        {resolved ? nameInitials(resolved.name) : "··"}
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

function CounsellorMultiPicker({
  value,
  onChange,
}: {
  value: string[]
  onChange: (ids: string[]) => void
}) {
  const [query, setQuery] = useState("")
  const debounced = useDebouncedValue(query.trim(), 250)
  const list = useEntityList<User>({
    resource: "users",
    params: { page: 1, limit: 8, search: debounced || undefined },
    listFn: usersApi.list,
  })
  const items = list.data?.items ?? []
  const selectedSet = new Set(value)

  const toggle = (id: string) => {
    if (selectedSet.has(id)) onChange(value.filter((v) => v !== id))
    else onChange([...value, id])
  }

  return (
    <div className="space-y-2">
      {value.length > 0 ? (
        <div className="flex flex-wrap gap-1.5">
          {value.map((id) => {
            const user = items.find((u) => u.id === id)
            return (
              <span
                key={id}
                className="inline-flex items-center gap-1 rounded-sm border border-primary/30 bg-primary/10 px-1.5 py-0.5 text-xs text-primary"
              >
                {user?.email ?? id.slice(0, 12)}
                <Button
                  type="button"
                  variant="ghost"
                  size="sm"
                  onClick={() => toggle(id)}
                  aria-label={`Remove ${user?.email ?? id}`}
                  className="size-4 p-0 hover:bg-primary/15"
                >
                  <X className="size-3" />
                </Button>
              </span>
            )
          })}
        </div>
      ) : null}
      <Input
        placeholder="Search users by email…"
        value={query}
        onChange={(e) => setQuery(e.target.value)}
      />
      <div className="max-h-44 overflow-y-auto rounded-sm border border-fg/15 bg-bg">
        {list.isPending ? (
          <p className="px-3 py-2 text-xs text-fg/55">Loading…</p>
        ) : items.length === 0 ? (
          <p className="px-3 py-2 text-xs text-fg/55">
            {debounced ? "No users match." : "Start typing to search users."}
          </p>
        ) : (
          <ul className="divide-y divide-fg/8">
            {items.map((u) => {
              const active = selectedSet.has(u.id)
              return (
                <li key={u.id}>
                  <Button
                    type="button"
                    variant="ghost"
                    onClick={() => toggle(u.id)}
                    className="flex h-auto w-full items-center justify-between gap-2.5 px-3 py-2 text-left"
                  >
                    <span className="min-w-0 truncate text-sm text-fg">{u.email}</span>
                    {active ? (
                      <span className="shrink-0 rounded-sm border border-primary/30 bg-primary/10 px-1.5 py-0.5 text-[10px] font-medium text-primary">
                        Selected
                      </span>
                    ) : null}
                  </Button>
                </li>
              )
            })}
          </ul>
        )}
      </div>
    </div>
  )
}

