import { Skeleton } from "@/components/ui/skeleton"
import { TableBody, TableCell, TableRow } from "@/components/ui/table"
import { cn } from "@/lib/utils"

const skeletonClass = "rounded-none bg-fg/15"

export function PersonsListSkeleton() {
  return (
    <div className="space-y-3">
      <div className="grid grid-cols-[1.6fr_0.8fr_1fr_0.8fr_0.8fr_0.6fr] gap-3 border-b border-fg/10 bg-surface px-3 py-2">
        {Array.from({ length: 6 }).map((_, i) => (
          <Skeleton key={i} className={cn(skeletonClass, "h-3 w-20")} />
        ))}
      </div>
      <table className="w-full text-sm">
        <TableBody>
          {Array.from({ length: 8 }).map((_, i) => (
            <TableRow key={i} className="border-fg/8">
              <TableCell>
                <div className="flex items-center gap-2.5">
                  <Skeleton className={cn(skeletonClass, "size-6")} />
                  <Skeleton className={cn(skeletonClass, "h-3.5 w-32")} />
                </div>
              </TableCell>
              <TableCell>
                <Skeleton className={cn(skeletonClass, "h-5 w-20")} />
              </TableCell>
              <TableCell>
                <Skeleton className={cn(skeletonClass, "h-3.5 w-28")} />
              </TableCell>
              <TableCell>
                <Skeleton className={cn(skeletonClass, "h-5 w-16")} />
              </TableCell>
              <TableCell>
                <Skeleton className={cn(skeletonClass, "h-3.5 w-32")} />
              </TableCell>
              <TableCell>
                <Skeleton className={cn(skeletonClass, "h-3.5 w-12")} />
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </table>
    </div>
  )
}

export function PersonDetailSkeleton() {
  return (
    <div className="space-y-5">
      <div className="border border-fg/10 bg-surface">
        <div className="flex items-center gap-3 border-b border-fg/10 px-5 py-3">
          <Skeleton className={cn(skeletonClass, "h-9 w-9")} />
          <Skeleton className={cn(skeletonClass, "h-4 w-48")} />
          <Skeleton className={cn(skeletonClass, "h-3.5 w-24")} />
          <Skeleton className={cn(skeletonClass, "h-5 w-16")} />
        </div>
      </div>
      <div className="grid grid-cols-12 gap-5 px-5">
        <div className="col-span-12 lg:col-span-8 space-y-3">
          <Skeleton className={cn(skeletonClass, "h-9 w-72")} />
          <Skeleton className={cn(skeletonClass, "h-32 w-full")} />
          <Skeleton className={cn(skeletonClass, "h-32 w-full")} />
        </div>
        <aside className="col-span-12 lg:col-span-4 space-y-4">
          {Array.from({ length: 4 }).map((_, i) => (
            <Skeleton key={i} className={cn(skeletonClass, "h-24 w-full")} />
          ))}
        </aside>
      </div>
    </div>
  )
}
