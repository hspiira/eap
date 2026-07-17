import { useState } from "react"

import { Controller } from "react-hook-form"
import { z } from "zod"

import { clientsApi } from "@/api/endpoints/clients"
import { contractsApi } from "@/api/endpoints/contracts"
import type { ContractCreate } from "@/api/generated"
import { FormField } from "@/components/common/FormField"
import { FormSection } from "@/components/common/FormSection"
import { SheetForm } from "@/components/common/SheetForm"
import { Button } from "@/components/ui/button"
import { Checkbox } from "@/components/ui/checkbox"
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
import { nameInitials } from "@/lib/display"
import { useEntityList } from "@/lib/queries"
import type { Client, Contract } from "@/types/entities"
import { PaymentFrequency } from "@/types/enums"

const FREQUENCY_VALUES = [
  PaymentFrequency.WEEKLY,
  PaymentFrequency.MONTHLY,
  PaymentFrequency.QUARTERLY,
  PaymentFrequency.ANNUALLY,
] as const

const contractSchema = z
  .object({
    client_id: z.string().trim().min(1, "Client is required"),
    start_date: z.string().min(1, "Start date is required"),
    end_date: z.string().min(1, "End date is required"),
    billing_amount: z
      .string()
      .trim()
      .min(1, "Billing amount is required")
      .refine((v) => /^\d+(\.\d+)?$/.test(v) && Number(v) > 0, "Must be a positive number"),
    currency: z
      .string()
      .trim()
      .length(3, "Use the ISO 3-letter currency code (e.g. KES, USD)"),
    payment_frequency: z.enum(FREQUENCY_VALUES as readonly [string, ...string[]], {
      message: "Payment frequency is required",
    }),
    is_auto_renew: z.boolean().optional(),
  })
  .refine((d) => d.end_date >= d.start_date, {
    path: ["end_date"],
    message: "End date must be on or after start date",
  })

type ContractFormValues = z.infer<typeof contractSchema>

const EMPTY: ContractFormValues = {
  client_id: "",
  start_date: "",
  end_date: "",
  billing_amount: "",
  currency: "KES",
  payment_frequency: PaymentFrequency.MONTHLY,
  is_auto_renew: false,
}

/** Convert an HTML `date` input value (`YYYY-MM-DD`) to an ISO datetime BE will accept. */
function toIsoDatetime(date: string): string {
  if (!date) return ""
  return `${date}T00:00:00Z`
}

/** Convert a BE ISO datetime back to a `YYYY-MM-DD` string for the date input. */
function fromIsoDatetime(iso: string | null | undefined): string {
  if (!iso) return ""
  const m = /^(\d{4}-\d{2}-\d{2})/.exec(iso)
  return m ? m[1] : ""
}

interface ContractFormSheetProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  /** Pass a contract to edit; omit/null to create. */
  contract?: Contract | null
  /** When set, locks the form to this client and hides the picker. */
  clientId?: string
  /** Pre-resolved client used for the locked summary (avoids extra fetch). */
  client?: Client | null
  onSaved?: (contract: Contract) => void
}

