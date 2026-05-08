import * as React from "react"

import { MoreHorizontal } from "lucide-react"

import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"

interface PageShellProps {
  icon?: React.ElementType
  breadcrumb: string
  title: React.ReactNode
  description?: React.ReactNode
  actions?: React.ReactNode
  toolbar?: React.ReactNode
  menu?: React.ReactNode
  children?: React.ReactNode
}

export function PageShell({
  icon: Icon,
  breadcrumb,
  title,
  description,
  actions,
  toolbar,
  menu,
  children,
}: PageShellProps) {
  return (
    <div className="flex h-full min-h-0 flex-1 flex-col bg-bg">
      <div className="flex h-9 shrink-0 items-center gap-1.5 border-b border-fg/15 bg-surface px-4">
        {Icon ? <Icon className="size-3.5 shrink-0 text-fg/60" /> : null}
        <span className="min-w-0 truncate text-xs font-medium text-fg/70">
          {breadcrumb}
        </span>
        <div className="ml-auto" />
        {menu ?? <DefaultPageMenu />}
      </div>

      <div className="flex flex-wrap items-end justify-between gap-3 border-b border-fg/10 bg-surface px-5 pb-4 pt-5 shrink-0">
        <div className="min-w-0">
          <h1 className="truncate text-xl font-semibold leading-tight text-fg">
            {title}
          </h1>
          {description ? (
            <p className="mt-1 text-sm text-fg/65">{description}</p>
          ) : null}
        </div>
        {actions ? <div className="flex items-center gap-2">{actions}</div> : null}
      </div>

      {toolbar ? (
        <div className="flex flex-wrap items-center gap-2 border-b border-fg/10 bg-surface px-5 py-2.5 shrink-0">
          {toolbar}
        </div>
      ) : null}

      {children}
    </div>
  )
}

function DefaultPageMenu() {
  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <button
          type="button"
          aria-label="Page options"
          className="grid size-7 place-items-center rounded-none text-fg/70 transition-colors hover:bg-surface-hover hover:text-fg"
        >
          <MoreHorizontal className="size-4" />
        </button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="end" className="rounded-none">
        <DropdownMenuItem>View settings</DropdownMenuItem>
        <DropdownMenuItem>Export CSV</DropdownMenuItem>
      </DropdownMenuContent>
    </DropdownMenu>
  )
}
