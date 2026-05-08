import { createFileRoute, useNavigate } from "@tanstack/react-router"
import { z } from "zod"

import { serviceAssignmentsApi } from "@/api/endpoints/service-assignments"
import { FormField } from "@/components/common/FormField"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { useApiForm } from "@/hooks/useApiForm"

export const Route = createFileRoute("/service-assignments/new")({
  component: ServiceAssignmentCreatePage,
})

const serviceAssignmentCreateSchema = z.object({
  contract_id: z.string().trim().min(1, "Contract ID is required"),
  service_id: z.string().trim().min(1, "Service ID is required"),
})

function ServiceAssignmentCreatePage() {
  const navigate = useNavigate()

  const { register, formState, submit, serverError } = useApiForm<z.infer<typeof serviceAssignmentCreateSchema>>({
    schema: serviceAssignmentCreateSchema,
    defaultValues: { contract_id: "", service_id: "" },
    successToast: "Service assignment created",
    onSubmit: async (values) => {
      await serviceAssignmentsApi.create({ contract_id: values.contract_id, service_id: values.service_id })
      navigate({ to: "/service-assignments" })
    },
  })

  return (
    <div className="p-6 max-w-md">
      <h1 className="text-xl font-semibold text-fg">Add service assignment</h1>
      <form onSubmit={submit} className="mt-6 space-y-4" noValidate>
        {serverError && <p className="text-sm text-fg" role="alert">{serverError}</p>}
        <FormField
          label="Contract ID"
          required
          error={formState.errors.contract_id?.message as string | undefined}
          htmlFor="contract_id"
        >
          <Input id="contract_id" className="rounded-none" {...register("contract_id")} />
        </FormField>
        <FormField
          label="Service ID"
          required
          error={formState.errors.service_id?.message as string | undefined}
          htmlFor="service_id"
        >
          <Input id="service_id" className="rounded-none" {...register("service_id")} />
        </FormField>
        <div className="flex gap-2">
          <Button type="submit" disabled={formState.isSubmitting} className="rounded-none">
            {formState.isSubmitting ? "Creating…" : "Create"}
          </Button>
          <Button type="button" variant="secondary" className="rounded-none" onClick={() => navigate({ to: "/service-assignments" })}>
            Cancel
          </Button>
        </div>
      </form>
    </div>
  )
}
