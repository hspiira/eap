import { createFileRoute, useNavigate } from "@tanstack/react-router"
import { z } from "zod"

import { servicesApi } from "@/api/endpoints/services"
import { FormField } from "@/components/common/FormField"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { useApiForm } from "@/hooks/useApiForm"

export const Route = createFileRoute("/services/new")({
  component: ServiceCreatePage,
})

const serviceCreateSchema = z.object({
  name: z.string().trim().min(1, "Name is required"),
  description: z.string().optional(),
})

function ServiceCreatePage() {
  const navigate = useNavigate()

  const { register, formState, submit, serverError } = useApiForm<z.infer<typeof serviceCreateSchema>>({
    schema: serviceCreateSchema,
    defaultValues: { name: "", description: "" },
    successToast: "Service created",
    onSubmit: async (values) => {
      await servicesApi.create({ name: values.name, description: values.description || undefined })
      navigate({ to: "/services" })
    },
  })

  return (
    <div className="p-6 max-w-md">
      <h1 className="text-xl font-semibold text-fg">Add service</h1>
      <form onSubmit={submit} className="mt-6 space-y-4" noValidate>
        {serverError && <p className="text-sm text-fg" role="alert">{serverError}</p>}
        <FormField
          label="Name"
          required
          error={formState.errors.name?.message as string | undefined}
          htmlFor="name"
        >
          <Input id="name" className="rounded-none" {...register("name")} />
        </FormField>
        <FormField
          label="Description"
          error={formState.errors.description?.message as string | undefined}
          htmlFor="description"
        >
          <Input id="description" className="rounded-none" {...register("description")} />
        </FormField>
        <div className="flex gap-2">
          <Button type="submit" disabled={formState.isSubmitting} className="rounded-none">
            {formState.isSubmitting ? "Creating…" : "Create service"}
          </Button>
          <Button type="button" variant="secondary" className="rounded-none" onClick={() => navigate({ to: "/services" })}>
            Cancel
          </Button>
        </div>
      </form>
    </div>
  )
}
