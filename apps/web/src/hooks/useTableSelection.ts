import { useEffect, useRef, useState } from "react"

export interface TableSelection {
  selectedIds: ReadonlySet<string>
  selectAllState: boolean | "indeterminate"
  toggleSelect: (id: string) => void
  toggleSelectAll: () => void
  clearSelection: () => void
}

export function useTableSelection<T extends { id: string }>(items: T[]): TableSelection {
  const [selectedIds, setSelectedIds] = useState<Set<string>>(new Set())

  const prevKeyRef = useRef<string>("")
  const itemKey = items.map((i) => i.id).join(",")
  useEffect(() => {
    if (itemKey !== prevKeyRef.current) {
      prevKeyRef.current = itemKey
      setSelectedIds(new Set())
    }
  }, [itemKey])

  const toggleSelect = (id: string) => {
    setSelectedIds((prev) => {
      const next = new Set(prev)
      next.has(id) ? next.delete(id) : next.add(id)
      return next
    })
  }

  const toggleSelectAll = () => {
    setSelectedIds((prev) =>
      prev.size === items.length ? new Set() : new Set(items.map((i) => i.id)),
    )
  }

  const clearSelection = () => setSelectedIds(new Set())

  const isAll = items.length > 0 && selectedIds.size === items.length
  const isSome = selectedIds.size > 0 && !isAll
  const selectAllState: boolean | "indeterminate" = isAll ? true : isSome ? "indeterminate" : false

  return { selectedIds, selectAllState, toggleSelect, toggleSelectAll, clearSelection }
}
