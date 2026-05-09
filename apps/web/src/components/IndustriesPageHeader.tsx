import { BarChart3, MoreHorizontal } from "lucide-react"

import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"
import { Button } from "@/components/ui/button"
import { cn } from "@/lib/utils"

type IndustriesPageHeaderProps = {
  breadcrumb: string
  children?: React.ReactNode
}

export function IndustriesPageHeader({ breadcrumb, children }: IndustriesPageHeaderProps) {
  return (
    <div className="flex h-full min-h-0 flex-1 flex-col bg-white">
      <div
        className={cn(
          "h-8 flex items-center rounded-none bg-white border-b border-fg/20",
        )}
      >
        <div className="flex w-full items-center gap-1.5 px-2 py-1">
          <BarChart3 className="h-4 w-4 shrink-0 text-fg/70" />
          <span className="min-w-0 flex-1 truncate text-sm text-fg">{breadcrumb}</span>
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button
                type="button"
                variant="ghost"
                size="sm"
                className="size-8 shrink-0 p-0 text-fg"
                aria-label="More options"
              >
                <MoreHorizontal className="h-4 w-4" />
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end">
              <DropdownMenuItem>View settings</DropdownMenuItem>
              <DropdownMenuItem>Export</DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        </div>
      </div>

      {children}
    </div>
  )
}
