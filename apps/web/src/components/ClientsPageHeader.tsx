import { Link } from "@tanstack/react-router"
import { Building2, MoreHorizontal, Plus, Search } from "lucide-react"

import { Button } from "@/components/ui/button"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"
import { Input } from "@/components/ui/input"
import { cn } from "@/lib/utils"

type ClientsPageHeaderProps = {
  breadcrumb: string
  toolbar?: React.ReactNode
  children?: React.ReactNode
}

export function ClientsPageHeader({ breadcrumb, toolbar, children }: ClientsPageHeaderProps) {
  return (
    <div className="flex h-full min-h-0 flex-1 flex-col bg-white">
      <div
        className={cn(
          "flex items-center gap-1.5 px-3 py-1.5 rounded-none bg-white border-b border-fg/20",
        )}
      >
        <Building2 className="h-4 w-4 shrink-0 text-fg/70" />
        <span className="min-w-0 flex-1 truncate text-sm text-fg">{breadcrumb}</span>
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <button
              type="button"
              className="flex h-8 w-8 shrink-0 items-center justify-center text-fg hover:bg-surface-hover rounded-sm"
              aria-label="More options"
            >
              <MoreHorizontal className="h-4 w-4" />
            </button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end" className="rounded-none">
            <DropdownMenuItem>View settings</DropdownMenuItem>
            <DropdownMenuItem>Export</DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      </div>

      {toolbar != null && (
        <div className="flex flex-wrap items-center gap-2 border-b border-fg/20 bg-white px-3 py-2">
          {toolbar}
        </div>
      )}

      {children}
    </div>
  )
}

export function ClientsListToolbar({
  searchValue,
  onSearchChange,
}: {
  searchValue?: string
  onSearchChange?: (value: string) => void
}) {
  return (
    <>
      <h1 className="text-base font-semibold text-fg shrink-0">Clients</h1>
      <div className="min-w-0 flex-1 flex justify-end gap-2">
        {onSearchChange != null && (
          <div className="relative w-full max-w-xs">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-fg/60" />
            <Input
              placeholder="Search clients…"
              value={searchValue ?? ""}
              onChange={(e) => onSearchChange(e.target.value)}
              className="pl-8 h-8 rounded-none border-fg/30 bg-white text-fg placeholder:text-fg/50 text-sm"
            />
          </div>
        )}
        <Link to="/clients/new">
          <Button size="sm" className="h-8 gap-1 rounded-none bg-primary text-white hover:bg-primary">
            <Plus className="h-4 w-4" />
            Add client
          </Button>
        </Link>
      </div>
    </>
  )
}
