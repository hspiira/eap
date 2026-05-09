/**
 * Model-aware pricing config editor for contract create/edit. Switches input set per
 * `PricingModel`. Returns a fully-shaped `ContractPricing` to the parent.
 *
 * Acceptance per plan: one screen-test per pricing model + invoice-line preview rendered inline.
 */

import { useEffect, useMemo, useState } from "react"

import { useQuery } from "@tanstack/react-query"

import { pricingApi } from "@/api/endpoints/pricing"
import { FormField } from "@/components/common/FormField"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"
import type { ContractPricing, InvoiceLinePreview } from "@/types/entities"
import { PricingModel } from "@/types/enums"

interface PricingConfigProps {
  value: ContractPricing
  onChange: (pricing: ContractPricing) => void
  /** Sessions per month used for the preview math. */
  projectedSessions?: number
}

const MODEL_VALUES = [
  PricingModel.RETAINER,
  PricingModel.FRAMEWORK,
  PricingModel.FFS,
  PricingModel.ADMIN_UTILISATION,
  PricingModel.VALUE_ADD,
] as const

export function defaultPricingFor(model: PricingModel): ContractPricing {
  switch (model) {
    case PricingModel.RETAINER:
      return { model, monthly_fee: 0, session_cap: null, overflow_rate: null }
    case PricingModel.FRAMEWORK:
      return { model, deposit: 0, drawdown_balance: 0, unit_rate: 0 }
    case PricingModel.FFS:
      return { model, unit_rate: 0 }
    case PricingModel.ADMIN_UTILISATION:
      return { model, monthly_admin_fee: 0, admin_floor: 0, utilisation_rate: 0 }
    case PricingModel.VALUE_ADD:
      return { model, monthly_fee: 0, bundled_services: [] }
  }
}

