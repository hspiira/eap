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

export function ClientsListSkeleton() {
  const rows = 8

  return (
    <div className="space-y-4">
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
      <div className="rounded-none border border-fg/20 bg-white overflow-hidden">
        <Table>
          <TableHeader>
            <TableRow className="border-fg/15 hover:bg-transparent [&>th]:h-9 [&>th]:py-2 [&>th]:px-3 [&>th]:text-xs [&>th]:font-medium [&>th]:uppercase [&>th]:text-fg [&>th]:bg-surface/30">
              <TableHead>Name</TableHead>
              <TableHead>Code</TableHead>
              <TableHead>Status</TableHead>
              <TableHead>Contact</TableHead>
              <TableHead>Operation</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {Array.from({ length: rows }).map((_, i) => (
              <TableRow
                key={i}
                className="border-fg/10 [&>td]:py-2 [&>td]:px-3 [&>td]:text-sm"
              >
                <TableCell>
                  <Skeleton className={cn(skeletonClass, "h-3.5 w-full max-w-[140px]")} />
                </TableCell>
                <TableCell>
                  <Skeleton className={cn(skeletonClass, "h-3.5 w-12")} />
                </TableCell>
                <TableCell>
                  <Skeleton className={cn(skeletonClass, "h-5 w-16")} />
                </TableCell>
                <TableCell>
                  <Skeleton className={cn(skeletonClass, "h-3.5 w-full max-w-[180px]")} />
                </TableCell>
                <TableCell>
                  <Skeleton className={cn(skeletonClass, "h-4 w-4")} />
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </div>
      <div className="flex items-center justify-between">
        <Skeleton className={cn(skeletonClass, "h-4 w-24")} />
        <div className="flex gap-1">
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
    <div className="space-y-4">
      <div className="border border-fg/30 rounded-none bg-neutral-50 overflow-hidden">
        <div className="px-6 py-5 border-b border-fg/20 bg-surface/30">
          <div className="flex items-center gap-2">
            <Skeleton className={cn(skeletonClass, "h-7 w-48")} />
            <Skeleton className={cn(skeletonClass, "h-5 w-16")} />
          </div>
          <Skeleton className={cn(skeletonClass, "h-4 w-20 mt-2")} />
        </div>
        <div className="px-6 py-5">
          <Skeleton className={cn(skeletonClass, "h-4 w-24 mb-3")} />
          <dl className="grid gap-3 sm:grid-cols-2">
            {[1, 2, 3, 4].map((i) => (
              <div key={i}>
                <Skeleton className={cn(skeletonClass, "h-3 w-14 mb-1.5")} />
                <Skeleton className={cn(skeletonClass, "h-4 w-32")} />
              </div>
            ))}
          </dl>
        </div>
      </div>

      <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
        <div className="border border-fg/30 rounded-none bg-neutral-50 overflow-hidden">
          <div className="flex items-center gap-2 border-b border-fg/20 px-4 py-3 bg-surface/20">
            <Skeleton className={cn(skeletonClass, "h-4 w-4")} />
            <Skeleton className={cn(skeletonClass, "h-4 w-16")} />
          </div>
          <div className="px-4 py-3 space-y-2">
            <Skeleton className={cn(skeletonClass, "h-10 w-full")} />
            <Skeleton className={cn(skeletonClass, "h-10 w-full")} />
          </div>
        </div>
        <div className="border border-fg/30 rounded-none bg-neutral-50 overflow-hidden">
          <div className="px-4 py-3 border-b border-fg/20">
            <Skeleton className={cn(skeletonClass, "h-4 w-20")} />
          </div>
          <div className="px-4 py-3 space-y-2">
            <Skeleton className={cn(skeletonClass, "h-14 w-full")} />
            <Skeleton className={cn(skeletonClass, "h-14 w-full")} />
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 gap-4 lg:grid-cols-3">
        <div className="lg:col-span-2 border border-fg/30 rounded-none bg-neutral-50 overflow-hidden">
          <div className="px-4 py-3 border-b border-fg/20">
            <Skeleton className={cn(skeletonClass, "h-4 w-20")} />
          </div>
          <div className="divide-y divide-ink/15 px-4">
            {[1, 2, 3, 4].map((i) => (
              <div key={i} className="flex gap-3 py-3">
                <Skeleton className={cn(skeletonClass, "h-9 w-9 shrink-0")} />
                <div className="min-w-0 flex-1 space-y-1">
                  <Skeleton className={cn(skeletonClass, "h-4 w-32")} />
                  <Skeleton className={cn(skeletonClass, "h-3 w-full max-w-[200px]")} />
                  <Skeleton className={cn(skeletonClass, "h-3 w-16")} />
                </div>
              </div>
            ))}
          </div>
        </div>
        <div className="space-y-4">
          <div className="border border-fg/30 rounded-none bg-neutral-50 overflow-hidden">
            <div className="px-6 py-3 border-b border-fg/20">
              <Skeleton className={cn(skeletonClass, "h-4 w-20")} />
            </div>
            <div className="px-6 py-4 grid grid-cols-2 gap-4">
              <Skeleton className={cn(skeletonClass, "h-10 w-full")} />
              <Skeleton className={cn(skeletonClass, "h-10 w-full")} />
            </div>
          </div>
          <div className="border border-fg/30 rounded-none bg-neutral-50 overflow-hidden">
            <div className="px-6 py-3 border-b border-fg/20">
              <Skeleton className={cn(skeletonClass, "h-4 w-28")} />
            </div>
            <div className="px-6 py-4">
              <Table>
                <TableHeader>
                  <TableRow className="hover:bg-transparent border-fg/15">
                    <TableHead className="text-fg">Name</TableHead>
                    <TableHead className="text-fg">Code</TableHead>
                    <TableHead className="text-fg">Status</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {[1, 2, 3].map((i) => (
                    <TableRow key={i}>
                      <TableCell><Skeleton className={cn(skeletonClass, "h-4 w-24")} /></TableCell>
                      <TableCell><Skeleton className={cn(skeletonClass, "h-4 w-12")} /></TableCell>
                      <TableCell><Skeleton className={cn(skeletonClass, "h-5 w-14")} /></TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>
          </div>
          <div className="border border-fg/30 rounded-none bg-neutral-50 overflow-hidden">
            <div className="px-6 py-3 border-b border-fg/20">
              <Skeleton className={cn(skeletonClass, "h-4 w-24")} />
            </div>
            <div className="px-6 py-4">
              <Table>
                <TableHeader>
                  <TableRow className="hover:bg-transparent border-fg/15">
                    <TableHead className="text-fg">Number</TableHead>
                    <TableHead className="text-fg">Status</TableHead>
                    <TableHead className="text-fg">Dates</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {[1, 2].map((i) => (
                    <TableRow key={i}>
                      <TableCell><Skeleton className={cn(skeletonClass, "h-4 w-20")} /></TableCell>
                      <TableCell><Skeleton className={cn(skeletonClass, "h-5 w-16")} /></TableCell>
                      <TableCell><Skeleton className={cn(skeletonClass, "h-4 w-28")} /></TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>
          </div>
          <div className="border border-fg/30 rounded-none bg-neutral-50 overflow-hidden">
            <div className="px-6 py-3 border-b border-fg/20">
              <Skeleton className={cn(skeletonClass, "h-4 w-16")} />
            </div>
            <div className="px-6 py-4 flex flex-wrap gap-2">
              <Skeleton className={cn(skeletonClass, "h-6 w-20")} />
              <Skeleton className={cn(skeletonClass, "h-6 w-24")} />
            </div>
          </div>
          <div className="border border-fg/30 rounded-none bg-neutral-50 overflow-hidden">
            <div className="px-4 py-3 border-b border-fg/20">
              <Skeleton className={cn(skeletonClass, "h-4 w-28")} />
            </div>
            <div className="p-4">
              <div className="mb-4 flex items-center gap-2">
                <Skeleton className={cn(skeletonClass, "h-8 w-8")} />
                <Skeleton className={cn(skeletonClass, "h-2 flex-1")} />
                <Skeleton className={cn(skeletonClass, "h-4 w-8")} />
              </div>
              <ul className="space-y-2">
                {[1, 2, 3, 4].map((i) => (
                  <li key={i} className="flex items-center gap-3">
                    <Skeleton className={cn(skeletonClass, "h-6 w-6")} />
                    <Skeleton className={cn(skeletonClass, "h-4 flex-1")} />
                  </li>
                ))}
              </ul>
            </div>
          </div>
          <div className="border border-fg/30 rounded-none bg-neutral-50 overflow-hidden">
            <div className="px-6 py-4 border-b border-fg/20">
              <Skeleton className={cn(skeletonClass, "h-4 w-14")} />
            </div>
            <div className="px-6 py-4 flex flex-wrap gap-2">
              <Skeleton className={cn(skeletonClass, "h-9 w-24")} />
              <Skeleton className={cn(skeletonClass, "h-9 w-28")} />
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
