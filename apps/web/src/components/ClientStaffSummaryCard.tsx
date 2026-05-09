import { useEffect, useState } from "react"

import { Link } from "@tanstack/react-router"
import { ChevronRight, Users } from "lucide-react"

import { personsApi } from "@/api/endpoints/persons"
import { Panel } from "@/components/common/Panel"
import { Skeleton } from "@/components/ui/skeleton"
import { cn } from "@/lib/utils"
import type { Person } from "@/types/entities"
import { PersonType } from "@/types/enums"

interface ClientStaffSummaryCardProps {
  clientId: string
  className?: string
}

export function ClientStaffSummaryCard({
  clientId,
  className,
}: ClientStaffSummaryCardProps) {
  const [persons, setPersons] = useState<Person[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    setLoading(true)
    personsApi
      .list({ client_id: clientId, limit: 500 })
      .then((res) => setPersons(res.items ?? []))
      .catch(() => setPersons([]))
      .finally(() => setLoading(false))
  }, [clientId])

  const staff = persons.filter(
    (p) => p.person_type === PersonType.CLIENT_EMPLOYEE,
  )
  const dependents = persons.filter(
    (p) => p.person_type === PersonType.DEPENDENT,
  )
  const other = persons.filter(
    (p) =>
      p.person_type !== PersonType.CLIENT_EMPLOYEE &&
      p.person_type !== PersonType.DEPENDENT,
  )
  const total = persons.length

  return (
    <Panel
      icon={Users}
      title="Staff & people"
      action={
        <Link
          to="/persons"
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
      ) : (
        <div className="grid gap-3">
          <div>
            <div className="font-mono text-2xl font-semibold tabular-nums text-fg">
              {total}
            </div>
            <p className="text-xs text-fg/60">
              Total people linked to this client
            </p>
          </div>
          <div className="grid grid-cols-2 gap-x-4 gap-y-1 border-t border-fg/8 pt-2 text-xs">
            <Row label="Employees" value={staff.length} />
            <Row label="Dependents" value={dependents.length} />
            {other.length > 0 ? (
              <Row label="Other" value={other.length} className="col-span-2" />
            ) : null}
          </div>
        </div>
      )}
    </Panel>
  )
}

function Row({
  label,
  value,
  className,
}: {
  label: string
  value: number
  className?: string
}) {
  return (
    <div className={cn("flex justify-between py-1", className)}>
      <span className="text-fg/60">{label}</span>
      <span className="font-mono font-medium tabular-nums text-fg">{value}</span>
    </div>
  )
}
