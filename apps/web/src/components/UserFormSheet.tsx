import { z } from "zod"
import { Controller } from "react-hook-form"

import { usersApi } from "@/api/endpoints/users"
import { FormField } from "@/components/common/FormField"
import { FormSection } from "@/components/common/FormSection"
import { SheetForm } from "@/components/common/SheetForm"
import { Input } from "@/components/ui/input"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import { useEntityFormSheet } from "@/hooks/useEntityFormSheet"
import type { User } from "@/types/entities"
import { Language } from "@/types/enums"

const LANGUAGE_OPTIONS = [
  { value: Language.EN, label: "English" },
  { value: Language.ES, label: "Spanish" },
  { value: Language.FR, label: "French" },
  { value: Language.DE, label: "German" },
  { value: Language.IT, label: "Italian" },
  { value: Language.PT, label: "Portuguese" },
  { value: Language.ZH, label: "Chinese" },
  { value: Language.JA, label: "Japanese" },
  { value: Language.KO, label: "Korean" },
] as const

const baseSchema = z.object({
  email: z.string().trim().min(1, "Email is required").email("Invalid email"),
  preferred_language: z.string().optional(),
  timezone: z.string().optional(),
})

const createSchema = baseSchema.extend({
  password: z
    .string()
    .optional()
    .refine((v) => !v || v.length >= 8, "Password must be at least 8 characters"),
})

const editSchema = baseSchema

type CreateValues = z.infer<typeof createSchema>
type EditValues = z.infer<typeof editSchema>

interface UserFormSheetProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  /** Pass a user to edit; omit/null to create a new one. */
  user?: User | null
  onSaved?: (user: User) => void
}

export function UserFormSheet(props: UserFormSheetProps) {
  if (props.user) {
    return <UserEditSheet {...props} user={props.user} />
  }
  return <UserCreateSheet {...props} />
}

function UserCreateSheet({ open, onOpenChange, onSaved }: UserFormSheetProps) {
  const { register, control, formState, submit, serverError } = useEntityFormSheet<
    CreateValues,
    Parameters<typeof usersApi.create>[0],
    User,
    User
  >({
    resource: "users",
    schema: createSchema,
    defaultValues: { email: "", password: "", preferred_language: "", timezone: "" },
    open,
    onOpenChange,
    parsePayload: (values) => ({
      email: values.email,
      password: values.password || undefined,
      preferred_language: values.preferred_language || undefined,
      timezone: values.timezone || undefined,
    }),
    save: ({ payload }) => usersApi.create(payload),
    successToast: { create: "User created" },
    onSaved,
  })

  const errors = formState.errors

  return (
    <SheetForm
      open={open}
      onOpenChange={onOpenChange}
      title="Add user"
      description="Create a new platform login. The user can complete profile details after first sign-in."
      size="md"
      onSubmit={submit}
      isSubmitting={formState.isSubmitting}
      serverError={serverError}
      submitLabel="Create user"
      submittingLabel="Creating…"
    >
      <FormSection title="Account">
        <FormField label="Email" required error={errors.email?.message} htmlFor="us-email">
          <Input
            id="us-email"
            type="email"
            placeholder="ada@minet.com"
            {...register("email")}
          />
        </FormField>
        <FormField
          label="Initial password"
          optional
          description="Leave blank to send a passwordless invite. Min 8 characters."
          error={errors.password?.message}
          htmlFor="us-password"
        >
          <Input id="us-password" type="password" {...register("password")} />
        </FormField>
      </FormSection>
      <FormSection
        title="Preferences"
        description="Optional. The user can change these later."
      >
        <FormField
          label="Preferred language"
          optional
          error={errors.preferred_language?.message}
          htmlFor="us-lang"
        >
          <Controller
            control={control}
            name="preferred_language"
            render={({ field }) => (
              <Select value={field.value ?? ""} onValueChange={field.onChange}>
                <SelectTrigger id="us-lang">
                  <SelectValue placeholder="Unset" />
                </SelectTrigger>
                <SelectContent>
                  {LANGUAGE_OPTIONS.map((l) => (
                    <SelectItem key={l.value} value={l.value}>
                      {l.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            )}
          />
        </FormField>
        <FormField
          label="Timezone"
          optional
          description="IANA tz, e.g. Africa/Kampala."
          error={errors.timezone?.message}
          htmlFor="us-tz"
        >
          <Input id="us-tz" placeholder="Africa/Kampala" {...register("timezone")} />
        </FormField>
      </FormSection>
    </SheetForm>
  )
}

function UserEditSheet({
  open,
  onOpenChange,
  user,
  onSaved,
}: UserFormSheetProps & { user: User }) {
  const { register, control, formState, submit, serverError } = useEntityFormSheet<
    EditValues,
    Parameters<typeof usersApi.updatePreferences>[1],
    User,
    User
  >({
    resource: "users",
    schema: editSchema,
    defaultValues: {
      email: user.email,
      preferred_language: user.preferred_language ?? "",
      timezone: user.timezone ?? "",
    },
    open,
    onOpenChange,
    entity: user,
    toFormValues: (u) => ({
      email: u.email,
      preferred_language: u.preferred_language ?? "",
      timezone: u.timezone ?? "",
    }),
    parsePayload: (values) => ({
      preferred_language: values.preferred_language || undefined,
      timezone: values.timezone || undefined,
    }),
    save: ({ payload, entity }) => usersApi.updatePreferences(entity!.id, payload),
    successToast: { update: "User updated" },
    onSaved,
  })

  const errors = formState.errors

  return (
    <SheetForm
      open={open}
      onOpenChange={onOpenChange}
      title="Edit user preferences"
      description="Update language and timezone. Email and password are managed elsewhere."
      size="md"
      onSubmit={submit}
      isSubmitting={formState.isSubmitting}
      serverError={serverError}
      submitLabel="Save changes"
      submittingLabel="Saving…"
    >
      <FormSection title="Account">
        <FormField label="Email" htmlFor="us-email-readonly">
          <Input
            id="us-email-readonly"
            type="email"
            value={user.email}
            disabled
            readOnly
          />
        </FormField>
        <input type="hidden" {...register("email")} />
      </FormSection>
      <FormSection title="Preferences">
        <FormField
          label="Preferred language"
          optional
          error={errors.preferred_language?.message}
          htmlFor="us-lang"
        >
          <Controller
            control={control}
            name="preferred_language"
            render={({ field }) => (
              <Select value={field.value ?? ""} onValueChange={field.onChange}>
                <SelectTrigger id="us-lang">
                  <SelectValue placeholder="Unset" />
                </SelectTrigger>
                <SelectContent>
                  {LANGUAGE_OPTIONS.map((l) => (
                    <SelectItem key={l.value} value={l.value}>
                      {l.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            )}
          />
        </FormField>
        <FormField
          label="Timezone"
          optional
          description="IANA tz, e.g. Africa/Kampala."
          error={errors.timezone?.message}
          htmlFor="us-tz"
        >
          <Input id="us-tz" placeholder="Africa/Kampala" {...register("timezone")} />
        </FormField>
      </FormSection>
    </SheetForm>
  )
}