export function ContractFormSheet({
  open,
  onOpenChange,
  contract,
  clientId,
  client,
  onSaved,
}: ContractFormSheetProps) {
  const lockedClientId = clientId ?? contract?.client_id

  const { register, control, formState, submit, serverError, setValue, watch, isEdit } =
    useEntityFormSheet<ContractFormValues, ContractCreate, Contract, Contract>({
      resource: "contracts",
      schema: contractSchema,
      defaultValues: { ...EMPTY, client_id: clientId ?? "" },
      open,
      onOpenChange,
      entity: contract,
      // Read straight off the wire shape. These previously read top-level
      // start_date/billing_amount/currency/billing_frequency, none of which the
      // BE sends, so editing a contract opened a blank form and saving it reset
      // the currency to the KES default.
      toFormValues: (c) => ({
        client_id: c.client_id,
        start_date: fromIsoDatetime(c.period.start_date),
        end_date: fromIsoDatetime(c.period.end_date),
        billing_amount: c.billing_rate.amount,
        currency: c.billing_rate.currency,
        payment_frequency: c.payment_frequency,
        is_auto_renew: c.is_auto_renew,
      }),
      parsePayload: (values): ContractCreate => ({
        client_id: values.client_id,
        start_date: toIsoDatetime(values.start_date),
        end_date: toIsoDatetime(values.end_date),
        billing_rate: {
          amount: values.billing_amount,
          currency: values.currency.toUpperCase(),
        },
        payment_frequency: values.payment_frequency as PaymentFrequency,
        is_auto_renew: Boolean(values.is_auto_renew),
      }),
      save: async ({ payload, entity, isEdit }) => {
        if (isEdit && entity) {
          // BE `ContractUpdate` only accepts `{billing_rate?, payment_frequency?, is_auto_renew?}`.
          // Date changes go via the dedicated `renew` route; client_id is immutable.
          return contractsApi.update(entity.id, {
            billing_rate: payload.billing_rate,
            payment_frequency: payload.payment_frequency,
            is_auto_renew: payload.is_auto_renew,
          })
        }
        return contractsApi.create(payload)
      },
      successToast: { create: "Contract created", update: "Contract updated" },
      extraInvalidations: lockedClientId
        ? [{ queryKey: ["clients", "detail", lockedClientId] }]
        : undefined,
      onSaved,
    })

  const watchedClientId = watch("client_id")

  const errors = formState.errors

  return (
    <SheetForm
      open={open}
      onOpenChange={onOpenChange}
      title={isEdit ? "Edit contract" : "Add contract"}
      description={
        isEdit
          ? "Update lifecycle dates and billing details."
          : "Create a contract for a corporate client. You can refine pricing and renewals later."
      }
      size="md"
      onSubmit={submit}
      isSubmitting={formState.isSubmitting}
      serverError={serverError}
      submitLabel={isEdit ? "Save changes" : "Create contract"}
      submittingLabel={isEdit ? "Saving…" : "Creating…"}
    >
      <FormSection title="Client">
        {lockedClientId ? (
          <LockedClientSummary clientId={lockedClientId} client={client ?? null} />
        ) : (
          <FormField
            label="Client"
            required
            error={errors.client_id?.message}
            description="Select the corporate client this contract is for."
          >
            <ClientPicker
              value={watchedClientId}
              onChange={(id) =>
                setValue("client_id", id, { shouldValidate: true, shouldDirty: true })
              }
            />
          </FormField>
        )}
        <Input type="hidden" {...register("client_id")} />
      </FormSection>

      <FormSection title="Term">
        <div className="grid grid-cols-2 gap-3">
          <FormField
            label="Start date"
            required
            error={errors.start_date?.message}
            htmlFor="cf-start"
          >
            <Input id="cf-start" type="date" {...register("start_date")} />
          </FormField>
          <FormField
            label="End date"
            required
            error={errors.end_date?.message}
            htmlFor="cf-end"
          >
            <Input id="cf-end" type="date" {...register("end_date")} />
          </FormField>
        </div>
        <div className="flex items-center gap-2 pt-1">
          <Controller
            control={control}
            name="is_auto_renew"
            render={({ field }) => (
              <Checkbox
                id="cf-auto-renew"
                checked={Boolean(field.value)}
                onCheckedChange={field.onChange}
              />
            )}
          />
          <label
            htmlFor="cf-auto-renew"
            className="cursor-pointer text-sm text-fg"
          >
            Auto-renew at end of term
          </label>
        </div>
      </FormSection>

      <FormSection
        title="Billing"
        description="Pricing model (retainer, framework, fee-for-service…) is configured separately on the contract detail page."
      >
        <FormField
          label="Payment frequency"
          required
          error={errors.payment_frequency?.message}
          htmlFor="cf-frequency"
        >
          <Controller
            control={control}
            name="payment_frequency"
            render={({ field }) => (
              <Select value={field.value} onValueChange={field.onChange}>
                <SelectTrigger id="cf-frequency">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {FREQUENCY_VALUES.map((f) => (
                    <SelectItem key={f} value={f}>
                      {f}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            )}
          />
        </FormField>
        <div className="grid grid-cols-[1fr_6rem] gap-3">
          <FormField
            label="Billing rate"
            required
            error={errors.billing_amount?.message}
            htmlFor="cf-amount"
          >
            <Input
              id="cf-amount"
              type="number"
              inputMode="decimal"
              step="0.01"
              min="0"
              placeholder="0.00"
              className="font-mono"
              {...register("billing_amount")}
            />
          </FormField>
          <FormField
            label="Currency"
            required
            error={errors.currency?.message}
            htmlFor="cf-currency"
          >
            <Input
              id="cf-currency"
              placeholder="KES"
              maxLength={3}
              className="font-mono uppercase"
              {...register("currency")}
            />
          </FormField>
        </div>
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

interface ClientPickerProps {
  value: string
  onChange: (clientId: string) => void
}

function ClientPicker({ value, onChange }: ClientPickerProps) {
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
          {nameInitials(selected.name)}
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
            {debounced ? "No clients match that search." : "Start typing to search clients."}
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
                    {nameInitials(c.name)}
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

