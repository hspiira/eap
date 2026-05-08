import { createFileRoute, useNavigate } from "@tanstack/react-router"
import { z } from "zod"

import { contractsApi } from "@/api/endpoints/contracts"
import { FormField } from "@/components/common/FormField"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { useApiForm } from "@/hooks/useApiForm"

export const Route = createFileRoute("/contracts/new")({
  component: ContractCreatePage,
})

const contractCreateSchema = z
  .object({
    client_id: z.string().trim().min(1, "Client ID is required"),
    contract_number: z.string().optional(),
    start_date: z.string().min(1, "Start date is required"),
    end_date: z.string().optional(),
  })
  .refine(
    (d) => !d.end_date || d.end_date >= d.start_date,
    { path: ["end_date"], message: "End date must be on or after start date" },
  )

function ContractCreatePage() {
  const navigate = useNavigate()

  const { register, formState, submit, serverError } = useApiForm<z.infer<typeof contractCreateSchema>>({
    schema: contractCreateSchema,
    defaultValues: { client_id: "", contract_number: "", start_date: "", end_date: "" },
    successToast: "Contract created",
    onSubmit: async (values) => {
      await contractsApi.create({
        client_id: values.client_id,
        contract_number: values.contract_number || undefined,
        start_date: values.start_date,
        end_date: values.end_date || undefined,
      })
      navigate({ to: "/contracts" })
    },
  })

  return (
    <div className="p-6 max-w-md">
      <h1 className="text-xl font-semibold text-ink">Add contract</h1>
      <form onSubmit={submit} className="mt-6 space-y-4" noValidate>
        {serverError && <p className="text-sm text-ink" role="alert">{serverError}</p>}
        <FormField
          label="Client ID"
          required
          error={formState.errors.client_id?.message as string | undefined}
          htmlFor="client_id"
        >
          <Input id="client_id" className="rounded-none" {...register("client_id")} />
        </FormField>
        <FormField
          label="Contract number"
          error={formState.errors.contract_number?.message as string | undefined}
          htmlFor="contract_number"
        >
          <Input id="contract_number" className="rounded-none" {...register("contract_number")} />
        </FormField>
        <FormField
          label="Start date"
          required
          error={formState.errors.start_date?.message as string | undefined}
          htmlFor="start_date"
        >
          <Input id="start_date" type="date" className="rounded-none" {...register("start_date")} />
        </FormField>
        <FormField
          label="End date"
          error={formState.errors.end_date?.message as string | undefined}
          htmlFor="end_date"
        >
          <Input id="end_date" type="date" className="rounded-none" {...register("end_date")} />
        </FormField>
        <div className="flex gap-2">
          <Button type="submit" disabled={formState.isSubmitting} className="rounded-none">
            {formState.isSubmitting ? "Creating…" : "Create contract"}
          </Button>
          <Button type="button" variant="secondary" className="rounded-none" onClick={() => navigate({ to: "/contracts" })}>
            Cancel
          </Button>
        </div>
      </form>
    </div>
  )
}
