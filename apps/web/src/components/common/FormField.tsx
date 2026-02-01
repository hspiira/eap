/**
 * Form Field Component
 * Wrapper around shadcn Input + Label with our API.
 * Supports both controlled and React Hook Form integration.
 */

"use client"

import * as React from 'react'
import { useFormContext, Controller } from 'react-hook-form'

import { cn } from '@/lib/utils'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { getFieldError } from '@/utils/validators'

interface FormFieldProps {
  label: string
  name: string
  type?: 'text' | 'email' | 'password' | 'number' | 'tel' | 'url' | 'textarea'
  value?: string
  onChange?: (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => void
  error?: string
  required?: boolean
  placeholder?: string
  autoComplete?: string
  disabled?: boolean
  min?: number
  max?: number
  rows?: number
  className?: string
  compact?: boolean
  useFormContext?: boolean
}

export function FormField({
  label,
  name,
  type = 'text',
  value: controlledValue,
  onChange: controlledOnChange,
  error: externalError,
  required = false,
  placeholder,
  autoComplete,
  disabled = false,
  min,
  max,
  rows = 4,
  className = '',
  compact = false,
  useFormContext: useForm = false,
}: FormFieldProps) {
  const formContext = useForm ? useFormContext() : null
  const formError = formContext ? getFieldError(formContext.formState.errors, name) : null
  const error = externalError || formError
  const space = compact ? 'mb-2' : 'mb-4'
  const labelSpace = compact ? 'mb-1' : 'mb-2'

  const inputClassName = cn(
    'rounded-none bg-surface border-border focus-visible:ring-border-focus',
    error && 'border-danger'
  )

  if (useForm && formContext) {
    return (
      <div className={cn(space, className)}>
        <Label htmlFor={name} className={cn('block text-text text-sm font-medium', labelSpace)}>
          {label}
          {required && <span className="text-danger ml-1">*</span>}
        </Label>
        <Controller
          name={name}
          control={formContext.control}
          render={({ field }) => {
            if (type === 'textarea') {
              return (
                <textarea
                  {...field}
                  id={name}
                  rows={rows}
                  placeholder={placeholder}
                  disabled={disabled}
                  required={required}
                  className={cn(
                    'flex w-full rounded-none border bg-surface px-3 py-2 text-base transition-colors placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring disabled:cursor-not-allowed disabled:opacity-50 md:text-sm',
                    error ? 'border-danger' : 'border-border'
                  )}
                />
              )
            }
            return (
              <Input
                {...field}
                type={type}
                id={name}
                placeholder={placeholder}
                autoComplete={autoComplete}
                disabled={disabled}
                required={required}
                min={min}
                max={max}
                className={inputClassName}
              />
            )
          }}
        />
        {error && <p className="mt-1 text-sm text-danger">{error}</p>}
      </div>
    )
  }

  if (type === 'textarea') {
    return (
      <div className={cn(space, className)}>
        <Label htmlFor={name} className={cn('block text-text text-sm font-medium', labelSpace)}>
          {label}
          {required && <span className="text-danger ml-1">*</span>}
        </Label>
        <textarea
          id={name}
          name={name}
          value={controlledValue || ''}
          onChange={controlledOnChange as React.ChangeEventHandler<HTMLTextAreaElement>}
          placeholder={placeholder}
          required={required}
          disabled={disabled}
          rows={rows}
          className={cn(
            'flex w-full rounded-none border bg-surface px-3 py-2 text-base transition-colors placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring disabled:cursor-not-allowed disabled:opacity-50 md:text-sm',
            error ? 'border-danger' : 'border-border'
          )}
        />
        {error && <p className="mt-1 text-sm text-danger">{error}</p>}
      </div>
    )
  }

  return (
    <div className={cn(space, className)}>
      <Label htmlFor={name} className={cn('block text-text text-sm font-medium', labelSpace)}>
        {label}
        {required && <span className="text-danger ml-1">*</span>}
      </Label>
      <Input
        type={type}
        id={name}
        name={name}
        value={controlledValue || ''}
        onChange={controlledOnChange}
        placeholder={placeholder}
        autoComplete={autoComplete}
        required={required}
        disabled={disabled}
        min={min}
        max={max}
        className={inputClassName}
      />
      {error && <p className="mt-1 text-sm text-danger">{error}</p>}
    </div>
  )
}
