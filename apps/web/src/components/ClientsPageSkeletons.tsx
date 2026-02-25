import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"
import { Skeleton } from "@/components/ui/skeleton"
import { cn } from "@/lib/utils"

const skeletonClass = "rounded-none bg-[#5A626A]/15"

export function ClientsListSkeleton() {
  const rows = 8

  return (
    <div className="space-y-2">
      <div className="rounded-none border border-[#5A626A]/30 bg-white">
        <Table>
          <TableHeader>
            <TableRow className="border-[#5A626A]/20 hover:bg-transparent">
              <TableHead className="text-[#5A626A]">Name</TableHead>
              <TableHead className="text-[#5A626A]">Code</TableHead>
              <TableHead className="text-[#5A626A]">Status</TableHead>
              <TableHead className="text-[#5A626A]">Contact</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {Array.from({ length: rows }).map((_, i) => (
              <TableRow key={i} className="border-[#5A626A]/15">
                <TableCell className="py-1.5">
                  <Skeleton className={cn(skeletonClass, "h-3.5 w-full max-w-[140px]")} />
                </TableCell>
                <TableCell className="py-1.5">
                  <Skeleton className={cn(skeletonClass, "h-3.5 w-12")} />
                </TableCell>
                <TableCell className="py-1.5">
                  <Skeleton className={cn(skeletonClass, "h-4 w-16")} />
                </TableCell>
                <TableCell className="py-1.5">
                  <Skeleton className={cn(skeletonClass, "h-3.5 w-full max-w-[180px]")} />
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </div>
      <div className="flex items-center justify-between pt-1">
        <Skeleton className={cn(skeletonClass, "h-8 w-24")} />
        <div className="flex gap-2">
          <Skeleton className={cn(skeletonClass, "h-8 w-8")} />
          <Skeleton className={cn(skeletonClass, "h-8 w-8")} />
          <Skeleton className={cn(skeletonClass, "h-8 w-8")} />
        </div>
      </div>
    </div>
  )
}

export function ClientDetailSkeleton() {
  return (
    <div className="border border-[#5A626A]/30 rounded-none bg-[#fafafa] overflow-hidden">
      <div className="px-6 py-5 border-b border-[#5A626A]/20 bg-[#f5f5f5]">
        <Skeleton className={cn(skeletonClass, "h-7 w-48")} />
        <Skeleton className={cn(skeletonClass, "h-4 w-20 mt-2")} />
      </div>
      <dl className="grid gap-4 sm:grid-cols-2 px-6 py-5">
        {[1, 2, 3, 4].map((i) => (
          <div key={i}>
            <Skeleton className={cn(skeletonClass, "h-3 w-14 mb-2")} />
            <Skeleton className={cn(skeletonClass, "h-4 w-32")} />
          </div>
        ))}
      </dl>
      <div className="px-6 py-5 border-t border-[#5A626A]/20 bg-[#f5f5f5]">
        <Skeleton className={cn(skeletonClass, "h-4 w-14 mb-3")} />
        <div className="flex flex-wrap gap-2">
          <Skeleton className={cn(skeletonClass, "h-9 w-24")} />
          <Skeleton className={cn(skeletonClass, "h-9 w-28")} />
        </div>
      </div>
    </div>
  )
}
