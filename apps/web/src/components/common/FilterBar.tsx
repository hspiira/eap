import * as React from "react"

import { ChevronDown, Filter as FilterIcon, Search, X } from "lucide-react"

import { Button } from "@/components/ui/button"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"
import { cn } from "@/lib/utils"

export function FilterBar({
  children,
  className,
}: {
  children: React.ReactNode
  className?: string
}) {
  return (
    <div
      className={cn(
        "flex h-10 shrink-0 flex-nowrap items-center gap-2 overflow-x-auto border-b border-fg/15 bg-surface px-3",
        className,
      )}
    >
      {children}
    </div>
  )
}

interface FilterButtonProps {
  options: ReadonlyArray<{
    id: string
    label: string
    icon?: React.ElementType
    onSelect?: () => void
  }>
}

export function FilterButton({ options }: FilterButtonProps) {
  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <Button variant="secondary" size="sm" className="h-8 shrink-0 gap-1.5">
          <FilterIcon className="size-3.5" />
          Filter
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="start" className="min-w-52">
        {options.map((opt) => (
          <DropdownMenuItem
            key={opt.id}
            className="gap-2"
            onSelect={(e) => {
              e.preventDefault()
              opt.onSelect?.()
            }}
          >
            {opt.icon ? <opt.icon className="size-4" /> : <span className="size-4" />}
            {opt.label}
          </DropdownMenuItem>
        ))}
      </DropdownMenuContent>
    </DropdownMenu>
  )
}

interface FilterChipProps {
  label: React.ReactNode
  onRemove: () => void
}

export function FilterChip({ label, onRemove }: FilterChipProps) {
  return (
    <span className="inline-flex h-8 shrink-0 items-center gap-1 rounded-sm border border-fg/25 bg-bg pl-2 pr-1 text-sm text-fg">
      <span className="truncate">{label}</span>
      <button
        type="button"
        onClick={onRemove}
        aria-label="Remove filter"
        className="grid size-5 place-items-center rounded-sm text-fg/65 transition-colors hover:bg-surface-hover hover:text-fg"
      >
        <X className="size-3" />
      </button>
    </span>
  )
}

interface FilterTriggerOption<T extends string> {
  value: T
  label: string
}

interface FilterTriggerProps<T extends string> {
  icon?: React.ElementType
  label: string
  value: T
  options: ReadonlyArray<FilterTriggerOption<T>>
  onChange: (value: T) => void
}

export function FilterTrigger<T extends string>({
  icon: Icon,
  label,
  value,
  options,
  onChange,
}: FilterTriggerProps<T>) {
  const current = options.find((o) => o.value === value)?.label ?? label
  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <button
          type="button"
          className="inline-flex h-8 shrink-0 items-center gap-1.5 rounded-sm border border-fg/25 bg-bg px-2 text-sm text-fg hover:bg-surface-hover focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
        >
          {Icon ? <Icon className="size-3.5 text-fg/65" /> : null}
          <span className="whitespace-nowrap">{current}</span>
          <ChevronDown className="size-3.5 text-fg/55" />
        </button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="start" className="min-w-44">
        {options.map((opt) => (
          <DropdownMenuItem
            key={opt.value}
            className="gap-2"
            onSelect={() => onChange(opt.value)}
          >
            {opt.label}
          </DropdownMenuItem>
        ))}
      </DropdownMenuContent>
    </DropdownMenu>
  )
}

interface FilterSearchProps {
  value: string
  onChange: (value: string) => void
  placeholder?: string
  className?: string
}

export function FilterSearch({
  value,
  onChange,
  placeholder = "Search…",
  className,
}: FilterSearchProps) {
  return (
    <label
      className={cn(
        "relative inline-flex h-8 shrink-0 items-center rounded-sm border border-fg/25 bg-bg pl-7 pr-1.5 focus-within:ring-2 focus-within:ring-ring",
        className,
      )}
    >
      <Search
        aria-hidden
        className="pointer-events-none absolute left-2 size-3.5 text-fg/55"
      />
      <input
        type="search"
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder={placeholder}
        aria-label={placeholder}
        className="h-full w-44 bg-transparent text-sm text-fg placeholder:text-fg/55 focus:outline-none"
      />
      <kbd
        aria-hidden
        className="ml-1 hidden h-5 select-none items-center border border-fg/20 bg-surface px-1 font-mono text-[10px] text-fg/55 sm:inline-flex"
      >
        ⌘K
      </kbd>
    </label>
  )
}
