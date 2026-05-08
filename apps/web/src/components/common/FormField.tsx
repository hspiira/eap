import * as React from "react"

import { Label } from "@/components/ui/label"
import { cn } from "@/lib/utils"

export interface FormFieldProps {
  label: string
  error?: string
  required?: boolean
  htmlFor?: string
  children: React.ReactNode
  className?: string
}

export function FormField({
  label,
  error,
  required,
  htmlFor,
  children,
  className,
}: FormFieldProps) {
  return (
    <div className={cn("space-y-1.5", className)}>
      <Label htmlFor={htmlFor}>
        {label}
        {required && <span className="text-fg/80 ml-0.5">*</span>}
      </Label>
      {children}
      {error && (
        <p className="text-sm text-fg" role="alert">
          {error}
        </p>
      )}
    </div>
  )
}
