import { z } from 'zod'

import { type TenantCreate, tenantsApi } from '@/api/endpoints/tenants'
import { FormField } from '@/components/common/FormField'
import { SheetForm } from '@/components/common/SheetForm'
import { Checkbox } from '@/components/ui/checkbox'
import { Input } from '@/components/ui/input'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import { useEntityFormSheet } from '@/hooks/useEntityFormSheet'
import type { Tenant } from '@/types/entities'

const SUBSCRIPTION_TIERS = ['Free', 'Basic', 'Professional', 'Enterprise'] as const

const tenantSchema = z.object({
  name: z.string().trim().min(1, 'Name is required').max(255),
  code: z
    .string()
    .trim()
    .min(3, 'Code must be at least 3 characters')
    .max(15, 'Code must be at most 15 characters')
    .regex(
      /^[a-z0-9-]+$/,
      'Lowercase letters, digits, and hyphens only',
    ),
  admin_email: z
    .union([z.string().trim().email('Enter a valid email address').max(255), z.literal('')])
    .optional(),
  azure_tenant_id: z
    .string()
    .trim()
    .max(64, 'Max 64 characters')
    .optional(),
  azure_sso_enabled: z.boolean(),
  subscription_tier: z.enum(SUBSCRIPTION_TIERS),
  max_users: z
    .string()
    .trim()
    .refine((v) => /^\d+$/.test(v) && Number.parseInt(v, 10) >= 1, 'Must be ≥ 1'),
  max_clients: z
    .string()
    .trim()
    .refine((v) => /^\d+$/.test(v) && Number.parseInt(v, 10) >= 1, 'Must be ≥ 1'),
  custom_branding: z.boolean(),
})

type TenantFormValues = z.infer<typeof tenantSchema>

const DEFAULTS: TenantFormValues = {
  name: '',
  code: '',
  admin_email: '',
  azure_tenant_id: '',
  azure_sso_enabled: false,
  subscription_tier: 'Free',
  max_users: '10',
  max_clients: '5',
  custom_branding: false,
}

interface TenantFormSheetProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  tenant?: Tenant | null
  onSaved?: (tenant: Tenant) => void
}

