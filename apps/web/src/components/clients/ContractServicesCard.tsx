import { useQuery } from "@tanstack/react-query"
import { Link } from "@tanstack/react-router"
import { ExternalLink, FileCheck, RotateCw } from "lucide-react"

import { serviceAssignmentsApi } from "@/api/endpoints/service-assignments"
import { servicesApi } from "@/api/endpoints/services"
import { StatusBadge } from "@/components/common/StatusBadge"
import { ContractAttachments } from "@/components/contracts/ContractAttachments"
import { Button } from "@/components/ui/button"
import { contractLabel } from "@/lib/display"
import { normalizeErrorMessage } from "@/lib/errors"
import { entityListKey } from "@/lib/queries"
import type { Contract } from "@/types/entities"

/** The list endpoint caps limit at 100, which is far above any real contract. */
const ASSIGNMENT_PAGE = 100

function useContractServices(contractId: string) {
  return useQuery({
    queryKey: entityListKey("service-assignments", {
      contract_id: contractId,
      limit: ASSIGNMENT_PAGE,
    }),
    queryFn: async () => {
      const { items } = await serviceAssignmentsApi.list({
        contract_id: contractId,
        limit: ASSIGNMENT_PAGE,
      })
      const services = new Map(
        await Promise.all(
          [...new Set(items.map((item) => item.service_id))].map(
            async (id) => [id, await servicesApi.getById(id)] as const,
          ),
        ),
      )
      return items.map((assignment) => ({
        assignment,
        service: services.get(assignment.service_id)!,
      }))
    },
  })
}

export function ContractServicesCard({ contract }: { contract: Contract }) {
  const query = useContractServices(contract.id)
  return (
    <div className="flex min-h-0 flex-col overflow-hidden border border-fg/10 bg-surface lg:max-h-[calc(100dvh-8rem)]">
      <header className="flex items-start gap-3 border-b border-fg/10 px-4 py-3">
        <span
          aria-hidden
          className="grid size-8 shrink-0 place-items-center bg-primary/10 text-primary"
        >
          <FileCheck className="size-4" />
        </span>
        <div className="min-w-0 flex-1">
          <h3 className="truncate text-sm font-semibold leading-tight text-fg">
            {contractLabel(contract)}
          </h3>
          <p className="mt-1 text-[11px] text-fg-muted">
            {query.data ? `${query.data.length} services` : "Services in this contract"}
          </p>
        </div>
        <StatusBadge status={contract.status} size="sm" />
      </header>

      <div className="flex min-h-0 flex-1 flex-col gap-4 overflow-y-auto overscroll-contain p-4">
        <ContractServicesList query={query} />
        <Link
          to="/contracts/$contractId"
          params={{ contractId: contract.id }}
          search={{ tab: "services" }}
          className="inline-flex items-center gap-1.5 text-sm font-medium text-primary hover:underline"
        >
          Manage services
          <ExternalLink className="size-3.5" />
        </Link>
        <ContractAttachments contractId={contract.id} />
      </div>
    </div>
  )
}

function ContractServicesList({ query }: { query: ReturnType<typeof useContractServices> }) {
  if (query.isPending)
    return (
      <p role="status" className="text-sm text-fg-muted">
        Loading services…
      </p>
    )
  if (query.isError)
    return (
      <div role="alert" className="space-y-2 text-sm">
        <p className="text-danger-fg">
          {normalizeErrorMessage(query.error, "Could not load services")}
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
  if (!query.data.length)
    return (
      <p className="border border-dashed border-fg/15 p-6 text-center text-sm text-fg-muted">
        No services assigned to this contract yet.
      </p>
    )
  return (
    <ul className="divide-y divide-fg/10 border border-fg/10">
      {query.data.map(({ assignment, service }) => (
        <li key={assignment.id} className="flex items-start justify-between gap-3 px-3 py-2.5">
          <div className="min-w-0">
            <Link
              to="/services/$serviceId"
              params={{ serviceId: service.id }}
              className="text-sm font-medium text-primary hover:underline"
            >
              {service.name}
            </Link>
            {assignment.notes && <p className="mt-0.5 text-xs text-fg-muted">{assignment.notes}</p>}
          </div>
          <StatusBadge status={assignment.status} size="sm" />
        </li>
      ))}
    </ul>
  )
}
