import * as React from "react"

import { Lock } from "lucide-react"

import { cn } from "@/lib/utils"

/** Shared building blocks for detail pages. */

export function DetailCard({
  title,
  phiLabel,
  children,
}: {
  title: string
  /** Marks the card as showing protected health information. */
  phiLabel?: string
  children: React.ReactNode
}) {
  return (
    <section className="rounded-sm border border-fg/10 bg-surface p-4">
      {phiLabel ? (
        <div className="mb-3 flex items-center gap-2">
          <h3 className="text-xs font-semibold tracking-wide text-fg/55">{title}</h3>
          <span className="ml-auto inline-flex items-center gap-1 text-[10px] text-fg/40">
            <Lock className="size-2.5" aria-hidden />
            {phiLabel}
          </span>
        </div>
      ) : (
        <h3 className="mb-3 text-xs font-semibold tracking-wide text-fg/55">{title}</h3>
      )}
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
      <h3 className="text-xs font-semibold tracking-wide text-fg/55">{title}</h3>
      {children}
    </section>
  )
}

export function DetailGrid({ children }: { children: React.ReactNode }) {
  return <dl className="grid grid-cols-2 gap-x-3 gap-y-2.5">{children}</dl>
}

export function DetailRow({
  label,
  value,
  fullWidth,
}: {
  label: string
  value: React.ReactNode
  fullWidth?: boolean
}) {
  return (
    <div className={cn(fullWidth && "col-span-2")}>
      <dt className="text-[11px] font-medium tracking-wide text-fg/55">{label}</dt>
      <dd className="mt-0.5 truncate text-sm text-fg">
        {value || <span className="text-fg/40">—</span>}
      </dd>
    </div>
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
      <div className="text-[11px] font-medium tracking-wide text-fg/55">{label}</div>
      <div
        className={cn(
          "mt-0.5 font-semibold text-fg",
          variant === "numeric" ? "font-mono text-base" : "text-sm",
          truncate && "truncate",
        )}
      >
        {value}
      </div>
    </div>
  )
}
