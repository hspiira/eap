/**
 * Form Component
 * Wrapper component for React Hook Form integration
 */

import { FormProvider, useForm, UseFormReturn, FieldValues, SubmitHandler } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { ReactNode } from 'react'

export interface FormProps<T extends FieldValues> {
  schema?: z.ZodSchema<T>
  defaultValues?: Partial<T>
  onSubmit: SubmitHandler<T>
  children: (methods: UseFormReturn<T>) => ReactNode
  loading?: boolean
  className?: string
}

export function Form<T extends FieldValues>({
  schema,
  defaultValues,
  onSubmit,
  children,
  loading = false,
  className = '',
}: FormProps<T>) {
  const methods = useForm<T>({
    resolver: schema ? zodResolver(schema) : undefined,
    defaultValues: (defaultValues || {}) as any,
  })

  const handleSubmit = methods.handleSubmit(async (data) => {
    try {
      await onSubmit(data)
    } catch (error) {
      // Error handling is done by the form's error state
      console.error('Form submission error:', error)
    }
  })

  return (
    <FormProvider {...methods}>
      <form onSubmit={handleSubmit} className={className}>
        {loading && (
          <div className="mb-4 p-3 bg-surface-muted border border-[0.5px] border-border text-text text-sm">
            Submitting...
          </div>
        )}
        {children(methods)}
      </form>
    </FormProvider>
  )
}
