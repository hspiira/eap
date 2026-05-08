import { createFileRoute, useNavigate } from "@tanstack/react-router"
import { z } from "zod"

import { personsApi } from "@/api/endpoints/persons"
import { FormField } from "@/components/common/FormField"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { useApiForm } from "@/hooks/useApiForm"
import { PersonType } from "@/types/enums"

export const Route = createFileRoute("/persons/new")({
  component: PersonCreatePage,
})

const personCreateSchema = z.object({
  first_name: z.string().trim().min(1, "First name is required"),
  last_name: z.string().trim().min(1, "Last name is required"),
  person_type: z.enum([
    PersonType.CLIENT_EMPLOYEE,
    PersonType.DEPENDENT,
    PersonType.SERVICE_PROVIDER,
    PersonType.PLATFORM_STAFF,
  ]),
  client_id: z.string().optional(),
})

function PersonCreatePage() {
  const navigate = useNavigate()

  const { register, formState, submit, serverError } = useApiForm<z.infer<typeof personCreateSchema>>({
    schema: personCreateSchema,
    defaultValues: {
      first_name: "",
      last_name: "",
      person_type: PersonType.CLIENT_EMPLOYEE,
      client_id: "",
    },
    successToast: "Person created",
    onSubmit: async (values) => {
      await personsApi.create({
        first_name: values.first_name,
        last_name: values.last_name,
        person_type: values.person_type,
        client_id: values.client_id || undefined,
      })
      navigate({ to: "/persons" })
    },
  })

  return (
    <div className="p-6 max-w-md">
      <h1 className="text-xl font-semibold text-fg">Add person</h1>
      <form onSubmit={submit} className="mt-6 space-y-4" noValidate>
        {serverError && <p className="text-sm text-fg" role="alert">{serverError}</p>}
        <FormField
          label="First name"
          required
          error={formState.errors.first_name?.message as string | undefined}
          htmlFor="first_name"
        >
          <Input id="first_name" className="rounded-none" {...register("first_name")} />
        </FormField>
        <FormField
          label="Last name"
          required
          error={formState.errors.last_name?.message as string | undefined}
          htmlFor="last_name"
        >
          <Input id="last_name" className="rounded-none" {...register("last_name")} />
        </FormField>
        <FormField
          label="Type"
          required
          error={formState.errors.person_type?.message as string | undefined}
          htmlFor="person_type"
        >
          <select
            id="person_type"
            className="flex h-9 w-full border border-fg/30 bg-surface px-3 py-2 rounded-none"
            {...register("person_type")}
          >
            <option value={PersonType.CLIENT_EMPLOYEE}>Client Employee</option>
            <option value={PersonType.DEPENDENT}>Dependent</option>
            <option value={PersonType.SERVICE_PROVIDER}>Service Provider</option>
            <option value={PersonType.PLATFORM_STAFF}>Platform Staff</option>
          </select>
        </FormField>
        <FormField
          label="Client ID (optional)"
          error={formState.errors.client_id?.message as string | undefined}
          htmlFor="client_id"
        >
          <Input id="client_id" className="rounded-none" {...register("client_id")} />
        </FormField>
        <div className="flex gap-2">
          <Button type="submit" disabled={formState.isSubmitting} className="rounded-none">
            {formState.isSubmitting ? "Creating…" : "Create person"}
          </Button>
          <Button type="button" variant="secondary" className="rounded-none" onClick={() => navigate({ to: "/persons" })}>
            Cancel
          </Button>
        </div>
      </form>
    </div>
  )
}
