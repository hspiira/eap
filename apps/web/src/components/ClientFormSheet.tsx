import { useState } from "react"

import { useQuery } from "@tanstack/react-query"
import { Check, ChevronsUpDown } from "lucide-react"
import { Controller } from "react-hook-form"
import * as SelectPrimitive from "@radix-ui/react-select"
import { z } from "zod"

import { clientsApi } from "@/api/endpoints/clients"
import { industriesApi } from "@/api/endpoints/industries"
import type { ClientCreate, ClientUpdate } from "@/api/generated"
import { FormField } from "@/components/common/FormField"
import { FormSection } from "@/components/common/FormSection"
import { SheetForm } from "@/components/common/SheetForm"
import {
  Command,
  CommandEmpty,
  CommandGroup,
  CommandInput,
  CommandItem,
  CommandList,
} from "@/components/ui/command"
import { Input } from "@/components/ui/input"
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover"
import { Button } from "@/components/ui/button"
import {
  Select,
  SelectContent,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import { useEntityFormSheet } from "@/hooks/useEntityFormSheet"
import type { Client } from "@/types/entities"
import { ClientTier } from "@/types/enums"
import { cn } from "@/lib/utils"

const TIER_OPTIONS = [
  { value: ClientTier.A, label: "Tier A", desc: "Strategic — full service mix" },
  { value: ClientTier.B, label: "Tier B", desc: "Mid-tier — consultancy extension" },
  { value: ClientTier.C, label: "Tier C", desc: "Long-tail — lower-touch model" },
] as const

const TIER_VALUES = TIER_OPTIONS.map((o) => o.value) as [ClientTier, ...ClientTier[]]

const clientSchema = z
  .object({
    name: z.string().trim().min(1, "Name is required"),
    code: z
      .string()
      .trim()
      .min(3, "Code must be 3–5 characters")
      .max(5, "Code must be 3–5 characters"),
    tier: z.enum(["", ...TIER_VALUES] as readonly [string, ...string[]]).optional(),
    email: z
      .string()
      .trim()
      .optional()
      .refine((v) => !v || /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(v), "Invalid email"),
    phone: z.string().optional(),
    address: z.string().optional(),
    billing_street: z.string().optional(),
    billing_city: z.string().optional(),
    billing_postal: z.string().optional(),
    billing_country: z.string().optional(),
    industry_id: z.string().optional(),
  })
  .superRefine((d, ctx) => {
    const anyBilling =
      d.billing_street || d.billing_city || d.billing_postal || d.billing_country
    if (!anyBilling) return
    for (const f of ["billing_street", "billing_city", "billing_country"] as const) {
      if (!d[f]?.trim()) {
        ctx.addIssue({
          code: "custom",
          path: [f],
          message: "Required when any billing field is set",
        })
      }
    }
  })

type ClientFormValues = z.infer<typeof clientSchema>

const EMPTY: ClientFormValues = {
  name: "",
  code: "",
  tier: "",
  email: "",
  phone: "",
  address: "",
  billing_street: "",
  billing_city: "",
  billing_postal: "",
  billing_country: "",
  industry_id: "",
}

interface ClientFormSheetProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  client?: Client | null
  onSaved?: (client: Client) => void
}

