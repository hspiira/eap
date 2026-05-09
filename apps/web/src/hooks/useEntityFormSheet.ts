/**
 * Sheet form for an entity. Wraps `useApiForm` with the boilerplate every
 * `*FormSheet.tsx` component used to repeat: open-effect reset, mutation,
 * list+detail invalidation, success toast, close on success.
 *
 * Consumers pass:
 *   - schema + defaultValues (Zod + RHF)
 *   - parsePayload: form values → API request body
 *   - save: (payload, isEdit) → API call
 *   - entity (optional): when present, sheet renders in edit mode
 *   - toFormValues (required when entity given): entity → form values
 */

import { useEffect } from 'react'

import { useQueryClient } from '@tanstack/react-query'
import type { DefaultValues, FieldValues } from 'react-hook-form'
import type { ZodType } from 'zod'

import { useApiForm, type UseApiFormReturn } from '@/hooks/useApiForm'

export interface UseEntityFormSheetOptions<
  TValues extends FieldValues,
  TPayload,
  TResult,
  TEntity,
> {
  resource: string
  schema: ZodType<TValues>
  defaultValues: DefaultValues<TValues>
  open: boolean
  onOpenChange: (open: boolean) => void
  entity?: TEntity | null
  toFormValues?: (entity: TEntity) => TValues
  parsePayload: (values: TValues) => TPayload
  save: (args: { payload: TPayload; entity: TEntity | null | undefined; isEdit: boolean }) => Promise<TResult>
  successToast?: { create?: string; update?: string }
  /** Detail id to invalidate after success. Defaults to `entity.id` if `entity` has an id. */
  detailId?: string | null
  onSaved?: (result: TResult) => void
}

export interface UseEntityFormSheetReturn<TValues extends FieldValues>
  extends UseApiFormReturn<TValues> {
  isEdit: boolean
}

function entityId(entity: unknown): string | null {
  if (entity && typeof entity === 'object' && 'id' in entity) {
    const id = (entity as { id: unknown }).id
    if (typeof id === 'string') return id
  }
  return null
}

export function useEntityFormSheet<
  TValues extends FieldValues,
  TPayload,
  TResult,
  TEntity,
>(opts: UseEntityFormSheetOptions<TValues, TPayload, TResult, TEntity>): UseEntityFormSheetReturn<TValues> {
  const {
    resource,
    schema,
    defaultValues,
    open,
    onOpenChange,
    entity,
    toFormValues,
    parsePayload,
    save,
    successToast,
    detailId,
    onSaved,
  } = opts

  const isEdit = !!entity
  const qc = useQueryClient()

  const form = useApiForm<TValues>({
    schema,
    defaultValues,
    successToast: isEdit ? successToast?.update : successToast?.create,
    onSubmit: async (values) => {
      const payload = parsePayload(values)
      const result = await save({ payload, entity: entity ?? null, isEdit })
      await qc.invalidateQueries({ queryKey: [resource, 'list'] })
      const id = detailId ?? entityId(entity)
      if (id) await qc.invalidateQueries({ queryKey: [resource, 'detail', id] })
      onSaved?.(result)
      onOpenChange(false)
      form.reset()
    },
  })

  useEffect(() => {
    if (!open) return
    if (entity && toFormValues) {
      form.reset(toFormValues(entity) as DefaultValues<TValues>)
    } else {
      form.reset(defaultValues)
    }
    // form is stable; defaultValues reference is owned by the caller
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [open, entity])

  return { ...form, isEdit }
}
