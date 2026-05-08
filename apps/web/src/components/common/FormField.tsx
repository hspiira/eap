import * as React from "react"

import { Label } from "@/components/ui/label"
import { cn } from "@/lib/utils"

export interface FormFieldProps {
  label: string
  description?: React.ReactNode
  error?: string
  required?: boolean
  optional?: boolean
  htmlFor?: string
  hint?: React.ReactNode
  children: React.ReactNode
  className?: string
}

export function FormField({
  label,
  description,
  error,
  required,
  optional,
  htmlFor,
  hint,
  children,
  className,
}: FormFieldProps) {
  return (
    <div className={cn("space-y-1.5", className)}>
      <div className="flex items-baseline justify-between gap-2">
        <Label htmlFor={htmlFor} className="text-xs font-medium text-fg/85">
          {label}
          {required ? (
            <span className="ml-0.5 text-danger" aria-hidden>
              *
            </span>
          ) : null}
        </Label>
        {optional ? (
          <span className="text-[10px] uppercase tracking-wider text-fg/45">
            Optional
          </span>
        ) : null}
      </div>
      {description ? (
        <p className="text-xs leading-relaxed text-fg/55">{description}</p>
      ) : null}
      {children}
      {error ? (
        <p className="text-xs font-medium text-danger" role="alert">
          {error}
        </p>
      ) : hint ? (
        <p className="text-xs text-fg/55">{hint}</p>
      ) : null}
    </div>
  )
}
