import * as React from "react"

import { cn } from "@/lib/utils"

interface FormSectionProps {
  title?: string
  description?: React.ReactNode
  children: React.ReactNode
  className?: string
}

export function FormSection({
  title,
  description,
  children,
  className,
}: FormSectionProps) {
  return (
    <section className={cn("space-y-3", className)}>
      {title ? (
        <header className="space-y-0.5">
          <h3 className="text-xs font-semibold tracking-wide text-fg/65">
            {title}
          </h3>
          {description ? (
            <p className="text-xs text-fg/55">{description}</p>
          ) : null}
        </header>
      ) : null}
      <div className="space-y-3.5">{children}</div>
    </section>
  )
}
