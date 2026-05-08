import { createFileRoute, useNavigate } from "@tanstack/react-router"
import { z } from "zod"

import { usersApi } from "@/api/endpoints/users"
import { FormField } from "@/components/common/FormField"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { useApiForm } from "@/hooks/useApiForm"

export const Route = createFileRoute("/users/new")({
  component: UserCreatePage,
})

const userCreateSchema = z.object({
  email: z.string().trim().min(1, "Email is required").email("Invalid email"),
  password: z.string().optional(),
})

function UserCreatePage() {
  const navigate = useNavigate()

  const { register, formState, submit, serverError } = useApiForm<z.infer<typeof userCreateSchema>>({
    schema: userCreateSchema,
    defaultValues: { email: "", password: "" },
    successToast: "User created",
    onSubmit: async (values) => {
      await usersApi.create({ email: values.email, password: values.password || undefined })
      navigate({ to: "/users" })
    },
  })

  return (
    <div className="p-6 max-w-md">
      <h1 className="text-xl font-semibold text-fg">Add user</h1>
      <form onSubmit={submit} className="mt-6 space-y-4" noValidate>
        {serverError && (
          <p className="text-sm text-fg" role="alert">
            {serverError}
          </p>
        )}
        <FormField
          label="Email"
          required
          error={formState.errors.email?.message as string | undefined}
          htmlFor="email"
        >
          <Input id="email" type="email" className="rounded-none" {...register("email")} />
        </FormField>
        <FormField
          label="Password (optional)"
          error={formState.errors.password?.message as string | undefined}
          htmlFor="password"
        >
          <Input id="password" type="password" className="rounded-none" {...register("password")} />
        </FormField>
        <div className="flex gap-2">
          <Button type="submit" disabled={formState.isSubmitting} className="rounded-none">
            {formState.isSubmitting ? "Creating…" : "Create user"}
          </Button>
          <Button
            type="button"
            variant="secondary"
            className="rounded-none"
            onClick={() => navigate({ to: "/users" })}
          >
            Cancel
          </Button>
        </div>
      </form>
    </div>
  )
}
