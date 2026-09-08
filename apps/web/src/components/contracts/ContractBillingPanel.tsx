import { useState } from "react"

import { useQuery } from "@tanstack/react-query"

import { pricingApi } from "@/api/endpoints/pricing"
import { DetailCard, DetailGrid, DetailRow } from "@/components/common/DetailPrimitives"
import { StatusBadge } from "@/components/common/StatusBadge"
import { ROW_BORDER, TABLE_HEAD } from "@/components/common/tableStyles"
import { ContractUtilisationPanel } from "@/components/contracts/ContractUtilisationPanel"
import { Input } from "@/components/ui/input"
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"
import { normalizeErrorMessage } from "@/lib/errors"
import { formatDay, todayDayKey } from "@/lib/format"
import type { Contract } from "@/types/entities"
import { getStatusLabel } from "@/utils/statusColors"

function money(value: { amount: string; currency: string } | undefined): string {
  if (!value) return "-"
  const amount = Number(value.amount)
  const formatted = Number.isFinite(amount) ? amount.toLocaleString() : value.amount
  return `${value.currency} ${formatted}`
}

/** The window the invoice covers: the current billing period where the contract names one. */
function defaultPeriod(contract: Contract): { from: string; to: string } {
  const to = contract.next_billing_date ?? contract.period?.end_date ?? todayDayKey()
  const from =
    contract.last_billing_date ?? contract.period?.start_date ?? `${to.slice(0, 4)}-01-01`
  return { from, to }
}

/**
 * What this contract owes for a window, priced by the server.
 *
 * The engine is the same one billing uses, so the figure here cannot disagree
 * with the invoice. It is a preview of a period, not a record of one: nothing
 * here is issued or paid.
 */
function InvoicePreviewCard({ contract }: { contract: Contract }) {
  const initial = defaultPeriod(contract)
  const [from, setFrom] = useState(initial.from)
  const [to, setTo] = useState(initial.to)

  const query = useQuery({
    queryKey: ["contracts", contract.id, "invoice-preview", from, to],
    queryFn: () => pricingApi.invoicePreview(contract.id, { period_from: from, period_to: to }),
    enabled: Boolean(from && to && from <= to),
    retry: false,
  })

  return (
    <DetailCard title="Invoice preview">
      <div className="mb-3 flex flex-wrap items-end gap-3">
        <label className="space-y-1">
          <span className="block text-[11px] text-fg-muted">From</span>
          <Input
            type="date"
            value={from}
            onChange={(event) => setFrom(event.target.value)}
            className="h-8 w-40 rounded-none"
          />
        </label>
        <label className="space-y-1">
          <span className="block text-[11px] text-fg-muted">To</span>
          <Input
            type="date"
            value={to}
            onChange={(event) => setTo(event.target.value)}
            className="h-8 w-40 rounded-none"
          />
        </label>
        {from > to ? (
          <p className="text-xs text-danger-fg">The start of the window is after its end.</p>
        ) : null}
      </div>

      {query.isPending && from <= to ? (
        <p className="text-sm text-fg-muted">Pricing this window…</p>
      ) : query.isError ? (
        <p role="alert" className="text-sm text-danger-fg">
          {normalizeErrorMessage(query.error, "Could not price this window")}
        </p>
      ) : query.data ? (
        <>
          <div className="overflow-x-auto border border-fg/10">
            <Table className="w-full text-sm">
              <TableHeader className={TABLE_HEAD}>
                <TableRow className={`hover:bg-transparent ${ROW_BORDER}`}>
                  <TableHead className="text-fg/65">Line</TableHead>
                  <TableHead className="text-right text-fg/65">Qty</TableHead>
                  <TableHead className="text-right text-fg/65">Unit</TableHead>
                  <TableHead className="text-right text-fg/65">Amount</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {query.data.lines.length === 0 ? (
                  <TableRow className={ROW_BORDER}>
                    <TableCell colSpan={4} className="py-3 text-xs text-fg-muted">
                      Nothing billable in this window.
                    </TableCell>
                  </TableRow>
                ) : (
                  query.data.lines.map((line, index) => (
                    <TableRow key={`${line.description}-${index}`} className={`h-9 ${ROW_BORDER}`}>
                      <TableCell className="text-xs text-fg">{line.description}</TableCell>
                      <TableCell className="text-right text-xs tabular-nums text-fg/70">
                        {line.quantity}
                      </TableCell>
                      <TableCell className="text-right text-xs tabular-nums text-fg/70">
                        {money(line.unit_amount)}
                      </TableCell>
                      <TableCell className="text-right text-xs font-medium tabular-nums text-fg">
                        {money(line.total)}
                      </TableCell>
                    </TableRow>
                  ))
                )}
              </TableBody>
            </Table>
          </div>

          <div className="mt-3 flex flex-wrap items-baseline justify-between gap-2 border-t border-fg/10 pt-3">
            <span className="text-xs text-fg-muted">
              {getStatusLabel(query.data.pricing_model)} · {formatDay(query.data.period_from)} to{" "}
              {formatDay(query.data.period_to)}
            </span>
            <span className="text-base font-semibold tabular-nums text-fg">
              {money(query.data.subtotal)}
            </span>
          </div>

          {query.data.notes.length > 0 ? (
            <ul className="mt-2 space-y-0.5">
              {query.data.notes.map((note) => (
                <li key={note} className="text-[11px] text-fg-muted">
                  {note}
                </li>
              ))}
            </ul>
          ) : null}
          <p className="mt-2 text-[11px] text-fg-subtle">
            A preview of what the window prices to. Nothing here is issued or paid.
          </p>
        </>
      ) : null}
    </DetailCard>
  )
}

/** Billing terms, what the period prices to, and the usage behind it. */
export function ContractBillingPanel({ contract }: { contract: Contract }) {
  return (
    <div className="space-y-4">
      <DetailCard title="Billing terms">
        <DetailGrid>
          <DetailRow label="Frequency" value={contract.payment_frequency} />
          <DetailRow
            label="Payment status"
            value={<StatusBadge status={contract.payment_status} />}
          />
          <DetailRow label="Auto-renew" value={contract.is_auto_renew ? "Yes" : "No"} />
          <DetailRow label="Last billed" value={formatDay(contract.last_billing_date)} />
          <DetailRow label="Next billing" value={formatDay(contract.next_billing_date)} />
        </DetailGrid>
      </DetailCard>

      {contract.pricing_model ? (
        <InvoicePreviewCard contract={contract} />
      ) : (
        <DetailCard title="Invoice preview">
          <p className="text-sm text-fg-muted">
            This contract has no pricing configuration, so a window cannot be priced. Set the
            pricing model to see what usage costs.
          </p>
        </DetailCard>
      )}

      <ContractUtilisationPanel contractId={contract.id} />
    </div>
  )
}
