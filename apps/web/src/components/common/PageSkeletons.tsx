import { Skeleton } from "@/components/ui/skeleton"
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"
import { cn } from "@/lib/utils"

const skeletonClass = "rounded-none bg-fg/15"

export type ColSpec = string | { width: string; isBadge?: boolean }

interface TableSkeletonProps {
  cols: number | ColSpec[]
  rows?: number
  headers?: string[]
  withFilters?: boolean
  withPagination?: boolean
  className?: string
}

function resolveCols(cols: number | ColSpec[]): ColSpec[] {
  if (typeof cols === "number") return Array.from({ length: cols }, () => ({ width: "w-24" }))
  return cols
}

export function TableSkeleton({
  cols,
  rows = 8,
  headers,
  withFilters = false,
  withPagination = false,
  className,
}: TableSkeletonProps) {
  const colSpecs = resolveCols(cols)

  return (
    <div className={cn("space-y-3", className)}>
      {withFilters ? (
        <div className="flex flex-nowrap items-center gap-2">
          <Skeleton className={cn(skeletonClass, "h-9 flex-1 max-w-md")} />
          <Skeleton className={cn(skeletonClass, "h-9 w-20")} />
          <Skeleton className={cn(skeletonClass, "h-9 w-[180px]")} />
          <Skeleton className={cn(skeletonClass, "h-9 w-20")} />
          <div className="flex-1 min-w-2" />
          <Skeleton className={cn(skeletonClass, "h-9 w-20")} />
          <Skeleton className={cn(skeletonClass, "h-9 w-24")} />
          <Skeleton className={cn(skeletonClass, "h-9 w-28")} />
        </div>
      ) : null}
      <div className={cn(headers ? "rounded-none border border-fg/30 overflow-hidden" : "")}>
        <Table>
          {headers ? (
            <TableHeader>
              <TableRow className="border-fg/20 hover:bg-transparent">
                {headers.map((h) => (
                  <TableHead key={h} className="text-fg">{h}</TableHead>
                ))}
              </TableRow>
            </TableHeader>
          ) : null}
          <TableBody>
            {Array.from({ length: rows }).map((_, r) => (
              <TableRow key={r} className="border-fg/8">
                {colSpecs.map((spec, c) => {
                  const w = typeof spec === "string" ? spec : spec.width
                  const h = typeof spec === "object" && spec.isBadge ? "h-5" : "h-3.5"
                  return (
                    <TableCell key={c} className="py-1.5">
                      <Skeleton className={cn(skeletonClass, h, w)} />
                    </TableCell>
                  )
                })}
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </div>
      {withPagination ? (
        <div className="flex items-center justify-between pt-1">
          <Skeleton className={cn(skeletonClass, "h-8 w-24")} />
          <div className="flex gap-2">
            <Skeleton className={cn(skeletonClass, "h-8 w-8")} />
            <Skeleton className={cn(skeletonClass, "h-8 w-8")} />
            <Skeleton className={cn(skeletonClass, "h-8 w-8")} />
          </div>
        </div>
      ) : null}
    </div>
  )
}

interface DetailSkeletonProps {
  withHero?: boolean
  mainPanels?: number
  railPanels?: number
  className?: string
}

export function DetailSkeleton({
  withHero = true,
  mainPanels = 2,
  railPanels = 4,
  className,
}: DetailSkeletonProps) {
  return (
    <div className={cn("space-y-5", className)}>
      {withHero ? (
        <div className="border border-fg/10 bg-surface">
          <div className="flex items-center gap-3 border-b border-fg/10 px-5 py-3">
            <Skeleton className={cn(skeletonClass, "h-9 w-9")} />
            <Skeleton className={cn(skeletonClass, "h-4 w-48")} />
            <Skeleton className={cn(skeletonClass, "h-3.5 w-24")} />
            <Skeleton className={cn(skeletonClass, "h-5 w-16")} />
          </div>
        </div>
      ) : null}
      <div className="grid grid-cols-12 gap-5 px-5">
        <div className="col-span-12 lg:col-span-8 space-y-3">
          <Skeleton className={cn(skeletonClass, "h-9 w-72")} />
          {Array.from({ length: mainPanels }).map((_, i) => (
            <Skeleton key={i} className={cn(skeletonClass, "h-32 w-full")} />
          ))}
        </div>
        <aside className="col-span-12 lg:col-span-4 space-y-4">
          {Array.from({ length: railPanels }).map((_, i) => (
            <Skeleton key={i} className={cn(skeletonClass, "h-24 w-full")} />
          ))}
        </aside>
      </div>
    </div>
  )
}
