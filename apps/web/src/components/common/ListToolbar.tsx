import * as React from "react"

import { Search } from "lucide-react"

import { Input } from "@/components/ui/input"
import { cn } from "@/lib/utils"

interface ListToolbarProps {
  searchValue: string
  onSearchChange: (value: string) => void
  placeholder?: string
  filters?: React.ReactNode
  trailing?: React.ReactNode
  className?: string
}

export function ListToolbar({
  searchValue,
  onSearchChange,
  placeholder = "Search…",
  filters,
  trailing,
  className,
}: ListToolbarProps) {
  return (
    <div className={cn("flex flex-wrap items-center gap-2", className)}>
      <div className="relative h-9 min-w-0 flex-1 max-w-sm">
        <Search
          className="pointer-events-none absolute left-2.5 top-1/2 size-4 -translate-y-1/2 text-fg/55"
          aria-hidden
        />
        <Input
          value={searchValue}
          onChange={(e) => onSearchChange(e.target.value)}
          placeholder={placeholder}
          aria-label={placeholder}
          className="h-9 rounded-none border-fg/25 bg-surface pl-8 pr-12 text-sm text-fg placeholder:text-fg/55 focus-visible:ring-ring"
        />
        <kbd
          aria-hidden
          className="pointer-events-none absolute right-2 top-1/2 inline-flex h-5 -translate-y-1/2 select-none items-center rounded-sm border border-fg/20 bg-bg px-1.5 font-mono text-[10px] font-medium text-fg/55"
        >
          ⌘K
        </kbd>
      </div>
      {filters}
      {trailing ? <div className="ml-auto flex items-center gap-2">{trailing}</div> : null}
    </div>
  )
}
