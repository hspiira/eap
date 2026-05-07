import { useEffect, useState } from "react"

import { Link } from "@tanstack/react-router"
import { ChevronRight } from "lucide-react"

import { personsApi } from "@/api/endpoints/persons"
import { Skeleton } from "@/components/ui/skeleton"
import { cn } from "@/lib/utils"
import type { Person } from "@/types/entities"
import { PersonType } from "@/types/enums"

const skeletonClass = "rounded-none bg-[#5A626A]/15"

interface ClientStaffSummaryCardProps {
  clientId: string
  className?: string
}

export function ClientStaffSummaryCard({ clientId, className }: ClientStaffSummaryCardProps) {
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

  const staff = persons.filter((p) => p.person_type === PersonType.CLIENT_EMPLOYEE)
  const dependents = persons.filter((p) => p.person_type === PersonType.DEPENDENT)
  const other = persons.filter(
    (p) =>
      p.person_type !== PersonType.CLIENT_EMPLOYEE && p.person_type !== PersonType.DEPENDENT
  )
  const total = persons.length

  return (
    <div
      className={cn(
        "flex flex-col border border-[#5A626A]/20 bg-white p-4 rounded-none",
        className
      )}
    >
      <div className="mb-3 flex items-center justify-between">
        <h3 className="text-sm font-semibold text-[#5A626A]">Staff & people</h3>
        <Link
          to="/persons"
          className="text-xs text-[#5A626A]/70 hover:text-natural flex items-center gap-0.5"
        >
          View details <ChevronRight className="inline h-3 w-3" />
        </Link>
      </div>
      {loading ? (
        <div className="space-y-3">
          <Skeleton className={cn(skeletonClass, "h-8 w-16")} />
          <Skeleton className={cn(skeletonClass, "h-4 w-full")} />
          <Skeleton className={cn(skeletonClass, "h-4 w-full")} />
          <Skeleton className={cn(skeletonClass, "h-4 w-full")} />
        </div>
      ) : (
        <>
          <div className="mb-3 text-2xl font-bold text-[#5A626A]">{total}</div>
          <p className="mb-3 text-xs text-[#5A626A]/70">Total people linked to this client</p>
          <div className="grid grid-cols-2 gap-2 border-t border-[#5A626A]/15 pt-3 text-xs">
            <div className="flex justify-between py-1">
              <span className="text-[#5A626A]/80">Staff (employees)</span>
              <span className="font-medium text-[#5A626A]">{staff.length}</span>
            </div>
            <div className="flex justify-between py-1">
              <span className="text-[#5A626A]/80">Dependents / relatives</span>
              <span className="font-medium text-[#5A626A]">{dependents.length}</span>
            </div>
            {other.length > 0 && (
              <div className="flex justify-between py-1 col-span-2">
                <span className="text-[#5A626A]/80">Other</span>
                <span className="font-medium text-[#5A626A]">{other.length}</span>
              </div>
            )}
          </div>
        </>
      )}
    </div>
  )
}
