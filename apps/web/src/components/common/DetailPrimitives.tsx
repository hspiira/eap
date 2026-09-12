import * as React from "react"

import { Link } from "@tanstack/react-router"
import { ChevronRight, Lock } from "lucide-react"

import { cn } from "@/lib/utils"

/** Shared building blocks for detail pages. */

export function DetailCard({
  title,
  icon: Icon,
  phiLabel,
  action,
  children,
}: {
  title: string
  /** Small anchor icon rendered before the title. */
  icon?: React.ComponentType<{ className?: string }>
  /** Marks the card as showing protected health information. */
  phiLabel?: string
  /** Optional control rendered at the top-right of the header (e.g. an Edit button). */
  action?: React.ReactNode
  children: React.ReactNode
}) {
  return (
    <section className="rounded-none border border-fg/10 bg-surface p-4">
      <div className="mb-3 flex items-center gap-2 border-b border-fg/10 pb-2">
        {Icon ? <Icon className="size-3.5 shrink-0 text-primary/70" aria-hidden /> : null}
        <h3 className="text-xs font-semibold tracking-wide text-fg-muted">{title}</h3>
        {phiLabel ? (
          <span className="ml-auto inline-flex items-center gap-1 text-[10px] text-fg-subtle">
            <Lock className="size-2.5" aria-hidden />
            {phiLabel}
          </span>
        ) : action ? (
          <span className="ml-auto">{action}</span>
        ) : null}
      </div>
      {children}
    </section>
  )
}

export function RailSection({
  title,
  children,
  className,
}: {
  title: string
  children: React.ReactNode
  className?: string
}) {
  return (
    <section className={cn("space-y-2", className)}>
      <h3 className="text-xs font-semibold tracking-wide text-fg-muted">{title}</h3>
      {children}
    </section>
  )
}

/** A list of one-line rows, separated by hairlines. Accepts DetailRow and LinkRow. */
export function DetailGrid({ children }: { children: React.ReactNode }) {
  return <div className="divide-y divide-fg/5">{children}</div>
}

export function DetailRow({
  label,
  value,
  fullWidth,
}: {
  label: string
  value: React.ReactNode
  /** Lets a prose value wrap instead of truncating. */
  fullWidth?: boolean
}) {
  return (
    <div className="flex items-baseline gap-1.5 py-1.5 first:pt-0 last:pb-0">
      <span className="shrink-0 text-xs text-fg-muted">{label}:</span>
      <span
        className={cn("min-w-0 text-sm text-fg", fullWidth ? "whitespace-pre-wrap" : "truncate")}
        title={!fullWidth && typeof value === "string" ? value : undefined}
      >
        {value || <span className="text-fg-subtle">-</span>}
      </span>
    </div>
  )
}

/** A one-line "label: value" row that navigates, with a chevron to say so. */
export function LinkRow({
  label,
  value,
  meta,
  to,
  params,
}: {
  label: string
  value: React.ReactNode
  /** Short trailing context, e.g. a category or relation. */
  meta?: string | null
  to: string
  params?: Record<string, string>
}) {
  return (
    <Link
      to={to as never}
      params={params as never}
      className="group flex items-center gap-1.5 py-1.5 first:pt-0 last:pb-0"
    >
      <span className="shrink-0 text-xs text-fg-muted">{label}:</span>
      <span className="min-w-0 truncate text-sm font-medium text-primary group-hover:underline">
        {value}
      </span>
      {meta ? <span className="shrink-0 text-xs text-fg-muted">· {meta}</span> : null}
      <ChevronRight
        aria-hidden
        className="size-3.5 shrink-0 text-primary/60 transition-transform group-hover:translate-x-0.5 group-hover:text-primary"
      />
    </Link>
  )
}

export function Stat({
  label,
  value,
  /** `text` for prose values, which read badly in mono. */
  variant = "numeric",
  truncate,
}: {
  label: string
  value: React.ReactNode
  variant?: "numeric" | "text"
  truncate?: boolean
}) {
  return (
    <div className="rounded-sm border border-fg/10 bg-surface px-3 py-2">
      <div className="text-[11px] font-medium tracking-wide text-fg-muted">{label}</div>
      <div
        className={cn(
          "mt-0.5 font-semibold text-fg",
          variant === "numeric" ? "tabular-nums text-base" : "text-sm",
          truncate && "truncate",
        )}
      >
        {value}
      </div>
    </div>
  )
}
