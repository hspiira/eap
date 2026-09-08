import { useQuery } from "@tanstack/react-query"
import { RotateCw } from "lucide-react"

import { servicesApi } from "@/api/endpoints/services"
import { utilisationApi } from "@/api/endpoints/utilisation"
import { ROW_BORDER, TABLE_HEAD } from "@/components/common/tableStyles"
import { Button } from "@/components/ui/button"
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"
import { normalizeErrorMessage } from "@/lib/errors"
import { formatDay } from "@/lib/format"
import { getStatusLabel } from "@/utils/statusColors"

/** The services list caps `limit` at 100; asking for more is rejected outright. */
const SERVICE_PAGE = 100

/**
 * Billable usage recorded against one contract.
 *
 * `service_code` carries a service id in the records this reads, so an
 * unresolved one is printed as a dash rather than raw: an internal id on a
 * billing page reads as data the user is meant to act on.
 */
function useContractUtilisation(contractId: string) {
  return useQuery({
    queryKey: ["contracts", contractId, "utilisation"],
    queryFn: async () => {
      const [events, services] = await Promise.all([
        utilisationApi.byContract(contractId),
        servicesApi.list({ limit: SERVICE_PAGE }),
      ])
      const names = new Map((services.items ?? []).map((service) => [service.id, service.name]))
      return events.map((event) => ({
        event,
        serviceName: event.service_code ? (names.get(event.service_code) ?? null) : null,
      }))
    },
  })
}

export function ContractUtilisationPanel({ contractId }: { contractId: string }) {
  const query = useContractUtilisation(contractId)
  const rows = query.data ?? []
  const units = rows.reduce((total, { event }) => total + event.units, 0)

  return (
    <section className="space-y-2">
      <div className="flex items-baseline justify-between gap-3">
        <h3 className="text-xs font-semibold tracking-wide text-fg-muted">Recorded usage</h3>
        {rows.length > 0 && (
          <p className="text-xs text-fg-muted">
            {rows.length} event{rows.length === 1 ? "" : "s"} · {units} unit
            {units === 1 ? "" : "s"}
          </p>
        )}
      </div>
      <UtilisationBody query={query} rows={rows} />
    </section>
  )
}

function UtilisationBody({
  query,
  rows,
}: {
  query: ReturnType<typeof useContractUtilisation>
  rows: {
    event: { id: string; occurred_on: string; event_type: string; units: number }
    serviceName: string | null
  }[]
}) {
  if (query.isPending)
    return (
      <p role="status" className="text-sm text-fg-muted">
        Loading usage…
      </p>
    )
  if (query.isError)
    return (
      <div role="alert" className="space-y-2 text-sm">
        <p className="text-danger-fg">
          {normalizeErrorMessage(query.error, "Could not load usage")}
        </p>
        <Button
          type="button"
          size="sm"
          variant="outline"
          className="gap-1.5"
          onClick={() => void query.refetch()}
        >
          <RotateCw className="size-3.5" />
          Try again
        </Button>
      </div>
    )
  if (!rows.length)
    return <p className="text-sm text-fg-muted">Nothing billable recorded against this term yet.</p>
  return (
    <div className="overflow-hidden border border-fg/10 bg-surface">
      <Table className="w-full text-sm">
        <TableHeader className={TABLE_HEAD}>
          <TableRow className={`hover:bg-transparent ${ROW_BORDER}`}>
            <TableHead className="text-fg/65">Date</TableHead>
            <TableHead className="text-fg/65">Activity</TableHead>
            <TableHead className="text-fg/65">Service</TableHead>
            <TableHead className="text-right text-fg/65">Units</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {rows.map(({ event, serviceName }) => (
            <TableRow key={event.id} className={`h-9 ${ROW_BORDER}`}>
              <TableCell className="whitespace-nowrap text-xs text-fg/70">
                {formatDay(event.occurred_on)}
              </TableCell>
              <TableCell className="text-xs text-fg">{getStatusLabel(event.event_type)}</TableCell>
              <TableCell className="max-w-[16rem] truncate text-xs text-fg/70">
                {serviceName ?? <span className="text-fg-subtle">-</span>}
              </TableCell>
              <TableCell className="text-right tabular-nums text-xs text-fg/70">
                {event.units}
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </div>
  )
}
