import * as React from "react"

import { cn } from "@/lib/utils"

interface PanelProps {
  icon?: React.ElementType
  title: React.ReactNode
  subtitle?: React.ReactNode
  count?: number | null
  action?: React.ReactNode
  badge?: React.ReactNode
  children?: React.ReactNode
  className?: string
  bodyClassName?: string
}

export function Panel({
  icon: Icon,
  title,
  subtitle,
  count,
  action,
  badge,
  children,
  className,
  bodyClassName,
}: PanelProps) {
  return (
    <section
      className={cn(
        "flex min-h-0 flex-col rounded-sm border border-fg/10 bg-surface",
        className,
      )}
    >
      <header className="flex shrink-0 items-center gap-2 border-b border-fg/8 px-3 py-2">
        {Icon ? <Icon className="size-3.5 shrink-0 text-fg/55" /> : null}
        <div className="min-w-0 flex-1">
          <h3 className="truncate text-sm font-semibold leading-tight text-fg">
            {title}
          </h3>
          {subtitle ? (
            <p className="mt-0.5 truncate text-xs text-fg/60">{subtitle}</p>
          ) : null}
        </div>
        {count != null ? (
          <span className="shrink-0 font-mono text-[11px] tabular-nums text-fg/55">
            {count}
          </span>
        ) : null}
        {badge}
        {action ? <div className="shrink-0">{action}</div> : null}
      </header>
      <div className={cn(bodyClassName ?? "p-3")}>{children}</div>
    </section>
  )
}

export function PanelEmpty({
  children,
  className,
}: {
  children: React.ReactNode
  className?: string
}) {
  return (
    <p className={cn("px-3 py-6 text-center text-sm text-fg/60", className)}>
      {children}
    </p>
  )
}

export function PanelList({
  children,
  className,
}: {
  children: React.ReactNode
  className?: string
}) {
  return (
    <ul className={cn("divide-y divide-fg/8", className)}>{children}</ul>
  )
}
