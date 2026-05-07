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

const skeletonClass = "rounded-none bg-[#5A626A]/15"

export function IndustriesListSkeleton() {
  const rows = 8

  return (
    <div className="space-y-2">
      <div className="rounded-none border border-[#5A626A]/30">
        <Table>
          <TableHeader>
            <TableRow className="border-[#5A626A]/20 hover:bg-transparent">
              <TableHead className="text-[#5A626A]">Name</TableHead>
              <TableHead className="text-[#5A626A]">Code</TableHead>
              <TableHead className="text-[#5A626A]">Level</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {Array.from({ length: rows }).map((_, i) => (
              <TableRow key={i} className="border-[#5A626A]/15">
                <TableCell className="py-1.5">
                  <Skeleton className={cn(skeletonClass, "h-3.5 w-full max-w-[180px]")} />
                </TableCell>
                <TableCell className="py-1.5">
                  <Skeleton className={cn(skeletonClass, "h-3.5 w-16")} />
                </TableCell>
                <TableCell className="py-1.5">
                  <Skeleton className={cn(skeletonClass, "h-3.5 w-8")} />
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
