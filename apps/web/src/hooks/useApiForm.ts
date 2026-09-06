/**
 * React Hook Form bound to a Zod schema, with ApiError → field-error mapping.
 *
 * - `ApiError.fieldErrors` → `form.setError(field)`
 * - non-field errors → `errors.root.serverError`, exposed as `serverError`
 * - success toast on resolution if `successToast` is provided
 */

import { zodResolver } from "@hookform/resolvers/zod"
import {
  type DefaultValues,
  type FieldValues,
  type Path,
  type Resolver,
  useForm,
  type UseFormProps,
  type UseFormReturn,
} from "react-hook-form"
import type { ZodType } from "zod"

import { useToast } from "@/contexts/ToastContext"
import { defaultErrorMessage, isApiError } from "@/lib/errors"

export interface UseApiFormOptions<TValues extends FieldValues> {
  schema: ZodType<TValues>
  defaultValues?: DefaultValues<TValues>
  onSubmit: (values: TValues) => Promise<void> | void
  successToast?: string
  errorToast?: boolean
  formOptions?: Omit<UseFormProps<TValues>, "resolver" | "defaultValues">
}

export interface UseApiFormReturn<TValues extends FieldValues> extends UseFormReturn<TValues> {
  submit: (e?: React.BaseSyntheticEvent) => Promise<void>
  serverError: string | undefined
}

export function useApiForm<TValues extends FieldValues>(
  opts: UseApiFormOptions<TValues>,
): UseApiFormReturn<TValues> {
  const { showSuccess, showError } = useToast()

  const form = useForm<TValues>({
    ...opts.formOptions,
    resolver: zodResolver(
      opts.schema as unknown as Parameters<typeof zodResolver>[0],
    ) as Resolver<TValues>,
    defaultValues: opts.defaultValues,
  })

  const submit = form.handleSubmit(async (values) => {
    form.clearErrors("root.serverError" as Path<TValues>)
    try {
      await opts.onSubmit(values as TValues)
      if (opts.successToast) showSuccess(opts.successToast)
    } catch (err) {
      const fields = new Set(Object.keys(form.getValues() ?? {}))
      const fieldErrors = isApiError(err) ? (err.fieldErrors ?? {}) : {}
      const attached = Object.entries(fieldErrors).filter(([field]) => fields.has(field))
      for (const [field, message] of attached) {
        form.setError(field as Path<TValues>, { type: "server", message })
      }
      // A rejection whose fields the form does not have would otherwise be
      // silent, so anything unattached still surfaces as a form-level error.
      if (attached.length === Object.keys(fieldErrors).length && attached.length > 0) return

      const message = defaultErrorMessage(err)
      form.setError("root.serverError" as Path<TValues>, { type: "server", message })
      if (opts.errorToast !== false) showError(message)
    }
  })

  const errors = form.formState.errors as { root?: { serverError?: { message?: string } } }
  const serverError = errors.root?.serverError?.message

  return { ...form, submit, serverError }
}
