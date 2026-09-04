import * as React from "react"

interface PageShellProps {
  icon?: React.ElementType
  breadcrumb: React.ReactNode
  actions?: React.ReactNode
  menu?: React.ReactNode
  children?: React.ReactNode
}

export function PageShell({ icon: Icon, breadcrumb, actions, menu, children }: PageShellProps) {
  return (
    <div className="flex h-full min-h-0 flex-1 flex-col bg-bg">
      <div className="flex h-9 shrink-0 items-center gap-1.5 border-b border-fg/15 bg-surface pl-3 pr-2">
        {Icon ? <Icon className="size-3.5 shrink-0 text-fg/60" /> : null}
        <span className="min-w-0 truncate text-xs font-medium text-fg/75">{breadcrumb}</span>
        <div className="ml-auto flex items-center gap-1.5">
          {actions}
          {menu}
        </div>
      </div>
      {children}
    </div>
  )
}