export function ClientFormSheet({
  open,
  onOpenChange,
  client,
  onSaved,
}: ClientFormSheetProps) {
  const [industryOpen, setIndustryOpen] = useState(false)

  const { data: industriesPage } = useQuery({
    queryKey: ["industries", "picker"],
    queryFn: () => industriesApi.list({ limit: 200 }),
    enabled: open,
    staleTime: 5 * 60 * 1000,
  })
  const industryOptions = industriesPage?.items ?? []

  const { register, control, formState, submit, serverError, isEdit } = useEntityFormSheet<
    ClientFormValues,
    ClientCreate & { __tier?: ClientTier | null },
    Client,
    Client
  >({
    resource: "clients",
    schema: clientSchema,
    defaultValues: EMPTY,
    open,
    onOpenChange,
    entity: client,
    toFormValues: (c) => ({
      name: c.name,
      code: c.code,
      tier: c.tier ?? "",
      email: c.contact_info?.email ?? "",
      phone: c.contact_info?.phone ?? "",
      address: c.contact_info?.address ?? "",
      billing_street: c.billing_address?.street ?? "",
      billing_city: c.billing_address?.city ?? "",
      billing_postal: c.billing_address?.postal_code ?? "",
      billing_country: c.billing_address?.country ?? "",
      industry_id: c.industry_id ?? "",
    }),
    parsePayload: (values) => ({
      name: values.name,
      code: values.code,
      contact_info: {
        email: values.email || null,
        phone: values.phone || null,
        address: values.address || null,
      },
      billing_address:
        values.billing_street && values.billing_city && values.billing_country
          ? {
              street: values.billing_street,
              city: values.billing_city,
              country: values.billing_country,
              postal_code: values.billing_postal || null,
            }
          : null,
      industry_id: values.industry_id || null,
      __tier: values.tier ? (values.tier as ClientTier) : null,
    }),
    save: async ({ payload, entity, isEdit }) => {
      const { __tier, ...createPayload } = payload
      let saved: Client
      if (isEdit && entity) {
        const update: ClientUpdate = { name: createPayload.name }
        saved = await clientsApi.update(entity.id, update)
        if (__tier !== (entity.tier ?? null)) {
          saved = await clientsApi.setTier(entity.id, __tier ?? null)
        }
      } else {
        saved = await clientsApi.create(createPayload)
        if (__tier) {
          saved = await clientsApi.setTier(saved.id, __tier)
        }
      }
      return saved
    },
    successToast: { create: "Client created", update: "Client updated" },
    onSaved,
  })

  const errors = formState.errors

  return (
    <SheetForm
      open={open}
      onOpenChange={onOpenChange}
      title={isEdit ? "Edit client" : "Add client"}
      description={
        isEdit
          ? "Update identity, tiering, and contact details."
          : "Create a new corporate client. You can link contracts, services, and staff after saving."
      }
      size="md"
      onSubmit={submit}
      isSubmitting={formState.isSubmitting}
      serverError={serverError}
      submitLabel={isEdit ? "Save changes" : "Create client"}
      submittingLabel={isEdit ? "Saving…" : "Creating…"}
    >
      <FormSection title="Identity">
        <FormField
          label="Name"
          required
          error={errors.name?.message}
          htmlFor="cs-name"
        >
          <Input id="cs-name" placeholder="e.g. Acme Corp" {...register("name")} />
        </FormField>
        <FormField
          label="Code"
          description="3–5 character code used in employee references."
          required
          error={errors.code?.message}
          htmlFor="cs-code"
        >
          <Input
            id="cs-code"
            placeholder="ACME"
            maxLength={5}
            className="font-mono"
            {...register("code")}
          />
        </FormField>
      </FormSection>

      <FormSection title="Tiering & sector">
        <FormField label="Tier" optional error={errors.tier?.message} htmlFor="cs-tier">
          <Controller
            control={control}
            name="tier"
            render={({ field }) => (
              <Select value={field.value ?? ""} onValueChange={field.onChange}>
                <SelectTrigger id="cs-tier">
                  <SelectValue placeholder="Unassigned" />
                </SelectTrigger>
                <SelectContent>
                  {TIER_OPTIONS.map(({ value, label, desc }) => (
                    <SelectPrimitive.Item
                      key={value}
                      value={value}
                      className="relative flex w-full cursor-default select-none rounded-sm py-2 pl-2 pr-8 text-sm outline-none focus:bg-accent focus:text-accent-foreground data-disabled:pointer-events-none data-disabled:opacity-50"
                    >
                      <span className="absolute right-2 flex h-3.5 w-3.5 items-center justify-center mt-0.5">
                        <SelectPrimitive.ItemIndicator>
                          <Check className="h-4 w-4" />
                        </SelectPrimitive.ItemIndicator>
                      </span>
                      <div className="flex flex-col">
                        <SelectPrimitive.ItemText>{label}</SelectPrimitive.ItemText>
                        <span className="text-xs text-muted-foreground leading-tight mt-0.5">{desc}</span>
                      </div>
                    </SelectPrimitive.Item>
                  ))}
                </SelectContent>
              </Select>
            )}
          />
        </FormField>

        <FormField
          label="Industry"
          optional
          description={
            isEdit
              ? "Industry is set at creation only — contact platform admin to change."
              : "The sector this client operates in. Drives benchmarking and reporting."
          }
          error={errors.industry_id?.message}
          htmlFor="cs-industry"
        >
          <Controller
            control={control}
            name="industry_id"
            render={({ field }) => (
              <Popover open={industryOpen} onOpenChange={setIndustryOpen}>
                <PopoverTrigger asChild>
                  <Button
                    id="cs-industry"
                    type="button"
                    variant="outline"
                    role="combobox"
                    aria-expanded={industryOpen}
                    disabled={isEdit}
                    className={cn(
                      "w-full h-9 justify-between px-3 font-normal text-sm shadow-sm",
                      !field.value && "text-muted-foreground",
                    )}
                  >
                    <span className="truncate">
                      {field.value
                        ? (industryOptions.find((i) => i.id === field.value)?.name ?? "No industry")
                        : "No industry"}
                    </span>
                    <ChevronsUpDown className="ml-2 h-4 w-4 shrink-0 opacity-50" />
                  </Button>
                </PopoverTrigger>
                <PopoverContent
                  className="p-0"
                  align="start"
                  style={{ width: "var(--radix-popover-trigger-width)" }}
                >
                  <Command>
                    <CommandInput placeholder="Search industries…" />
                    <CommandList>
                      <CommandEmpty>No industries found.</CommandEmpty>
                      <CommandGroup>
                        <CommandItem
                          value="__none"
                          onSelect={() => {
                            field.onChange("")
                            setIndustryOpen(false)
                          }}
                        >
                          <Check
                            className={cn(
                              "mr-2 h-4 w-4",
                              !field.value ? "opacity-100" : "opacity-0",
                            )}
                          />
                          No industry
                        </CommandItem>
                        {industryOptions.map((ind) => (
                          <CommandItem
                            key={ind.id}
                            value={ind.name}
                            onSelect={() => {
                              field.onChange(ind.id)
                              setIndustryOpen(false)
                            }}
                          >
                            <Check
                              className={cn(
                                "mr-2 h-4 w-4",
                                field.value === ind.id ? "opacity-100" : "opacity-0",
                              )}
                            />
                            {ind.name}
                          </CommandItem>
                        ))}
                      </CommandGroup>
                    </CommandList>
                  </Command>
                </PopoverContent>
              </Popover>
            )}
          />
        </FormField>
      </FormSection>

      <FormSection
        title="Primary contact"
        description="Used for billing and account notifications."
      >
        <FormField
          label="Email"
          optional
          error={errors.email?.message}
          htmlFor="cs-email"
        >
          <Input id="cs-email" type="email" placeholder="contact@acme.com" {...register("email")} />
        </FormField>
        <FormField
          label="Phone"
          optional
          error={errors.phone?.message}
          htmlFor="cs-phone"
        >
          <Input id="cs-phone" type="tel" placeholder="+256 …" {...register("phone")} />
        </FormField>
        <FormField
          label="Address"
          optional
          error={errors.address?.message}
          htmlFor="cs-address"
        >
          <Input id="cs-address" placeholder="Street, city" {...register("address")} />
        </FormField>
      </FormSection>

      <FormSection
        title="Billing address"
        description="Where invoices are sent. Leave blank if same as contact address."
      >
        <FormField
          label="Street"
          optional
          error={errors.billing_street?.message}
          htmlFor="cs-billing-street"
        >
          <Input id="cs-billing-street" {...register("billing_street")} />
        </FormField>
        <div className="grid grid-cols-2 gap-3">
          <FormField
            label="City"
            optional
            error={errors.billing_city?.message}
            htmlFor="cs-billing-city"
          >
            <Input id="cs-billing-city" {...register("billing_city")} />
          </FormField>
          <FormField
            label="Postal code"
            optional
            error={errors.billing_postal?.message}
            htmlFor="cs-billing-postal"
          >
            <Input id="cs-billing-postal" {...register("billing_postal")} />
          </FormField>
        </div>
        <FormField
          label="Country"
          optional
          error={errors.billing_country?.message}
          htmlFor="cs-billing-country"
        >
          <Input id="cs-billing-country" placeholder="Uganda" {...register("billing_country")} />
        </FormField>
      </FormSection>
    </SheetForm>
  )
}
