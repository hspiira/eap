import { BarChart3, MoreHorizontal } from "lucide-react"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"
import { cn } from "@/lib/utils"
import { sidebarStyles } from "@/components/ui/sidebar"

type IndustriesPageHeaderProps = {
  breadcrumb: string
  children?: React.ReactNode
}

export function IndustriesPageHeader({ breadcrumb, children }: IndustriesPageHeaderProps) {
  return (
    <div className="flex h-full min-h-0 flex-1 flex-col bg-white">
      <div
        className={cn(
          "h-8 flex items-center rounded-none bg-white",
          sidebarStyles.borderedRowBottom
        )}
      >
        <div className="flex w-full items-center gap-1.5 px-2 py-1">
          <BarChart3 className="h-4 w-4 shrink-0 text-[#5A626A]/70" />
          <span className="min-w-0 flex-1 truncate text-sm text-[#5A626A]">{breadcrumb}</span>
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <button
                type="button"
                className="flex h-8 w-8 shrink-0 items-center justify-center py-0 text-[#5A626A] hover:bg-[#f0f0f0]"
                aria-label="More options"
              >
                <MoreHorizontal className="h-4 w-4" />
              </button>
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
