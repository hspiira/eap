/**
 * Form Component
 * Wrapper component for React Hook Form integration
 */

import { FormProvider, useForm, UseFormReturn, FieldValues, SubmitHandler, DefaultValues, Resolver } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { ReactNode } from 'react'

export interface FormProps<T extends FieldValues> {
  schema?: z.ZodSchema<T>
  defaultValues?: DefaultValues<T>
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
    resolver: schema
      ? (zodResolver(schema as Parameters<typeof zodResolver>[0]) as Resolver<T, any, T>)
      : undefined,
    defaultValues: (defaultValues ?? {}) as DefaultValues<T>,
  })

  const handleSubmit = methods.handleSubmit(async (data) => {
    try {
      await onSubmit(data)
    } catch (error) {
      throw error // Allow caller's onSubmit to handle via its own try/catch
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