export function PricingConfig({ value, onChange, projectedSessions = 20 }: PricingConfigProps) {
  const handleModel = (next: string) => {
    if (MODEL_VALUES.includes(next as PricingModel)) {
      onChange(defaultPricingFor(next as PricingModel))
    }
  }

  return (
    <div className="space-y-4">
      <FormField label="Pricing model" required htmlFor="pricing-model">
        <Select value={value.model} onValueChange={handleModel}>
          <SelectTrigger
            id="pricing-model"
            className="rounded-none h-9 border-fg/30 bg-white text-fg [&>svg]:text-fg"
          >
            <SelectValue placeholder="Select model" />
          </SelectTrigger>
          <SelectContent className="rounded-none border-fg/30 bg-white">
            {MODEL_VALUES.map((m) => (
              <SelectItem key={m} value={m} className="rounded-none">
                {m}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </FormField>

      {value.model === PricingModel.RETAINER && (
        <RetainerInputs value={value} onChange={onChange} />
      )}
      {value.model === PricingModel.FRAMEWORK && (
        <FrameworkInputs value={value} onChange={onChange} />
      )}
      {value.model === PricingModel.FFS && <FFSInputs value={value} onChange={onChange} />}
      {value.model === PricingModel.ADMIN_UTILISATION && (
        <AdminUtilisationInputs value={value} onChange={onChange} />
      )}
      {value.model === PricingModel.VALUE_ADD && (
        <ValueAddInputs value={value} onChange={onChange} />
      )}

      <InvoicePreview pricing={value} projectedSessions={projectedSessions} />
    </div>
  )
}

function NumericInput({
  id,
  value,
  onChange,
  step,
}: {
  id: string
  value: number
  onChange: (n: number) => void
  step?: number
}) {
  return (
    <Input
      id={id}
      type="number"
      step={step ?? 1}
      min={0}
      value={value}
      onChange={(e) => onChange(Number(e.target.value) || 0)}
      className="rounded-none border-fg/30"
    />
  )
}

function RetainerInputs({
  value,
  onChange,
}: {
  value: Extract<ContractPricing, { model: PricingModel.RETAINER }>
  onChange: (p: ContractPricing) => void
}) {
  return (
    <div className="grid gap-4 sm:grid-cols-3">
      <FormField label="Monthly fee" htmlFor="monthly_fee">
        <NumericInput
          id="monthly_fee"
          value={value.monthly_fee}
          onChange={(n) => onChange({ ...value, monthly_fee: n })}
        />
      </FormField>
      <FormField label="Session cap" htmlFor="session_cap">
        <NumericInput
          id="session_cap"
          value={value.session_cap ?? 0}
          onChange={(n) => onChange({ ...value, session_cap: n || null })}
        />
      </FormField>
      <FormField label="Overflow rate" htmlFor="overflow_rate">
        <NumericInput
          id="overflow_rate"
          value={value.overflow_rate ?? 0}
          onChange={(n) => onChange({ ...value, overflow_rate: n || null })}
        />
      </FormField>
    </div>
  )
}

function FrameworkInputs({
  value,
  onChange,
}: {
  value: Extract<ContractPricing, { model: PricingModel.FRAMEWORK }>
  onChange: (p: ContractPricing) => void
}) {
  const drawdownPct =
    value.deposit > 0
      ? Math.max(0, Math.min(100, Math.round((value.drawdown_balance / value.deposit) * 100)))
      : 0
  return (
    <div className="space-y-4">
      <div className="grid gap-4 sm:grid-cols-3">
        <FormField label="Deposit" htmlFor="deposit">
          <NumericInput
            id="deposit"
            value={value.deposit}
            onChange={(n) => onChange({ ...value, deposit: n })}
          />
        </FormField>
        <FormField label="Drawdown balance" htmlFor="drawdown_balance">
          <NumericInput
            id="drawdown_balance"
            value={value.drawdown_balance}
            onChange={(n) => onChange({ ...value, drawdown_balance: n })}
          />
        </FormField>
        <FormField label="Unit rate" htmlFor="unit_rate">
          <NumericInput
            id="unit_rate"
            value={value.unit_rate}
            onChange={(n) => onChange({ ...value, unit_rate: n })}
          />
        </FormField>
      </div>
      <div className="border border-fg/20 bg-surface/30 p-3" aria-label="Framework deposit drawdown">
        <p className="text-xs uppercase tracking-wide text-fg/60">Deposit drawdown</p>
        <div className="mt-2 h-3 w-full bg-white border border-fg/15">
          <div
            className="h-full bg-primary"
            style={{ width: `${drawdownPct}%` }}
            aria-hidden
          />
        </div>
        <p className="mt-2 text-xs text-fg/70">
          {value.drawdown_balance.toFixed(2)} of {value.deposit.toFixed(2)} remaining ({drawdownPct}%)
        </p>
      </div>
    </div>
  )
}

function FFSInputs({
  value,
  onChange,
}: {
  value: Extract<ContractPricing, { model: PricingModel.FFS }>
  onChange: (p: ContractPricing) => void
}) {
  return (
    <FormField label="Unit rate" htmlFor="unit_rate">
      <NumericInput
        id="unit_rate"
        value={value.unit_rate}
        onChange={(n) => onChange({ ...value, unit_rate: n })}
      />
    </FormField>
  )
}

function AdminUtilisationInputs({
  value,
  onChange,
}: {
  value: Extract<ContractPricing, { model: PricingModel.ADMIN_UTILISATION }>
  onChange: (p: ContractPricing) => void
}) {
  const belowFloor = value.monthly_admin_fee < value.admin_floor
  return (
    <div className="space-y-4">
      <div className="grid gap-4 sm:grid-cols-3">
        <FormField label="Monthly admin fee" htmlFor="monthly_admin_fee">
          <NumericInput
            id="monthly_admin_fee"
            value={value.monthly_admin_fee}
            onChange={(n) => onChange({ ...value, monthly_admin_fee: n })}
          />
        </FormField>
        <FormField label="Admin floor" htmlFor="admin_floor">
          <NumericInput
            id="admin_floor"
            value={value.admin_floor}
            onChange={(n) => onChange({ ...value, admin_floor: n })}
          />
        </FormField>
        <FormField label="Utilisation rate" htmlFor="utilisation_rate">
          <NumericInput
            id="utilisation_rate"
            value={value.utilisation_rate}
            onChange={(n) => onChange({ ...value, utilisation_rate: n })}
          />
        </FormField>
      </div>
      {belowFloor && value.admin_floor > 0 && (
        <p
          role="alert"
          className="border border-danger/40 bg-danger-soft/30 px-3 py-2 text-sm text-danger"
        >
          Admin fee is below the floor of {value.admin_floor.toFixed(2)} — pricing requires approval before activation.
        </p>
      )}
    </div>
  )
}

function ValueAddInputs({
  value,
  onChange,
}: {
  value: Extract<ContractPricing, { model: PricingModel.VALUE_ADD }>
  onChange: (p: ContractPricing) => void
}) {
  const [draft, setDraft] = useState("")
  const addService = () => {
    const trimmed = draft.trim()
    if (!trimmed) return
    if (value.bundled_services.includes(trimmed)) return
    onChange({ ...value, bundled_services: [...value.bundled_services, trimmed] })
    setDraft("")
  }
  const removeService = (svc: string) => {
    onChange({
      ...value,
      bundled_services: value.bundled_services.filter((s) => s !== svc),
    })
  }
  return (
    <div className="space-y-4">
      <FormField label="Monthly fee" htmlFor="va_monthly_fee">
        <NumericInput
          id="va_monthly_fee"
          value={value.monthly_fee}
          onChange={(n) => onChange({ ...value, monthly_fee: n })}
        />
      </FormField>
      <FormField label="Bundled services" htmlFor="va_service">
        <div className="flex gap-2">
          <Input
            id="va_service"
            value={draft}
            onChange={(e) => setDraft(e.target.value)}
            placeholder="e.g. CISM, Reports"
            className="rounded-none border-fg/30"
            onKeyDown={(e) => {
              if (e.key === "Enter") {
                e.preventDefault()
                addService()
              }
            }}
          />
          <Button
            type="button"
            variant="outline"
            size="sm"
            onClick={addService}
            className="rounded-none border-fg/30 bg-white text-sm text-fg hover:bg-surface/50"
          >
            Add
          </Button>
        </div>
      </FormField>
      {value.bundled_services.length > 0 && (
        <ul className="flex flex-wrap gap-2">
          {value.bundled_services.map((svc) => (
            <li
              key={svc}
              className="inline-flex items-center gap-1 border border-fg/20 bg-surface px-2 py-0.5 text-xs text-fg"
            >
              {svc}
              <Button
                type="button"
                variant="ghost"
                size="sm"
                onClick={() => removeService(svc)}
                aria-label={`Remove ${svc}`}
                className="ml-1 h-auto p-0 text-fg/60 hover:text-fg"
              >
                ×
              </Button>
            </li>
          ))}
        </ul>
      )}
    </div>
  )
}

function InvoicePreview({
  pricing,
  projectedSessions,
}: {
  pricing: ContractPricing
  projectedSessions: number
}) {
  const stable = useMemo(() => JSON.stringify(pricing), [pricing])
  const query = useQuery({
    queryKey: ["pricing", "preview", stable, projectedSessions],
    queryFn: () => pricingApi.preview(pricing, { projected_sessions: projectedSessions }),
    staleTime: 0,
  })
  const lines: InvoiceLinePreview[] = query.data ?? []
  const total = lines.reduce((s, l) => s + l.subtotal, 0)
  const [debouncedReady, setDebouncedReady] = useState(false)
  useEffect(() => {
    const id = setTimeout(() => setDebouncedReady(true), 50)
    return () => clearTimeout(id)
  }, [stable])

  return (
    <section
      aria-label="Invoice preview"
      className="border border-fg/20 bg-white p-4"
    >
      <h3 className="text-sm font-semibold text-fg">Invoice preview</h3>
      <p className="mt-1 text-xs text-fg/60">
        Projected at {projectedSessions} sessions/month.
      </p>
      {!debouncedReady || query.isPending ? (
        <p className="mt-3 text-sm text-fg/60">Calculating…</p>
      ) : (
        <Table className="mt-3 text-sm">
          <TableHeader>
            <TableRow className="border-b border-fg/20 text-left text-xs uppercase text-fg/60">
              <TableHead className="py-2 pr-3 font-medium">Line</TableHead>
              <TableHead className="py-2 pr-3 font-medium">Qty</TableHead>
              <TableHead className="py-2 pr-3 font-medium">Unit</TableHead>
              <TableHead className="py-2 pr-3 font-medium">Rate</TableHead>
              <TableHead className="py-2 text-right font-medium">Subtotal</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {lines.map((l, i) => (
              <TableRow key={`${l.label}-${i}`} className="border-b border-fg/10 align-top">
                <TableCell className="py-2 pr-3 text-fg">
                  {l.label}
                  {l.note && <p className="mt-1 text-xs text-danger">{l.note}</p>}
                </TableCell>
                <TableCell className="py-2 pr-3 text-fg">{l.quantity}</TableCell>
                <TableCell className="py-2 pr-3 text-fg/70">{l.unit}</TableCell>
                <TableCell className="py-2 pr-3 text-fg">{l.unit_rate.toFixed(2)}</TableCell>
                <TableCell className="py-2 text-right text-fg">{l.subtotal.toFixed(2)}</TableCell>
              </TableRow>
            ))}
            <TableRow>
              <TableCell colSpan={4} className="py-2 pr-3 text-right text-xs uppercase text-fg/60">
                Total
              </TableCell>
              <TableCell className="py-2 text-right text-sm font-semibold text-fg">
                {total.toFixed(2)}
              </TableCell>
            </TableRow>
          </TableBody>
        </Table>
      )}
    </section>
  )
}