export function TenantFormSheet({
  open,
  onOpenChange,
  tenant,
  onSaved,
}: TenantFormSheetProps) {
  const { register, setValue, watch, formState, submit, serverError, isEdit } =
    useEntityFormSheet<TenantFormValues, TenantCreate, Tenant, Tenant>({
      resource: 'tenants',
      schema: tenantSchema,
      defaultValues: DEFAULTS,
      open,
      onOpenChange,
      entity: tenant,
      toFormValues: (t) => ({
        name: t.name,
        code: t.code ?? '',
        admin_email: '',
        azure_tenant_id: '',
        azure_sso_enabled: false,
        subscription_tier: ((t.subscription_tier as TenantFormValues['subscription_tier']) ?? 'Free'),
        max_users: String(t.settings?.max_users ?? 10),
        max_clients: String(t.settings?.max_clients ?? 5),
        custom_branding: t.settings?.custom_branding ?? false,
      }),
      parsePayload: (v) => {
        const azureId = v.azure_tenant_id?.trim() || null
        return {
          name: v.name.trim(),
          code: v.code.trim().toLowerCase(),
          admin_email: v.admin_email?.trim() || null,
          azure_tenant_id: azureId,
          azure_sso_enabled: azureId ? v.azure_sso_enabled : false,
          subscription_tier: v.subscription_tier,
          settings: {
            max_users: Number.parseInt(v.max_users, 10),
            max_clients: Number.parseInt(v.max_clients, 10),
            features_enabled: [],
            custom_branding: v.custom_branding,
          },
        }
      },
      save: ({ payload, entity, isEdit }) =>
        isEdit && entity
          ? tenantsApi.update(entity.id, { name: payload.name })
          : tenantsApi.create(payload),
      successToast: { create: 'Tenant created', update: 'Tenant updated' },
      onSaved,
    })

  const errors = formState.errors
  const currentTier = watch('subscription_tier')
  const currentBranding = watch('custom_branding')
  const currentAzureId = watch('azure_tenant_id')
  const currentAzureSso = watch('azure_sso_enabled')

  return (
    <SheetForm
      open={open}
      onOpenChange={onOpenChange}
      title={isEdit ? 'Edit tenant' : 'New tenant'}
      description={
        isEdit
          ? 'Edit basic tenant info. Use the detail page for lifecycle and SSO config.'
          : 'Create a tenant and its first admin user. Optionally configure Azure SSO now.'
      }
      onSubmit={submit}
      isSubmitting={formState.isSubmitting}
      submitLabel={isEdit ? 'Save changes' : 'Create tenant'}
      serverError={serverError}
    >
      <FormField
        label="Name"
        required
        error={errors.name?.message}
        htmlFor="tenant-name"
      >
        <Input
          id="tenant-name"
          placeholder="Minet Uganda"
          autoComplete="off"
          {...register('name')}
        />
      </FormField>

      <FormField
        label="Code"
        required
        description="Short identifier (3–15 chars, lowercase). Used in sign-in URLs. Cannot be changed."
        error={errors.code?.message}
        htmlFor="tenant-code"
      >
        <Input
          id="tenant-code"
          placeholder="minet"
          autoComplete="off"
          className="font-mono"
          disabled={isEdit}
          {...register('code', {
            setValueAs: (v) => (typeof v === 'string' ? v.toLowerCase() : v),
          })}
        />
      </FormField>

      {!isEdit ? (
        <>
          <FormField
            label="Admin email"
            description="The tenant's first admin user. Leave blank to use a placeholder (admin_{code}@evexia.test)."
            error={errors.admin_email?.message}
            htmlFor="tenant-admin-email"
          >
            <Input
              id="tenant-admin-email"
              type="email"
              placeholder="admin@company.com"
              autoComplete="off"
              {...register('admin_email')}
            />
          </FormField>

          <FormField
            label="Azure tenant ID"
            description="Azure AD directory (tenant) ID from Azure Portal → Azure Active Directory → Properties. Leave blank to configure SSO later."
            error={errors.azure_tenant_id?.message}
            htmlFor="tenant-azure-id"
          >
            <Input
              id="tenant-azure-id"
              placeholder="xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"
              autoComplete="off"
              className="font-mono"
              {...register('azure_tenant_id')}
            />
          </FormField>

          {currentAzureId?.trim() ? (
            <FormField
              label="Enable Azure SSO"
              description="Allow users in this Azure directory to sign in immediately."
              error={errors.azure_sso_enabled?.message}
              htmlFor="tenant-azure-sso"
            >
              <div className="flex items-center gap-2">
                <Checkbox
                  id="tenant-azure-sso"
                  checked={currentAzureSso}
                  onCheckedChange={(v) =>
                    setValue('azure_sso_enabled', v === true, { shouldDirty: true })
                  }
                />
                <span className="text-sm text-fg-muted">Enable on creation</span>
              </div>
            </FormField>
          ) : null}
        </>
      ) : null}

      <FormField
        label="Subscription tier"
        required
        error={errors.subscription_tier?.message}
        htmlFor="tenant-tier"
      >
        <Select
          value={currentTier}
          onValueChange={(v) =>
            setValue('subscription_tier', v as TenantFormValues['subscription_tier'], {
              shouldDirty: true,
              shouldValidate: true,
            })
          }
          disabled={isEdit}
        >
          <SelectTrigger id="tenant-tier">
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            {SUBSCRIPTION_TIERS.map((t) => (
              <SelectItem key={t} value={t}>
                {t}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </FormField>

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
        <FormField
          label="Max users"
          required
          error={errors.max_users?.message}
          htmlFor="tenant-max-users"
        >
          <Input
            id="tenant-max-users"
            type="number"
            min={1}
            disabled={isEdit}
            {...register('max_users')}
          />
        </FormField>

        <FormField
          label="Max clients"
          required
          error={errors.max_clients?.message}
          htmlFor="tenant-max-clients"
        >
          <Input
            id="tenant-max-clients"
            type="number"
            min={1}
            disabled={isEdit}
            {...register('max_clients')}
          />
        </FormField>
      </div>

      <FormField
        label="Custom branding"
        optional
        description="Allow the tenant to upload their own logo and override theme colours."
        error={errors.custom_branding?.message}
        htmlFor="tenant-branding"
      >
        <div className="flex items-center gap-2">
          <Checkbox
            id="tenant-branding"
            checked={currentBranding}
            disabled={isEdit}
            onCheckedChange={(v) =>
              setValue('custom_branding', v === true, { shouldDirty: true })
            }
          />
          <span className="text-sm text-fg-muted">Enable per-tenant branding</span>
        </div>
      </FormField>
    </SheetForm>
  )
}
