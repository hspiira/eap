import { Link } from "@tanstack/react-router"
import { MoreHorizontal, Plus, Tag } from "lucide-react"

import { Button } from "@/components/ui/button"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"
import { sidebarStyles } from "@/components/ui/sidebar"
import { cn } from "@/lib/utils"

type TagsPageHeaderProps = {
  breadcrumb: string
  children?: React.ReactNode
}

export function TagsPageHeader({ breadcrumb, children }: TagsPageHeaderProps) {
  return (
    <div className="flex h-full min-h-0 flex-1 flex-col bg-white">
      <div
        className={cn(
          "h-10 flex items-center rounded-none bg-white",
          sidebarStyles.borderedRowBottom
        )}
      >
        <div className="flex w-full items-center gap-1.5 px-2 py-0">
          <Tag className="h-4 w-4 shrink-0 text-[#5A626A]/70" />
          <span className="min-w-0 flex-1 truncate text-sm text-[#5A626A]">{breadcrumb}</span>
          <Button asChild size="sm" variant="default" className="rounded-none h-8 gap-1.5 bg-natural hover:bg-natural-dark text-white">
            <Link to="/tags/new">
              <Plus className="h-4 w-4" />
              New tag
            </Link>
          </Button>
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
              <DropdownMenuItem>Export</DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        </div>
      </div>

      {children}
    </div>
  )
}
