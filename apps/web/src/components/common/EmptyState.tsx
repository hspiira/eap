import * as React from "react"

import { cn } from "@/lib/utils"

interface EmptyStateProps {
  icon?: React.ElementType
  title: string
  description?: React.ReactNode
  action?: React.ReactNode
  illustration?: React.ReactNode
  className?: string
}

export function EmptyState({
  icon: Icon,
  title,
  description,
  action,
  illustration,
  className,
}: EmptyStateProps) {
  return (
    <div className={cn("flex flex-1 items-center justify-center px-6 py-10", className)}>
      <div className="flex max-w-sm flex-col items-center text-center">
        {illustration ?? <DefaultIllustration icon={Icon} />}
        <h2 className="mt-5 text-base font-semibold text-fg">{title}</h2>
        {description ? (
          <p className="mt-1 text-sm text-fg/60">{description}</p>
        ) : null}
        {action ? <div className="mt-5">{action}</div> : null}
      </div>
    </div>
  )
}

function DefaultIllustration({ icon: Icon }: { icon?: React.ElementType }) {
  return (
    <div
      className="relative flex h-24 w-64 items-end justify-center"
      aria-hidden
    >
      <SkeletonRow icon={Icon} className="absolute left-3 top-0 w-52 opacity-55" />
      <SkeletonRow icon={Icon} className="absolute right-3 bottom-0 w-52 opacity-55" />
      <SkeletonRow
        icon={Icon}
        className="relative z-10 w-60 border-fg/15 bg-surface shadow-[0_1px_0_rgb(0_0_0/0.04)]"
      />
    </div>
  )
}

function SkeletonRow({
  icon: Icon,
  className,
}: {
  icon?: React.ElementType
  className?: string
}) {
  return (
    <div
      className={cn(
        "flex h-9 items-center gap-2.5 border border-fg/10 bg-surface px-2.5",
        className,
      )}
    >
      <span className="grid size-5 shrink-0 place-items-center bg-fg/8 text-fg/40">
        {Icon ? <Icon className="size-3" /> : null}
      </span>
      <span className="flex flex-1 flex-col gap-1">
        <span className="h-1.5 w-3/5 bg-fg/12" />
        <span className="h-1.5 w-2/5 bg-fg/8" />
      </span>
    </div>
  )
}
