import * as React from "react"

import { ArrowDown, ArrowUp, ChevronsUpDown } from "lucide-react"

import { Button } from "@/components/ui/button"
import { cn } from "@/lib/utils"

export type SortState = {
  field: string | undefined
  desc: boolean
}

/** Cycle: unsorted → asc → desc → unsorted. */
export function nextSort(prev: SortState, field: string): SortState {
  if (prev.field !== field) return { field, desc: false }
  if (!prev.desc) return { field, desc: true }
  return { field: undefined, desc: false }
}

/**
 * Reads `field` off a row by name. This is the one place allowed to widen a row
 * to an index signature — `sort.field` is a runtime string (it comes from column
 * definitions and the URL), so it cannot be checked statically. Callers that need
 * a computed or renamed column should pass their own `getValue` instead.
 */
export function fieldValue<T>(row: T, field: string): unknown {
  return (row as unknown as Record<string, unknown>)[field]
}

export function compareSort<T>(
  items: ReadonlyArray<T>,
  sort: SortState,
  getValue: (row: T, field: string) => unknown = fieldValue,
): T[] {
  if (!sort.field) return [...items]
  const dir = sort.desc ? -1 : 1
  return [...items].sort((a, b) => {
    const av = getValue(a, sort.field as string)
    const bv = getValue(b, sort.field as string)
    if (av == null && bv == null) return 0
    if (av == null) return 1
    if (bv == null) return -1
    if (typeof av === "number" && typeof bv === "number") return (av - bv) * dir
    return String(av).localeCompare(String(bv)) * dir
  })
}

interface SortHeaderProps {
  field: string
  sort: SortState
  onToggle: (field: string) => void
  className?: string
  align?: "left" | "right"
  children: React.ReactNode
}

export function SortHeader({
  field,
  sort,
  onToggle,
  className,
  align = "left",
  children,
}: SortHeaderProps) {
  const active = sort.field === field
  const Icon = active ? (sort.desc ? ArrowDown : ArrowUp) : ChevronsUpDown
  return (
    <Button
      type="button"
      variant="ghost"
      size="sm"
      onClick={() => onToggle(field)}
      aria-sort={active ? (sort.desc ? "descending" : "ascending") : "none"}
      className={cn(
        "group h-auto gap-1 rounded-sm p-0 text-fg/65 hover:bg-transparent hover:text-fg",
        align === "right" && "ml-auto",
        active && "text-fg",
        className,
      )}
    >
      <span>{children}</span>
      <Icon
        className={cn(
          "size-3 shrink-0 transition-colors",
          active ? "text-primary" : "text-fg/35 group-hover:text-fg/60",
        )}
      />
    </Button>
  )
}
