import { useQuery } from "@tanstack/react-query"
import { Link } from "@tanstack/react-router"
import { ChevronRight, Users } from "lucide-react"

import { personsApi } from "@/api/endpoints/persons"
import { Panel } from "@/components/common/Panel"
import { Button } from "@/components/ui/button"
import { Skeleton } from "@/components/ui/skeleton"
import { cn } from "@/lib/utils"
import { PersonType } from "@/types/enums"

interface ClientStaffSummaryCardProps {
  clientId: string
  className?: string
}

export function ClientStaffSummaryCard({ clientId, className }: ClientStaffSummaryCardProps) {
  const peopleQuery = useQuery({
    queryKey: ["persons", "client-summary", clientId],
    queryFn: async () => {
      const [all, employees, dependents] = await Promise.all([
        personsApi.list({ client_id: clientId, limit: 1 }),
        personsApi.list({ client_id: clientId, person_type: PersonType.CLIENT_EMPLOYEE, limit: 1 }),
        personsApi.list({ client_id: clientId, person_type: PersonType.DEPENDENT, limit: 1 }),
      ])
      return {
        total: all.total,
        staff: employees.total,
        dependents: dependents.total,
      }
    },
  })

  const loading = peopleQuery.isPending
  const total = peopleQuery.data?.total ?? 0
  const staff = peopleQuery.data?.staff ?? 0
  const dependents = peopleQuery.data?.dependents ?? 0
  const other = Math.max(0, total - staff - dependents)

  return (
    <Panel
      icon={Users}
      title="Staff & people"
      action={
        <Link
          to="/persons"
          search={{ client_id: clientId }}
          className="-mr-1 inline-flex h-7 items-center gap-0.5 rounded-sm px-2 text-xs text-fg/60 hover:bg-surface-hover hover:text-fg"
        >
          View details
          <ChevronRight className="size-3" />
        </Link>
      }
      className={className}
    >
      {loading ? (
        <div className="grid gap-2">
          <Skeleton className="h-7 w-16" />
          <Skeleton className="h-3 w-48" />
          <Skeleton className="h-3.5 w-full" />
          <Skeleton className="h-3.5 w-full" />
        </div>
      ) : peopleQuery.isError ? (
        <div className="grid gap-2 text-sm text-fg/60">
          <p>People data could not be loaded.</p>
          <Button variant="outline" size="sm" onClick={() => void peopleQuery.refetch()}>
            Retry
          </Button>
        </div>
      ) : (
        <div className="grid gap-3">
          <div>
            <div className="text-2xl font-semibold tabular-nums text-fg">{total}</div>
            <p className="text-xs text-fg/60">Total people linked to this client</p>
          </div>
          <div className="grid grid-cols-2 gap-x-4 gap-y-1 border-t border-fg/8 pt-2 text-xs">
            <Row label="Employees" value={staff} />
            <Row label="Dependents" value={dependents} />
            {other > 0 ? <Row label="Other" value={other} className="col-span-2" /> : null}
          </div>
        </div>
      )}
    </Panel>
  )
}

function Row({ label, value, className }: { label: string; value: number; className?: string }) {
  return (
    <div className={cn("flex justify-between py-1", className)}>
      <span className="text-fg/60">{label}</span>
      <span className="font-medium tabular-nums text-fg">{value}</span>
    </div>
  )
}
