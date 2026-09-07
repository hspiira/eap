import * as React from "react"

import { cn } from "@/lib/utils"

interface TableProps extends React.HTMLAttributes<HTMLTableElement> {
  /**
   * Wrap the table in its own scroll container. Leave it on for a table inside
   * a card or a dialog, which has nowhere else to scroll.
   *
   * Turn it off when the caller already owns a scroll area. The wrapper is a
   * scrolling ancestor, and `position: sticky` resolves against the nearest
   * one, so a sticky header inside an unconstrained wrapper has no scrollport
   * to stick in and rides up with the rows. That is what silently disabled
   * every sticky header on the list pages.
   */
  scrollable?: boolean
}

const Table = React.forwardRef<HTMLTableElement, TableProps>(
  ({ className, scrollable = true, ...props }, ref) => {
    const table = (
      <table
        ref={ref}
        className={cn("w-full caption-bottom text-sm rounded-none", className)}
        {...props}
      />
    )
    if (!scrollable) return table
    return <div className="relative w-full overflow-auto">{table}</div>
  },
)
Table.displayName = "Table"

const TableHeader = React.forwardRef<
  HTMLTableSectionElement,
  React.HTMLAttributes<HTMLTableSectionElement>
>(({ className, ...props }, ref) => (
  <thead
    ref={ref}
    className={cn("border-b border-fg/30 bg-surface rounded-none", className)}
    {...props}
  />
))
TableHeader.displayName = "TableHeader"

const TableBody = React.forwardRef<
  HTMLTableSectionElement,
  React.HTMLAttributes<HTMLTableSectionElement>
>(({ className, ...props }, ref) => (
  <tbody ref={ref} className={cn("[&_tr:last-child]:border-0", className)} {...props} />
))
TableBody.displayName = "TableBody"

const TableRow = React.forwardRef<HTMLTableRowElement, React.HTMLAttributes<HTMLTableRowElement>>(
  ({ className, ...props }, ref) => (
    <tr
      ref={ref}
      className={cn(
        "border-b border-fg/20 transition-colors hover:bg-surface-hover data-[state=selected]:bg-primary/8",
        className,
      )}
      {...props}
    />
  ),
)
TableRow.displayName = "TableRow"

const TableHead = React.forwardRef<
  HTMLTableCellElement,
  React.ThHTMLAttributes<HTMLTableCellElement>
>(({ className, ...props }, ref) => (
  <th
    ref={ref}
    className={cn(
      "h-8 px-3 text-left align-middle font-semibold text-primary text-xs rounded-none",
      className,
    )}
    {...props}
  />
))
TableHead.displayName = "TableHead"

const TableCell = React.forwardRef<
  HTMLTableCellElement,
  React.TdHTMLAttributes<HTMLTableCellElement>
>(({ className, ...props }, ref) => (
  <td
    ref={ref}
    className={cn("px-3 py-1.5 align-middle text-sm rounded-none", className)}
    {...props}
  />
))
TableCell.displayName = "TableCell"

export { Table, TableBody, TableCell, TableHead, TableHeader, TableRow }
