import { useEffect, useState } from "react"

import { Link } from "@tanstack/react-router"
import { ChevronRight } from "lucide-react"

import { personsApi } from "@/api/endpoints/persons"
import { Button } from "@/components/ui/button"
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"
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
    <Card className={cn("rounded-md", className)}>
      <CardHeader className="flex-row items-center justify-between gap-2 space-y-0 border-b border-border-subtle p-3">
        <CardTitle className="text-sm font-semibold text-fg">
          Staff & people
        </CardTitle>
        <Button
          asChild
          variant="ghost"
          size="sm"
          className="-mr-2 h-7 gap-0.5 px-2 text-xs text-fg-muted"
        >
          <Link to="/persons">
            View details
            <ChevronRight className="size-3" />
          </Link>
        </Button>
      </CardHeader>
      <CardContent className="grid gap-3 p-3">
        {loading ? (
          <div className="grid gap-2">
            <Skeleton className="h-7 w-16" />
            <Skeleton className="h-3 w-48" />
            <Skeleton className="h-3.5 w-full" />
            <Skeleton className="h-3.5 w-full" />
          </div>
        ) : (
          <>
            <div>
              <div className="font-mono text-2xl font-semibold tabular-nums text-fg">
                {total}
              </div>
              <p className="text-xs text-fg-muted">
                Total people linked to this client
              </p>
            </div>
            <div className="grid grid-cols-2 gap-x-4 gap-y-1 border-t border-border-subtle pt-2 text-xs">
              <Row label="Employees" value={staff.length} />
              <Row label="Dependents" value={dependents.length} />
              {other.length > 0 ? (
                <Row label="Other" value={other.length} className="col-span-2" />
              ) : null}
            </div>
          </>
        )}
      </CardContent>
    </Card>
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
      <span className="text-fg-muted">{label}</span>
      <span className="font-mono font-medium tabular-nums text-fg">
        {value}
      </span>
    </div>
  )
}
