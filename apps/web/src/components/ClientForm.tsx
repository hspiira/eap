import { z } from "zod"

import { clientsApi } from "@/api/endpoints/clients"
import { FormField } from "@/components/common/FormField"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { useApiForm } from "@/hooks/useApiForm"

export interface ClientFormProps {
  onSuccess?: () => void
  onCancel?: () => void
  submitLabel?: string
}

const clientCreateSchema = z.object({
  name: z.string().trim().min(1, "Name is required"),
  code: z
    .string()
    .trim()
    .min(3, "Code must be 3–5 characters")
    .max(5, "Code must be 3–5 characters"),
  email: z
    .string()
    .trim()
    .optional()
    .refine((v) => !v || /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(v), "Invalid email"),
  phone: z.string().optional(),
})

export function ClientForm({
  onSuccess,
  onCancel,
  submitLabel = "Create client",
}: ClientFormProps) {
  const { register, formState, submit, serverError } = useApiForm<z.infer<typeof clientCreateSchema>>({
    schema: clientCreateSchema,
    defaultValues: { name: "", code: "", email: "", phone: "" },
    successToast: "Client created",
    onSubmit: async (values) => {
      await clientsApi.create({
        name: values.name,
        code: values.code,
        contact_info: {
          email: values.email || undefined,
          phone: values.phone || undefined,
        },
      })
      onSuccess?.()
    },
  })

  const contactEmailError =
    (formState.errors as Record<string, { message?: string }>)["contact_info.email"]?.message ??
    formState.errors.email?.message
  const contactPhoneError =
    (formState.errors as Record<string, { message?: string }>)["contact_info.phone"]?.message ??
    formState.errors.phone?.message

  return (
    <form onSubmit={submit} className="space-y-4" noValidate>
      {serverError && (
        <p
          className="text-sm text-[#5A626A] border border-[#5A626A]/30 bg-[#f5f5f5] px-3 py-2 rounded-none"
          role="alert"
        >
          {serverError}
        </p>
      )}
      <FormField
        label="Name"
        required
        error={formState.errors.name?.message as string | undefined}
        htmlFor="client-name"
      >
        <Input id="client-name" className="rounded-none border-[#5A626A]/30" {...register("name")} />
      </FormField>
      <FormField
        label="Code (3–5 chars)"
        required
        error={formState.errors.code?.message as string | undefined}
        htmlFor="client-code"
      >
        <Input id="client-code" className="rounded-none border-[#5A626A]/30" {...register("code")} />
      </FormField>
      <FormField label="Email" error={contactEmailError as string | undefined} htmlFor="client-email">
        <Input
          id="client-email"
          type="email"
          className="rounded-none border-[#5A626A]/30"
          {...register("email")}
        />
      </FormField>
      <FormField label="Phone" error={contactPhoneError as string | undefined} htmlFor="client-phone">
        <Input id="client-phone" className="rounded-none border-[#5A626A]/30" {...register("phone")} />
      </FormField>
      <div className="flex gap-2 pt-2">
        <Button
          type="submit"
          disabled={formState.isSubmitting}
          className="rounded-none bg-natural text-white hover:bg-natural-dark"
        >
          {formState.isSubmitting ? "Creating…" : submitLabel}
        </Button>
        {onCancel && (
          <Button
            type="button"
            variant="secondary"
            className="rounded-none border-[#5A626A]/30 text-[#5A626A]"
            onClick={onCancel}
          >
            Cancel
          </Button>
        )}
      </div>
    </form>
  )
}
